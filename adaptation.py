import random

import numpy as np

from helper import (
    B, blk, STATE, clamp_entrance_offset, facing_vectors, front_origin, rot
)
from world import TERR, SEA_LEVEL
from site_selection import find_best_build_site, dry_fraction_fast

def sample_style(rng_: random.Random) -> dict:
    palettes = [
        dict(wall=B['dark_oak_planks'], frame=B['dark_oak_log'],        roof=B['cherry_planks']),
        dict(wall=B['spruce_planks'],   frame=B['stripped_spruce_log'],  roof=B['cherry_planks']),
        dict(wall=B['dark_oak_planks'], frame=B['stripped_spruce_log'],  roof=B['cherry_planks']),
    ]
    i = rng_.randrange(len(palettes))
    return {
        'palette':              palettes[i],
        'palette_index':        i,
        'shoji_density':        rng_.uniform(0.55, 0.90),
        'window_band_y':        rng_.choice([2, 3]),
        'roof_overhang':        rng_.choice([1, 2]),
        'vine_density':         rng_.uniform(0.12, 0.35),
        'eave_leaf_density':    rng_.uniform(0.20, 0.65),
        'garden_tree_pairs':    rng_.choice([1, 2, 3]),
        'garden_tree_spacing':  rng_.choice([6, 7, 8]),
    }


def sample_structure(rng_: random.Random) -> dict:
    footprint = rng_.choice(['compact', 'compact', 'wide', 'deep', 'annex'])
    return {
        'footprint_type':   footprint,
        'entrance_offset':  rng_.choice([-3, 0, 0, 3]),
        'roof_type':        rng_.choice(['irimoya', 'irimoya', 'gable', 'broad_low']),
        'partition_pos':    rng_.choice(['near_front', 'middle', 'near_back']),
        'has_annex':        footprint == 'annex',
        'annex_side':       rng_.choice(['left', 'right']),
        'annex_w':          rng_.choice([5, 7]),
        'annex_d':          rng_.choice([7, 9]),
    }

def candidate_dimension_sets(style: dict):
    ft = style['footprint_type']
    if ft == 'wide':
        return [('large', 27, 17, 7), ('medium', 23, 15, 6), ('small', 19, 13, 5)]
    if ft == 'deep':
        return [('large', 17, 27, 7), ('medium', 15, 23, 6), ('small', 13, 19, 5)]
    return [('large', 25, 21, 7), ('medium', 21, 19, 6), ('small', 17, 15, 5)]


def get_site_scan_dims(main_w: int, main_d: int, style: dict):
    extra_left = extra_right = 0
    if style.get('has_annex'):
        aw = style.get('annex_w', 7)
        if style.get('annex_side', 'right') == 'left':
            extra_left = aw
        else:
            extra_right = aw
    scan_w = main_w + extra_left + extra_right
    scan_d = main_d
    return scan_w, scan_d, extra_left, 0


def choose_best_variant(hmap: np.ndarray, style: dict, rng_: random.Random) -> dict:
    best_pack = None
    for size_name, w, d, h in candidate_dimension_sets(style):
        probe = dict(style)
        pad = 2
        if size_name == 'small':
            probe['has_annex']    = False
            probe['roof_overhang'] = 1
            pad = 1
        elif size_name == 'medium' and probe.get('has_annex'):
            probe['has_annex'] = rng_.random() < 0.5

        scan_w, scan_d, shift_x, shift_z = get_site_scan_dims(w, d, probe)
        result, score_maps = find_best_build_site(
            hmap, house_width=scan_w, house_depth=scan_d,
            padding=pad, origin_shift_x=shift_x, origin_shift_z=shift_z,
        )
        bonus      = {'small': 0.0, 'medium': 0.03, 'large': 0.05}[size_name]
        final_score = score_maps['best_score'] + bonus
        if best_pack is None or final_score > best_pack['final_score']:
            best_pack = {
                'size_name':   size_name,
                'w': w, 'd': d, 'h': h,
                'result':      result,
                'score_maps':  score_maps,
                'final_score': final_score,
                'style':       probe,
            }
    return best_pack

def measure_front_open_space(wx: int, wz: int, w: int, d: int, facing: str,
                             max_steps: int = 26, half_width: int = 5) -> int:
    door_cx, door_cz, fwd, right = front_origin(wx, wz, w, d, facing,
                                                 STATE.STYLE.get('entrance_offset', 0))
    base_y = TERR.support_base_y(door_cx, door_cz)
    usable = 0
    for step in range(1, max_steps + 1):
        ok_cols = 0
        for side in range(-half_width, half_width + 1):
            x = door_cx + fwd[0] * step + right[0] * side
            z = door_cz + fwd[1] * step + right[1] * side
            if not TERR.in_slice(x, z):
                continue
            if abs(TERR.support_base_y(x, z) - base_y) <= 4:
                ok_cols += 1
        if ok_cols < max(4, half_width):
            break
        usable += 1
    return usable


def apply_adaptive_profiles(wx: int, wz: int):
    front_space  = measure_front_open_space(wx, wz, STATE.WIDTH, STATE.DEPTH, STATE.FACING)
    chosen_size  = STATE.STYLE.get('chosen_size_name', 'medium')

    if chosen_size == 'large' and front_space >= 10:
        STATE.STYLE.update(size_mode='large', interior_mode='rich', garden_mode='full')
        return

    if chosen_size in ('large', 'medium') and front_space >= 7:
        STATE.STYLE.update(size_mode='medium', interior_mode='standard', garden_mode='courtyard')
        return

    STATE.STYLE.update(size_mode='small', interior_mode='minimal',
                       garden_mode='flowers_only', has_annex=False, roof_overhang=1)
