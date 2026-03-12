from helper import (
    B, AIR, STONE, MOSSY, ANDESITE, SAFE_OVERWRITE,
    blk, STATE, facing_vectors, front_origin, rot, clamp_entrance_offset
)
from world import editor, TERR, cub, SEA_LEVEL


def _style():
    return STATE.STYLE

def _facing():
    return STATE.FACING

def _gs_front(wx, wz, w, d):
    return STATE.gs_front_origin(wx, wz, w, d)

def flatten_terrain(x: int, y: int, z: int, w: int, d: int, pad: int = 2):
    height = STATE.HEIGHT
    clear_top = y + height + 12
    for dx in range(-pad, w + pad):
        for dz in range(-pad, d + pad):
            wx, wz = x + dx, z + dz
            sy = TERR.surface_y(wx, wz)
            if sy is None:
                continue
            if sy > y - 2:
                cub((wx, y - 2, wz), (wx, sy + 2, wz), AIR)
            elif sy < y - 2:
                cub((wx, sy, wz), (wx, y - 2, wz), STONE)
            cub((wx, y, wz), (wx, clear_top, wz), AIR)
            editor.placeBlock((wx, y - 1, wz), B['smooth_stone'])


def add_under_house_support(wx: int, floor_y: int, wz: int, w: int, d: int, pad: int = 1):
    top_fill_y = floor_y - 1
    for dx in range(-pad, w + pad):
        for dz in range(-pad, d + pad):
            x, z = wx + dx, wz + dz
            base_y = TERR.support_base_y(x, z)
            if base_y < top_fill_y:
                cub((x, base_y, z), (x, top_fill_y, z), STONE)


def build_stone_foundation(x: int, y: int, z: int, w: int, d: int):
    floor_block = _style()['palette']['wall']
    for dx in range(w):
        for dz in range(d):
            wx, wz = x + dx, z + dz
            base_y = TERR.support_base_y(wx, wz)
            if base_y < y - 2:
                cub((wx, base_y, wz), (wx, y - 2, wz), STONE)
            editor.placeBlock((wx, y - 1, wz), floor_block)

def build_timber_frame(x: int, y: int, z: int, w: int, d: int, h: int):
    frame = _style()['palette']['frame']

    def pillar(px: int, pz: int):
        cub((px, y, pz), (px, y + h - 1, pz), blk(frame.id, axis='y'))

    corners = [(x, z), (x + w - 1, z), (x, z + d - 1), (x + w - 1, z + d - 1)]
    for px, pz in corners:
        pillar(px, pz)
    for dx in range(3, w - 3, 3):
        pillar(x + dx, z)
        pillar(x + dx, z + d - 1)
    for dz in range(3, d - 3, 3):
        pillar(x, z + dz)
        pillar(x + w - 1, z + dz)

    top = y + h - 1
    for dx in range(w):
        editor.placeBlock((x + dx, top, z),         blk(frame.id, axis='x'))
        editor.placeBlock((x + dx, top, z + d - 1), blk(frame.id, axis='x'))
    for dz in range(1, d - 1):
        editor.placeBlock((x,         top, z + dz), blk(frame.id, axis='z'))
        editor.placeBlock((x + w - 1, top, z + dz), blk(frame.id, axis='z'))

