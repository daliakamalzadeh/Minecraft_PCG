import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from world import heights, SEA_LEVEL


HEIGHTMAP_DRY   = (heights > SEA_LEVEL).astype(np.float32)
HEIGHTMAP_COAST = ((heights > SEA_LEVEL) & (heights <= SEA_LEVEL + 1)).astype(np.float32)


def integral_image(a: np.ndarray) -> np.ndarray:
    ii = np.pad(a, ((1, 0), (1, 0)), mode='constant')
    return ii.cumsum(axis=0).cumsum(axis=1)


def window_sum(ii: np.ndarray, ox: int, oz: int, w: int, d: int) -> float:
    x2, z2 = ox + w, oz + d
    return float(ii[x2, z2] - ii[ox, z2] - ii[x2, oz] + ii[ox, oz])


DRY_II   = integral_image(HEIGHTMAP_DRY)
COAST_II = integral_image(HEIGHTMAP_COAST)


def dry_fraction_fast(ox: int, oz: int, w: int, d: int) -> float:
    return window_sum(DRY_II, ox, oz, w, d) / float(w * d)


def coast_fraction_fast(ox: int, oz: int, w: int, d: int) -> float:
    return window_sum(COAST_II, ox, oz, w, d) / float(w * d)

def rect_add(diff: np.ndarray, x1: int, z1: int, x2: int, z2: int, val: float):
    diff[x1, z1]         += val
    diff[x2 + 1, z1]     -= val
    diff[x1, z2 + 1]     -= val
    diff[x2 + 1, z2 + 1] += val


def rect_average_from_diffs(sum_diff: np.ndarray, count_diff: np.ndarray):
    sum_map   = sum_diff.cumsum(axis=0).cumsum(axis=1)[:-1, :-1]
    count_map = count_diff.cumsum(axis=0).cumsum(axis=1)[:-1, :-1]
    avg_map   = np.full(sum_map.shape, np.nan, dtype=float)
    mask = count_map > 0
    avg_map[mask] = sum_map[mask] / count_map[mask]
    return avg_map, count_map

def compute_site_summary(hmap: np.ndarray, lx: int, lz: int, w: int, d: int, score: float):
    region   = hmap[lx:lx + w, lz:lz + d]
    median_h = int(np.median(region))
    range_h  = int(region.max() - region.min())
    rough    = int(np.percentile(region, 90) - np.percentile(region, 10))

    max_adj = 0
    if region.shape[0] > 1:
        max_adj = max(max_adj, int(np.max(np.abs(np.diff(region, axis=0)))))
    if region.shape[1] > 1:
        max_adj = max(max_adj, int(np.max(np.abs(np.diff(region, axis=1)))))

    dry_ratio    = dry_fraction_fast(lx, lz, w, d)
    water_ratio  = 1.0 - dry_ratio
    usable_cells = int(round(dry_ratio * w * d))

    return {
        'median_height':     median_h,
        'range_height':      range_h,
        'rough_p90_p10':     rough,
        'max_adjacent_diff': max_adj,
        'water_ratio':       water_ratio,
        'usable_cells':      usable_cells,
        'score':             score,
    }

