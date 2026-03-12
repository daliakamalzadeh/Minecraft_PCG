from helper import (
    B, AIR, STONE, MOSSY, ANDESITE, SAFE_OVERWRITE, AIR_IDS, NON_SOLID_IDS,
    blk, STATE, rot
)
from world import editor, TERR, cub, SEA_LEVEL


def _style():
    return STATE.STYLE

def _gs_front(wx, wz, w, d):
    return STATE.gs_front_origin(wx, wz, w, d)

def safe_place(pos, block):
    current = editor.getBlock(pos)
    bid = getattr(current, 'id', str(current))
    if bid in SAFE_OVERWRITE:
        editor.placeBlock(pos, block)


def support_to_ground(x: int, top_y: int, z: int, top_block=STONE):
    base_y = TERR.support_base_y(x, z)
    if base_y < top_y - 1:
        cub((x, base_y, z), (x, top_y - 2, z), STONE)
    editor.placeBlock((x, top_y - 1, z), top_block)

def place_garden_lantern_post(x: int, y: int, z: int, post_height: int = 3):
    support_to_ground(x, y + 1, z, MOSSY)
    cub((x, y, z), (x, y + post_height - 1, z), blk('dark_oak_log', axis='y'))
    editor.placeBlock((x, y + post_height,     z), ANDESITE)
    editor.placeBlock((x, y + post_height - 1, z), blk('lantern', hanging='false'))

def build_garden_path(ox: int, py: int, oz: int, fwd: tuple, right: tuple,
                      length: int = 10, width: int = 3):
    half = width // 2
    y    = py - 1
    flower_choices = [blk(name) for name in
                      ['oxeye_daisy', 'white_tulip', 'allium', 'poppy', 'red_tulip', 'dandelion']]
    rng = STATE.rng

    for df in range(length):
        for dr in range(-half, half + 1):
            wx, wz    = rot(ox, oz, fwd, right, df, dr)
            top_block = B['dirt_path'] if dr == 0 else B['mossy_cobblestone']
            support_to_ground(wx, y + 1, wz, top_block)
        for side in (-half - 1, half + 1):
            wx, wz = rot(ox, oz, fwd, right, df, side)
            support_to_ground(wx, y + 1, wz, B['dirt_path'])
            if df % 2 == 0:
                editor.placeBlock((wx, y + 1, wz), rng.choice(flower_choices))
        if df % 4 == 0:
            for side in (-half - 2, half + 2):
                wx, wz = rot(ox, oz, fwd, right, df, side)
                place_garden_lantern_post(wx, y, wz)

def build_garden_beds(door_cx: int, door_cz: int, fwd: tuple, right: tuple,
                      gy: int, max_df: int = 8):
    plants  = [blk('cherry_sapling'), blk('azalea'), blk('flowering_azalea'), blk('fern')]
    flowers = [blk(name) for name in ['oxeye_daisy', 'white_tulip', 'allium', 'poppy']]
    rng = STATE.rng

    for side_sign in (-1, 1):
        for df in range(2, max_df + 1):
            for dr in [side_sign * r for r in range(4, 9)]:
                wx, wz = rot(door_cx, door_cz, fwd, right, df, dr)
                if TERR.support_base_y(wx, wz) <= SEA_LEVEL:
                    continue
                editor.placeBlock((wx, gy - 1, wz), MOSSY)
                editor.placeBlock((wx, gy,     wz), blk('dirt'))
                if rng.random() > 0.25:
                    editor.placeBlock((wx, gy + 1, wz), rng.choice(plants))
        for dr in (side_sign * 4, side_sign * 8):
            wx, wz = rot(door_cx, door_cz, fwd, right, 1, dr)
            if TERR.support_base_y(wx, wz) <= SEA_LEVEL:
                continue
            editor.placeBlock((wx, gy,     wz), blk('dirt'))
            editor.placeBlock((wx, gy + 1, wz), rng.choice(flowers))