def build_walls(x: int, y: int, z: int, w: int, d: int, h: int):
    style           = _style()
    wall            = style['palette']['wall']
    frame           = style['palette']['frame']
    shoji_density   = style['shoji_density']
    window_band_y   = style['window_band_y']
    facing          = _facing()
    door_cx, door_cz, _, _ = _gs_front(x, z, w, d)
    rng = STATE.rng

    def shoji(a: int, b: int):
        is_grid_bar = (a % 2 == 0) or (b % 2 == 0)
        keep_bar = 0.55 + 0.4 * shoji_density
        if is_grid_bar and rng.random() < keep_bar:
            return wall
        return B['paper']

    for dx in range(w):
        for dy in range(h - 1):
            wx, wy, wz = x + dx, y + dy, z
            if facing == 'south' and wx == door_cx and dy < 2:
                editor.placeBlock((wx, wy, wz), AIR)
            elif facing == 'south' and abs(wx - door_cx) == 1:
                editor.placeBlock((wx, wy, wz), blk(frame.id, axis='y'))
            elif dy >= window_band_y and 3 <= dx <= w - 4:
                editor.placeBlock((wx, wy, wz), shoji(dx, dy))
            else:
                editor.placeBlock((wx, wy, wz), wall)

    for dx in range(w):
        for dy in range(h - 1):
            wx, wy, wz = x + dx, y + dy, z + d - 1
            if facing == 'north' and wx == door_cx and dy < 2:
                editor.placeBlock((wx, wy, wz), AIR)
            elif facing == 'north' and abs(wx - door_cx) == 1:
                editor.placeBlock((wx, wy, wz), blk(frame.id, axis='y'))
            elif dy >= window_band_y and 2 <= dx <= w - 3:
                editor.placeBlock((wx, wy, wz), shoji(dx, dy))
            else:
                editor.placeBlock((wx, wy, wz), wall)

    for dz in range(1, d - 1):
        for dy in range(h - 1):
            wx, wy, wz = x, y + dy, z + dz
            if facing == 'west' and wz == door_cz and dy < 2:
                editor.placeBlock((wx, wy, wz), AIR)
            elif facing == 'west' and abs(wz - door_cz) == 1:
                editor.placeBlock((wx, wy, wz), blk(frame.id, axis='y'))
            elif dy >= window_band_y and 2 <= dz <= d - 3:
                editor.placeBlock((wx, wy, wz), shoji(dz, dy))
            else:
                editor.placeBlock((wx, wy, wz), wall)

    # East face
    for dz in range(1, d - 1):
        for dy in range(h - 1):
            wx, wy, wz = x + w - 1, y + dy, z + dz
            if facing == 'east' and wz == door_cz and dy < 2:
                editor.placeBlock((wx, wy, wz), AIR)
            elif facing == 'east' and abs(wz - door_cz) == 1:
                editor.placeBlock((wx, wy, wz), blk(frame.id, axis='y'))
            elif dy >= window_band_y and 2 <= dz <= d - 3:
                editor.placeBlock((wx, wy, wz), shoji(dz, dy))
            else:
                editor.placeBlock((wx, wy, wz), wall)

def build_irimoya_roof(x: int, y: int, z: int, w: int, d: int, h: int):
    roof     = _style()['palette']['roof']
    overhang = _style()['roof_overhang']
    roof_y   = y + h
    max_layers = min(w, d) // 2 - 1

    for layer in range(max_layers):
        ry  = roof_y + layer
        rx1 = x - overhang + layer
        rx2 = x + w - 1 + overhang - layer
        rz1 = z - overhang + layer
        rz2 = z + d - 1 + overhang - layer
        if rx1 >= rx2 or rz1 >= rz2:
            break
        cub((rx1, ry, rz1), (rx2, ry, rz2), roof)
        for bx in range(rx1, rx2 + 1):
            editor.placeBlock((bx, ry, rz1), blk('cherry_stairs', facing='south', half='bottom'))
            editor.placeBlock((bx, ry, rz2), blk('cherry_stairs', facing='north', half='bottom'))
        for bz in range(rz1 + 1, rz2):
            editor.placeBlock((rx1, ry, bz), blk('cherry_stairs', facing='west',  half='bottom'))
            editor.placeBlock((rx2, ry, bz), blk('cherry_stairs', facing='east',  half='bottom'))

    ridge_y = roof_y + max_layers
    ridge_z = z + d // 2
    for bx in range(x - overhang + max_layers - 1, x + w + overhang - max_layers + 1):
        editor.placeBlock((bx, ridge_y,     ridge_z), roof)
        editor.placeBlock((bx, ridge_y + 1, ridge_z), blk('cherry_slab', type='top'))


