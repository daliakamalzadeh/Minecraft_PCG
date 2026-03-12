import logging

from helper import make_rng, clamp_entrance_offset, STATE
from world import heights, STARTX, STARTZ
from site_selection import save_raw_heightmap, save_build_site_score_heatmap
from adaptation import sample_style, sample_structure, choose_best_variant, apply_adaptive_profiles
from house import build_minka
from garden import clear_garden_area, build_garden

logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s')


def main():
    rng, _ = make_rng()
    STATE.rng = rng

    style = sample_style(rng)
    style.update(sample_structure(rng))
    STATE.STYLE  = style
    STATE.FACING = rng.choice(['north', 'south', 'east', 'west'])

    best = choose_best_variant(heights, STATE.STYLE, rng)
    STATE.WIDTH, STATE.DEPTH, STATE.HEIGHT = best['w'], best['d'], best['h']
    STATE.STYLE.update(best['style'])
    STATE.STYLE['chosen_size_name'] = best['size_name']

    result     = best['result']
    score_maps = best['score_maps']

    print(f"[PCG] Chosen size: {best['size_name']} -> {STATE.WIDTH}x{STATE.DEPTH}x{STATE.HEIGHT}")
    print(f'[PCG] Facing: {STATE.FACING}')
    print(f"[PCG] Footprint: {STATE.STYLE['footprint_type']}")
    print(f"[PCG] Entrance offset: "
          f"{clamp_entrance_offset(STATE.WIDTH, STATE.DEPTH, STATE.FACING, STATE.STYLE['entrance_offset'])}")
    print(f"[PCG] Roof: type={STATE.STYLE['roof_type']}, overhang={STATE.STYLE['roof_overhang']}")
    print(f"[PCG] Annex: {STATE.STYLE['has_annex']} side={STATE.STYLE['annex_side']} "
          f"w={STATE.STYLE['annex_w']} d={STATE.STYLE['annex_d']}")
    print(f"[PCG] Palette index: {STATE.STYLE['palette_index']}")

    lx, lz, ly = result

    save_raw_heightmap(
        heights,
        site_lx=lx, site_lz=lz,
        site_w=STATE.WIDTH, site_d=STATE.DEPTH,
        out_dir='terrain_plots',
    )
    save_build_site_score_heatmap(
        score_maps,
        site_lx=lx, site_lz=lz,
        site_w=STATE.WIDTH, site_d=STATE.DEPTH,
        out_dir='terrain_plots',
    )

    world_x = STARTX + lx
    world_y = ly
    world_z = STARTZ + lz

    apply_adaptive_profiles(world_x, world_z)
    print(f"[PCG] Adaptive: size_mode={STATE.STYLE['size_mode']}, "
          f"interior={STATE.STYLE['interior_mode']}, garden={STATE.STYLE['garden_mode']}")

    build_minka(world_x, world_y, world_z)
    clear_garden_area(world_x, world_y, world_z, house_width=STATE.WIDTH, house_depth=STATE.DEPTH)
    build_garden(world_x, world_y, world_z, house_width=STATE.WIDTH, house_depth=STATE.DEPTH)


if __name__ == '__main__':
    main()