def find_best_build_site(hmap: np.ndarray, house_width: int, house_depth: int, padding: int = 2,
                         origin_shift_x: int = 0, origin_shift_z: int = 0):
    w, d     = house_width + 2 * padding, house_depth + 2 * padding
    max_x, max_z = hmap.shape
    xs = range(max_x - w + 1)
    zs = range(max_z - d + 1)

    q_flat  = np.zeros((max_x, max_z), dtype=float)
    q_water = np.zeros((max_x, max_z), dtype=float)
    q_elev  = np.zeros((max_x, max_z), dtype=float)
    q_total = np.zeros((max_x, max_z), dtype=float)
    cover_sum_diff   = np.zeros((max_x + 1, max_z + 1), dtype=float)
    cover_count_diff = np.zeros((max_x + 1, max_z + 1), dtype=float)

    best_score, best = -1.0, None
    total = len(xs) * len(zs)
    progress_every = max(1, total // 10)
    print('Scanning world slice for the best build location ...')

    i = 0
    for ox in xs:
        for oz in zs:
            i += 1
            if i % progress_every == 0 or i == total:
                print(f' scanned {i}/{total} windows...')

            region   = hmap[ox:ox + w, oz:oz + d]
            mean_y   = float(np.mean(region))
            target_y = int(mean_y)
            cost     = float(np.sum(np.abs(region - target_y)))

            score_flat  = float(np.exp(-cost / (w * d * 3.0)))
            dryfrac     = dry_fraction_fast(ox, oz, w, d)
            coastfrac   = coast_fraction_fast(ox, oz, w, d)
            waterfrac   = 1.0 - dryfrac
            score_water = max(0.0, dryfrac - 0.18 * coastfrac)
            score_elev  = float(np.exp(-((mean_y - 70.0) ** 2) / (2.0 * 10.0 ** 2)))
            score       = 0.35 * score_flat + 0.45 * score_water + 0.20 * score_elev

            q_flat[ox, oz]  = score_flat
            q_water[ox, oz] = score_water
            q_elev[ox, oz]  = score_elev
            q_total[ox, oz] = score

            x1, z1 = ox, oz
            x2, z2 = ox + w - 1, oz + d - 1
            rect_add(cover_sum_diff,   x1, z1, x2, z2, score)
            rect_add(cover_count_diff, x1, z1, x2, z2, 1.0)

            if waterfrac > 0.18:
                continue
            if score > best_score:
                best_score = score
                best = (ox + padding + origin_shift_x, oz + padding + origin_shift_z, target_y)

    if best is None:
        print('WARNING: No ideal dry site found. Falling back to a believable coastal site.')
        valid = q_total[:max_x - w + 1, :max_z - d + 1]
        order = np.argsort(valid.ravel())[::-1]
        for k in order[:12000]:
            ox, oz = np.unravel_index(k, valid.shape)
            cx = ox + padding + origin_shift_x + house_width // 2
            cz = oz + padding + origin_shift_z + house_depth // 2
            if int(hmap[cx, cz]) < SEA_LEVEL:
                continue
            if (1.0 - dry_fraction_fast(ox, oz, w, d)) > 0.30:
                continue
            region = hmap[ox:ox + w, oz:oz + d]
            best = (ox + padding + origin_shift_x, oz + padding + origin_shift_z, int(np.mean(region)))
            best_score = float(valid[ox, oz])
            break
        if best is None:
            raise RuntimeError('Could not find a believable build site.')

    coverage_avg, coverage_count = rect_average_from_diffs(cover_sum_diff, cover_count_diff)

    score_maps = {
        'heights':        hmap,
        'flatness':       q_flat,
        'water':          q_water,
        'elevation':      q_elev,
        'total':          q_total,
        'coverage_avg':   coverage_avg,
        'coverage_count': coverage_count,
        'best_ox':        best[0] - padding - origin_shift_x,
        'best_oz':        best[1] - padding - origin_shift_z,
        'win_w':          w,
        'win_d':          d,
        'best_score':     best_score,
    }
    print(f'Best site: local ({best[0]}, {best[1]}), height {best[2]} | score {best_score:.4f}')
    return best, score_maps

def save_build_site_score_heatmap(score_maps: dict, site_lx: int, site_lz: int,
                                  site_w: int, site_d: int,
                                  out_dir: str = 'terrain_plots'):
    os.makedirs(out_dir, exist_ok=True)

    heatmap      = np.array(score_maps['coverage_avg'], dtype=float)
    valid_scores = heatmap[np.isfinite(heatmap)]
    if valid_scores.size == 0:
        raise RuntimeError('Heatmap contains no valid evaluated cells.')

    vmin, vmax = float(valid_scores.min()), float(valid_scores.max())
    display_scores = np.full_like(heatmap, np.nan, dtype=float)
    if vmax - vmin < 1e-9:
        display_scores[np.isfinite(heatmap)] = 255.0
    else:
        display_scores[np.isfinite(heatmap)] = (
            255.0 * (heatmap[np.isfinite(heatmap)] - vmin) / (vmax - vmin)
        )

    summary = compute_site_summary(
        score_maps['heights'], site_lx, site_lz, site_w, site_d, score_maps['best_score']
    )
    text = (
        f"CHOSEN SITE\n"
        f"x=[{site_lx},{site_lx + site_w - 1}] z=[{site_lz},{site_lz + site_d - 1}]\n\n"
        f"median_height: {summary['median_height']}\n"
        f"range_height: {summary['range_height']}\n"
        f"rough (p90-p10): {summary['rough_p90_p10']}\n"
        f"max_adjacent_diff: {summary['max_adjacent_diff']}\n"
        f"water_ratio: {summary['water_ratio']:.3f}\n"
        f"usable_cells: {summary['usable_cells']}\n"
        f"score: {summary['score']:.3f}"
    )

    fig, ax = plt.subplots(figsize=(10, 8))
    cmap = plt.cm.viridis.copy()
    cmap.set_bad(color='#e8e8e8')
    im   = ax.imshow(display_scores.T, origin='lower', cmap=cmap, vmin=0, vmax=255)
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('score')

    rect = Rectangle((site_lx, site_lz), site_w, site_d,
                     linewidth=2.5, edgecolor='white', facecolor='none', linestyle='--')
    ax.add_patch(rect)
    ax.text(site_lx + site_w / 2, site_lz + site_d + 1.5, 'chosen',
            color='white', ha='center', va='center', fontsize=10)

    best_ox = score_maps.get('best_ox')
    best_oz = score_maps.get('best_oz')
    if best_ox is not None and best_oz is not None:
        ax.text(best_ox, best_oz, 'best', color='yellow', fontsize=9, ha='left', va='bottom')

    ax.text(0.02, 0.98, text, transform=ax.transAxes, va='top', ha='left', fontsize=10,
            bbox=dict(boxstyle='round,pad=0.5', fc='white', ec='0.4', alpha=0.92))

    ax.set_title('Build Site Score Heatmap')
    ax.set_xlabel('Local X')
    ax.set_ylabel('Local Z')
    fig.tight_layout()

    out_path = os.path.join(out_dir, 'build_site_score_heatmap.png')
    fig.savefig(out_path, dpi=200, bbox_inches='tight')
    plt.close(fig)
    print(f"Build-site score heatmap saved to '{out_path}'")


def save_raw_heightmap(hmap: np.ndarray, site_lx: int, site_lz: int,
                       site_w: int, site_d: int,
                       out_dir: str = 'terrain_plots'):
    os.makedirs(out_dir, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 8))
    im   = ax.imshow(hmap.T, origin='lower', cmap='terrain')
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Height (blocks)')

    rect = Rectangle((site_lx, site_lz), site_w, site_d,
                     linewidth=2.5, edgecolor='white', facecolor='none')
    ax.add_patch(rect)

    ax.set_title('Raw Heightmap with Chosen Build Site')
    ax.set_xlabel('Local X')
    ax.set_ylabel('Local Z')
    fig.tight_layout()

    out_path = os.path.join(out_dir, 'raw_heightmap.png')
    fig.savefig(out_path, dpi=200, bbox_inches='tight')
    plt.close(fig)
    print(f"Raw heightmap saved to '{out_path}'")