def build_gable_roof(x: int, y: int, z: int, w: int, d: int, h: int):
    roof     = _style()['palette']['roof']
    overhang = _style()['roof_overhang']
    roof_y   = y + h
    half     = w // 2 + overhang

    for layer in range(half):
        ry  = roof_y + layer
        rx1 = x - overhang + layer
        rx2 = x + w - 1 + overhang - layer
        rz1 = z - overhang
        rz2 = z + d - 1 + overhang
        if rx1 > rx2:
            break
        cub((rx1, ry, rz1), (rx2, ry, rz2), roof)
        for bz in range(rz1, rz2 + 1):
            if rx1 > x - overhang:
                editor.placeBlock((rx1, ry, bz), blk('cherry_stairs', facing='west', half='bottom'))
            if rx2 < x + w - 1 + overhang:
                editor.placeBlock((rx2, ry, bz), blk('cherry_stairs', facing='east', half='bottom'))

    ridge_x = x + w // 2
    ridge_y = roof_y + half
    for bz in range(z - overhang, z + d + overhang):
        editor.placeBlock((ridge_x,     ridge_y,     bz), roof)
        editor.placeBlock((ridge_x,     ridge_y + 1, bz), blk('cherry_slab', type='top'))


def build_broad_low_roof(x: int, y: int, z: int, w: int, d: int, h: int):
    roof     = _style()['palette']['roof']
    overhang = _style()['roof_overhang'] + 1
    roof_y   = y + h
    max_layers = max(1, min(w, d) // 2 - 2)

    for layer in range(max_layers):
        ry  = roof_y + layer
        rx1 = x - overhang + layer
        rx2 = x + w - 1 + overhang - layer
        rz1 = z - overhang + layer
        rz2 = z + d - 1 + overhang - layer
        if rx1 >= rx2 or rz1 >= rz2:
            break
        cub((rx1, ry, rz1), (rx2, ry, rz2), roof)
        for bx in range(rx1, rx2 + 1):
            editor.placeBlock((bx, ry, rz1), blk('cherry_stairs', facing='south', half='bottom'))
            editor.placeBlock((bx, ry, rz2), blk('cherry_stairs', facing='north', half='bottom'))
        for bz in range(rz1 + 1, rz2):
            editor.placeBlock((rx1, ry, bz), blk('cherry_stairs', facing='west', half='bottom'))
            editor.placeBlock((rx2, ry, bz), blk('cherry_stairs', facing='east', half='bottom'))

    ridge_y = roof_y + max_layers
    ridge_z = z + d // 2
    for bx in range(x - overhang + max_layers - 1, x + w + overhang - max_layers + 1):
        editor.placeBlock((bx, ridge_y, ridge_z - 1), roof)
        editor.placeBlock((bx, ridge_y, ridge_z),     roof)
        editor.placeBlock((bx, ridge_y, ridge_z + 1), roof)
        editor.placeBlock((bx, ridge_y + 1, ridge_z), blk('cherry_slab', type='top'))


def build_roof(x: int, y: int, z: int, w: int, d: int, h: int):
    roof_type = _style()['roof_type']
    if roof_type == 'gable':
        build_gable_roof(x, y, z, w, d, h)
    elif roof_type == 'broad_low':
        build_broad_low_roof(x, y, z, w, d, h)
    else:
        build_irimoya_roof(x, y, z, w, d, h)


def add_eave_corner_lanterns(x: int, y: int, z: int, w: int, d: int, h: int):
    overhang  = _style().get('roof_overhang', 1)
    lantern_y = y + h - 1
    corners = [
        (x - overhang,         z - overhang),
        (x + w - 1 + overhang, z - overhang),
        (x - overhang,         z + d - 1 + overhang),
        (x + w - 1 + overhang, z + d - 1 + overhang),
    ]
    for lx, lz in corners:
        editor.placeBlock((lx, lantern_y, lz), blk('lantern', hanging='true'))

def build_lantern_posts(x: int, y: int, z: int, w: int, d: int):
    door_cx, door_cz, fwd, right = _gs_front(x, z, w, d)
    for side in (-3, 3):
        lx = door_cx + right[0] * side + fwd[0]
        lz = door_cz + right[1] * side + fwd[1]
        cub((lx, y + 1, lz), (lx, y + 3, lz), blk('dark_oak_log', axis='y'))
        editor.placeBlock((lx, y + 2, lz), blk('lantern', hanging='true'))


def clear_entry_corridor(x: int, y: int, z: int, w: int, d: int,
                          inside_depth: int = 4, outside_depth: int = 6, half_width: int = 1):
    door_cx, door_cz, fwd, right = _gs_front(x, z, w, d)
    clear_top = y + STATE.HEIGHT - 2

    for step in range(2, inside_depth + 1):
        for side in range(-half_width, half_width + 1):
            wx = door_cx - fwd[0] * step + right[0] * side
            wz = door_cz - fwd[1] * step + right[1] * side
            if x + 1 <= wx <= x + w - 2 and z + 1 <= wz <= z + d - 2:
                cub((wx, y, wz), (wx, min(clear_top, y + 3), wz), AIR)

    for step in range(2, outside_depth + 1):
        for side in range(-half_width, half_width + 1):
            wx = door_cx + fwd[0] * step + right[0] * side
            wz = door_cz + fwd[1] * step + right[1] * side
            base_y = TERR.support_base_y(wx, wz)
            cub((wx, base_y + 1, wz), (wx, clear_top, wz), AIR)
            if base_y < y - 2:
                cub((wx, base_y, wz), (wx, y - 2, wz), STONE)


def place_door_and_steps(x: int, y: int, z: int, w: int, d: int):
    door_cx, door_cz, fwd, _ = _gs_front(x, z, w, d)
    facing = _facing()

    for side in (-1, 0, 1):
        if facing in ('north', 'south'):
            sx, sz = door_cx + side, door_cz + fwd[1]
        else:
            sx, sz = door_cx + fwd[0], door_cz + side
        editor.placeBlock((sx, y - 2, sz), STONE)
        editor.placeBlock((sx, y - 1, sz), blk('stone_brick_stairs', facing=facing, half='bottom'))

    editor.placeBlock((door_cx, y,     door_cz), AIR)
    editor.placeBlock((door_cx, y + 1, door_cz), AIR)
    editor.placeBlock((door_cx, y,     door_cz), blk('dark_oak_door', facing=facing, half='lower', hinge='left'))
    editor.placeBlock((door_cx, y + 1, door_cz), blk('dark_oak_door', facing=facing, half='upper', hinge='left'))

def safe_place(pos, block):
    current = editor.getBlock(pos)
    bid = getattr(current, 'id', str(current))
    if bid in SAFE_OVERWRITE:
        editor.placeBlock(pos, block)


def add_vines_and_foliage(x: int, y: int, z: int, w: int, d: int, h: int):
    style           = _style()
    vine_density    = style['vine_density']
    eave_leaf_density = style['eave_leaf_density']
    rng             = STATE.rng
    leaves          = blk('oak_leaves',                persistent='true')
    azalea          = blk('flowering_azalea_leaves',   persistent='true')
    cherry_leaves   = blk('cherry_leaves',             persistent='true')
    eave_y          = y + h

    for dz in range(1, d - 1, 2):
        for dy in range(h - 1):
            if rng.random() < vine_density:
                editor.placeBlock((x - 1,     y + dy, z + dz), blk('vine', west='true'))
            if rng.random() < vine_density:
                editor.placeBlock((x + w,     y + dy, z + dz), blk('vine', east='true'))
    for dx in range(2, w - 2, 2):
        for dy in range(h - 1):
            if rng.random() < vine_density * 0.5:
                editor.placeBlock((x + dx, y + dy, z - 1), blk('vine', north='true'))
            if rng.random() < vine_density * 0.5:
                editor.placeBlock((x + dx, y + dy, z + d), blk('vine', south='true'))

    corners = [(x - 1, eave_y, z - 1), (x + w, eave_y, z - 1),
               (x - 1, eave_y, z + d), (x + w, eave_y, z + d)]
    for lx, ly, lz in corners:
        for ddx in range(-2, 3):
            for ddz in range(-2, 3):
                if rng.random() < eave_leaf_density:
                    safe_place((lx + ddx, ly, lz + ddz), leaves)
                if rng.random() < eave_leaf_density * 0.4:
                    safe_place((lx + ddx, ly + 1, lz + ddz), cherry_leaves)
        safe_place((lx, ly + 1, lz), azalea)

    overhang = style.get('roof_overhang', 1)
    roof_y   = y + h
    for dx in range(0, w, 3):
        for ddz in (-overhang, d - 1 + overhang):
            safe_place((x + dx, roof_y,     z + ddz), leaves)
            if rng.random() < 0.5:
                safe_place((x + dx, roof_y + 1, z + ddz), cherry_leaves)

    cx = x + w // 2
    for pot_x in (cx - 3, cx + 3):
        editor.placeBlock((pot_x, y, z), blk('potted_fern'))
    for dz in range(2, d - 2, 4):
        for side_x in (x - 1, x + w):
            editor.placeBlock((side_x, y,     z + dz), blk('moss_block'))
            if rng.random() < 0.6:
                editor.placeBlock((side_x, y + 1, z + dz), blk('azalea'))

def place_low_table(cx: int, y: int, cz: int, lx: int = 2, lz: int = 1):
    x1 = cx - lx // 2
    z1 = cz - lz // 2
    for bx in range(x1, x1 + lx):
        for bz in range(z1, z1 + lz):
            editor.placeBlock((bx, y + 1, bz), blk('spruce_slab', type='bottom'))
    for bx, bz in [(x1, z1), (x1 + lx - 1, z1), (x1, z1 + lz - 1), (x1 + lx - 1, z1 + lz - 1)]:
        editor.placeBlock((bx, y, bz), B['dark_oak_fence'])


def place_zabuton(x: int, y: int, z: int):
    editor.placeBlock((x, y, z), blk('brown_carpet'))


def place_tokonoma(x: int, y: int, z: int):
    editor.placeBlock((x,     y, z), blk('smooth_stone_slab', type='top'))
    editor.placeBlock((x + 1, y, z), blk('smooth_stone_slab', type='top'))
    editor.placeBlock((x,     y + 1, z), B['potted_cherry'])
    editor.placeBlock((x + 1, y + 1, z), B['lantern'])


def place_futon(cx: int, y: int, head_z: int):
    editor.placeBlock((cx, y, head_z - 1), blk('white_bed', facing='south', part='foot'))
    editor.placeBlock((cx, y, head_z),     blk('white_bed', facing='south', part='head'))
    for bx, bz in [(cx - 1, head_z), (cx + 1, head_z), (cx, head_z - 2)]:
        editor.placeBlock((bx, y, bz), blk('white_carpet'))


def place_kitchen_corner(x: int, y: int, z: int):
    editor.placeBlock((x,     y,     z), blk('barrel', facing='east'))
    editor.placeBlock((x + 1, y,     z), blk('crafting_table'))
    editor.placeBlock((x + 2, y,     z), blk('smoker'))
    editor.placeBlock((x,     y + 1, z), B['lantern'])
    editor.placeBlock((x + 1, y + 1, z), blk('spruce_trapdoor', open='false', half='bottom'))
    editor.placeBlock((x + 2, y + 1, z), blk('cauldron'))

def get_reserved_entry_cells(x: int, z: int, w: int, d: int, inside_depth: int = 4, half_width: int = 1):
    door_cx, door_cz, fwd, right = _gs_front(x, z, w, d)
    reserved = set()
    for step in range(1, inside_depth + 1):
        for side in range(-half_width, half_width + 1):
            wx = door_cx - fwd[0] * step + right[0] * side
            wz = door_cz - fwd[1] * step + right[1] * side
            if x + 1 <= wx <= x + w - 2 and z + 1 <= wz <= z + d - 2:
                reserved.add((wx, wz))
    return reserved


def rect_intersects_reserved(x1: int, x2: int, z1: int, z2: int, reserved: set):
    return any((bx, bz) in reserved for bx in range(x1, x2 + 1) for bz in range(z1, z2 + 1))


def shift_rect_off_reserved(cx: int, cz: int, lx: int, lz: int, reserved: set,
                             min_x: int, max_x: int, min_z: int, max_z: int,
                             shift_axis: str = 'x'):
    for delta in [0, 1, -1, 2, -2, 3, -3, 4, -4]:
        ncx, ncz = cx, cz
        if shift_axis == 'x':
            ncx += delta
        else:
            ncz += delta
        x1, x2 = ncx - lx // 2, ncx - lx // 2 + lx - 1
        z1, z2 = ncz - lz // 2, ncz - lz // 2 + lz - 1
        if x1 < min_x or x2 > max_x or z1 < min_z or z2 > max_z:
            continue
        if not rect_intersects_reserved(x1, x2, z1, z2, reserved):
            return ncx, ncz
    return cx, cz

def build_interior(x: int, y: int, z: int, w: int, d: int, h: int):
    style      = _style()
    mode       = style.get('interior_mode', 'standard')
    west, east = x + 1, x + w - 2
    south, north = z + 1, z + d - 2
    cx         = x + w // 2
    reserved   = get_reserved_entry_cells(x, z, w, d)
    facing     = _facing()
    shift_axis = 'x' if facing in ('south', 'north') else 'z'

    if style['partition_pos'] == 'near_front':
        part_z = z + max(4, d // 3)
    elif style['partition_pos'] == 'near_back':
        part_z = z + min(d - 5, 2 * d // 3)
    else:
        part_z = z + max(5, d // 2)

    for bx in range(west + 1, east):
        for bz in range(south + 1, part_z - 1):
            if (bx, bz) not in reserved:
                editor.placeBlock((bx, y, bz), blk('moss_carpet'))

    table_len = 2 if mode == 'minimal' else 3
    table_wid = 1 if mode != 'rich' else 2
    table_cx, table_cz = shift_rect_off_reserved(
        cx, (south + part_z) // 2, table_len, table_wid, reserved,
        west + 1, east - 1, south + 1, part_z - 2, shift_axis,
    )
    place_low_table(table_cx, y, table_cz, table_len, table_wid)

    if not rect_intersects_reserved(west + 1, west + 2, south + 1, south + 1, reserved):
        place_tokonoma(west + 1, y, south + 1)

    zabutons = [(table_cx - 2, table_cz), (table_cx + 2, table_cz),
                (table_cx, table_cz - 1), (table_cx, table_cz + 1)]
    if mode == 'minimal':
        zabutons = zabutons[:3]
    for bx, bz in zabutons:
        if west + 1 <= bx <= east - 1 and south + 1 <= bz <= part_z - 2 and (bx, bz) not in reserved:
            place_zabuton(bx, y, bz)

    opening_half = 1 if mode == 'minimal' else 2
    for bx in range(west, east + 1):
        if abs(bx - cx) <= opening_half:
            continue
        editor.placeBlock((bx, y,     part_z), blk('dark_oak_log', axis='x'))
        editor.placeBlock((bx, y + 1, part_z), B['paper'])
        editor.placeBlock((bx, y + 2, part_z), blk('dark_oak_log', axis='x'))

    back_floor = 'white_carpet' if mode == 'rich' else 'brown_carpet'
    for bx in range(west + 1, east):
        for bz in range(part_z + 1, north):
            if (bx, bz) not in reserved:
                editor.placeBlock((bx, y, bz), blk(back_floor))

    futon_cx, futon_head_z = shift_rect_off_reserved(
        cx, north - 1, 1, 2, reserved,
        west + 1, east - 1, part_z + 1, north, shift_axis,
    )
    place_futon(futon_cx, y, futon_head_z + 1)

    if (west + 1, north - 1) not in reserved:
        editor.placeBlock((west + 1, y,     north - 1), blk('barrel', facing='north'))
        editor.placeBlock((west + 1, y + 1, north - 1), B['lantern'])
    if (east - 1, north - 1) not in reserved:
        editor.placeBlock((east - 1, y,     north - 1), blk('barrel', facing='north'))
        editor.placeBlock((east - 1, y + 1, north - 1), B['lantern'])

    if mode in ('standard', 'rich') and east - west >= 8 and north - part_z >= 5:
        if not rect_intersects_reserved(west + 1, west + 3, part_z + 2, part_z + 2, reserved):
            place_kitchen_corner(west + 1, y, part_z + 2)
        for bz in range(part_z + 2, north - 1, 2):
            if (east - 1, bz) not in reserved:
                editor.placeBlock((east - 1, y, bz), blk('barrel', facing='west'))

    if mode == 'rich' and east - west >= 10 and north - part_z >= 7:
        if (east - 2, part_z + 2) not in reserved:
            editor.placeBlock((east - 2, y,     part_z + 2), blk('bookshelf'))
            editor.placeBlock((east - 2, y + 1, part_z + 2), B['lantern'])
        if (east - 2, part_z + 4) not in reserved:
            editor.placeBlock((east - 2, y,     part_z + 4), blk('chest', facing='west'))
            editor.placeBlock((east - 2, y + 1, part_z + 4), B['potted_cherry'])

def build_annex(wx: int, wy: int, wz: int, main_w: int, main_d: int, main_h: int):
    style = _style()
    if not style.get('has_annex'):
        return

    annex_side = style.get('annex_side', 'right')
    aw  = style.get('annex_w', 7)
    ad  = style.get('annex_d', 9)
    ah  = max(3, main_h - 1)
    wall = style['palette']['wall']
    roof = style['palette']['roof']

    ax = wx + main_w if annex_side == 'right' else wx - aw
    az = wz + (main_d // 2) - (ad // 2)

    for dx in range(aw):
        for dz in range(ad):
            col_x, col_z = ax + dx, az + dz
            base_y = TERR.support_base_y(col_x, col_z)
            if base_y < wy - 2:
                cub((col_x, base_y, col_z), (col_x, wy - 2, col_z), STONE)
            cub((col_x, wy, col_z), (col_x, wy + ah + 5, col_z), AIR)
            editor.placeBlock((col_x, wy - 1, col_z), wall)

    for dx in range(aw):
        for dy in range(ah - 1):
            editor.placeBlock((ax + dx, wy + dy, az),          wall)
            editor.placeBlock((ax + dx, wy + dy, az + ad - 1), wall)
    for dz in range(1, ad - 1):
        for dy in range(ah - 1):
            editor.placeBlock((ax,          wy + dy, az + dz), wall)
            editor.placeBlock((ax + aw - 1, wy + dy, az + dz), wall)

    connect_z1   = az + max(1, ad // 2 - 1)
    connect_z2   = az + min(ad - 2, ad // 2 + 1)
    main_wall_x  = wx + main_w - 1 if annex_side == 'right' else wx
    annex_wall_x = ax             if annex_side == 'right' else ax + aw - 1
    for bz in range(connect_z1, connect_z2 + 1):
        for dy in range(2):
            editor.placeBlock((main_wall_x,  wy + dy, bz), AIR)
            editor.placeBlock((annex_wall_x, wy + dy, bz), AIR)

    for layer in range(min(aw, ad) // 2):
        ry  = wy + ah + layer
        rx1 = ax - 1 + layer
        rx2 = ax + aw - layer
        rz1 = az - 1 + layer
        rz2 = az + ad - layer
        if rx1 >= rx2 or rz1 >= rz2:
            break
        cub((rx1, ry, rz1), (rx2, ry, rz2), roof)

    cub((ax + 1, wy, az + 1), (ax + aw - 2, wy + ah - 2, az + ad - 2), AIR)
    for dz in range(1, ad - 1, 2):
        editor.placeBlock((ax + 1,      wy,     az + dz), blk('barrel', facing='east'))
        editor.placeBlock((ax + aw - 2, wy,     az + dz), blk('barrel', facing='west'))
        editor.placeBlock((ax + 1,      wy + 1, az + dz), B['lantern'])

def build_minka(wx: int, wy: int, wz: int):
    w, d, h = STATE.WIDTH, STATE.DEPTH, STATE.HEIGHT
    print(f'Building Minka at world ({wx}, {wy}, {wz}) ...')
    flatten_terrain(wx, wy, wz, w, d)
    cub((wx, wy, wz), (wx + w - 1, wy + h + 8, wz + d - 1), AIR)
    build_stone_foundation(wx, wy, wz, w, d)
    add_under_house_support(wx, wy, wz, w, d, pad=1)
    build_timber_frame(wx, wy, wz, w, d, h)
    build_walls(wx, wy, wz, w, d, h)
    build_roof(wx, wy, wz, w, d, h)
    add_eave_corner_lanterns(wx, wy, wz, w, d, h)
    cub((wx + 1, wy, wz + 1), (wx + w - 2, wy + h - 2, wz + d - 2), AIR)
    build_lantern_posts(wx, wy, wz, w, d)
    add_vines_and_foliage(wx, wy, wz, w, d, h)
    build_interior(wx, wy, wz, w, d, h)
    build_annex(wx, wy, wz, w, d, h)
    clear_entry_corridor(wx, wy, wz, w, d, inside_depth=4, outside_depth=6, half_width=1)
    place_door_and_steps(wx, wy, wz, w, d)
    print('Minka construction complete!')