def build_cherry_trees(door_cx: int, door_cz: int, fwd: tuple, right: tuple,
                       gy: int, approach_df_start: int, count_pairs: int = 2, spacing: int = 6):
    canopy_r = 1 if spacing <= 6 else 2
    for i in range(count_pairs):
        df = approach_df_start + i * spacing + 2
        for dr in (-5, 5):
            tx, tz = rot(door_cx, door_cz, fwd, right, df, dr)
            base_y = TERR.support_base_y(tx, tz)
            if base_y < gy - 1:
                cub((tx, base_y, tz), (tx, gy - 1, tz), blk('cherry_log', axis='y'))
            cub((tx, gy, tz), (tx, gy + 4, tz), blk('cherry_log', axis='y'))
            for ddx in range(-canopy_r, canopy_r + 1):
                for ddz in range(-canopy_r, canopy_r + 1):
                    for ddy in range(4):
                        if abs(ddx) + abs(ddz) + ddy <= canopy_r * 2:
                            safe_place((tx + ddx, gy + 3 + ddy, tz + ddz),
                                       blk('cherry_leaves', persistent='true'))

def clear_garden_area(wx: int, wy: int, wz: int, house_width: int, house_depth: int):
    door_cx, door_cz, fwd, right = _gs_front(wx, wz, house_width, house_depth)
    clear_top = wy + STATE.HEIGHT - 2
    for df in range(1, 20):
        for dr in range(-10, 11):
            x = door_cx + fwd[0] * df + right[0] * dr
            z = door_cz + fwd[1] * df + right[1] * dr
            if wx - 1 <= x <= wx + house_width and wz - 1 <= z <= wz + house_depth:
                continue
            base_y = TERR.support_base_y(x, z)
            for cy in range(base_y + 1, clear_top):
                bid = TERR.block_id_at(x, cy, z)
                if bid in AIR_IDS:
                    continue
                if bid in NON_SOLID_IDS | SAFE_OVERWRITE:
                    editor.placeBlock((x, cy, z), AIR)


def flatten_garden_area(door_cx: int, door_cz: int, fwd: tuple, right: tuple,
                        gy: int, depth: int = 14, half_width: int = 8,
                        wx_house: int = 0, wz_house: int = 0,
                        house_width: int = 0, house_depth: int = 0):
    for df in range(2, depth + 1):
        for dr in range(-half_width, half_width + 1):
            x, z = rot(door_cx, door_cz, fwd, right, df, dr)
            if not TERR.in_slice(x, z):
                continue
            if (wx_house - 2 <= x <= wx_house + house_width + 1 and
                    wz_house - 2 <= z <= wz_house + house_depth + 1):
                continue
            actual_y = TERR.support_base_y(x, z)
            if actual_y <= SEA_LEVEL:
                continue
            if actual_y < gy - 1:
                cub((x, actual_y, z), (x, gy - 2, z), STONE)
                editor.placeBlock((x, gy - 1, z), B['dirt_path'])
            elif actual_y > gy - 1:
                cub((x, gy, z), (x, actual_y + 2, z), AIR)
                editor.placeBlock((x, gy - 1, z), B['dirt_path'])

def build_garden(wx: int, wy: int, wz: int, house_width: int, house_depth: int):
    style    = _style()
    door_cx, door_cz, fwd, right = _gs_front(wx, wz, house_width, house_depth)
    ground_y = wy
    mode     = style.get('garden_mode', 'full')

    flatten_garden_area(door_cx, door_cz, fwd, right, ground_y,
                        wx_house=wx, wz_house=wz,
                        house_width=house_width, house_depth=house_depth)

    if mode == 'flowers_only':
        path_ox, path_oz = rot(door_cx, door_cz, fwd, right, 2, 0)
        build_garden_path(path_ox, ground_y, path_oz, fwd, right, length=6,  width=3)
        build_garden_beds(door_cx, door_cz, fwd, right, ground_y, max_df=5)
        print('Compact garden built.')
        return

    if mode == 'courtyard':
        path_ox, path_oz = rot(door_cx, door_cz, fwd, right, 2, 0)
        build_garden_path(path_ox, ground_y, path_oz, fwd, right, length=10, width=3)
        build_garden_beds(door_cx, door_cz, fwd, right, ground_y, max_df=7)
        build_cherry_trees(door_cx, door_cz, fwd, right, ground_y,
                           approach_df_start=8, count_pairs=1, spacing=8)
        print('Courtyard garden built.')
        return

    path_ox, path_oz = rot(door_cx, door_cz, fwd, right, 2, 0)
    build_garden_path(path_ox, ground_y, path_oz, fwd, right, length=14, width=3)
    build_garden_beds(door_cx, door_cz, fwd, right, ground_y, max_df=8)
    build_cherry_trees(
        door_cx, door_cz, fwd, right, ground_y,
        approach_df_start=10,
        count_pairs=style['garden_tree_pairs'],
        spacing=style['garden_tree_spacing'],
    )
    print('Full garden built.')
