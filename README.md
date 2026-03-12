# Japanese-Inspired Minka PCG for Minecraft

This project is a procedural content generator that builds a Japanese-inspired **minka** house inside a GDPC/Minecraft build area. It first scans the terrain to find a believable build site, then generates a house, interior, and front garden with randomized variation.

## What the project does

The generator is designed around three goals:

- **Believability**: avoid obviously bad locations such as water-heavy regions and adapt the house to the terrain.
- **Variation**: randomize the house size, footprint, roof, palette, annex, orientation, interior layout, and garden composition.
- **Adaptation**: flatten only a local area, extend supports when needed, and shape the front path and garden to the surroundings.

## Project structure

- `mypcg.py` — main entry point that runs the full pipeline.
- `world.py` — loads the GDPC build area, world slice, heightmap, and terrain helper logic.
- `site_selection.py` — evaluates terrain and produces the raw heightmap and build-site score heatmap.
- `adaptation.py` — samples styles/structures, chooses the best house variant, and adapts richness to available front space.
- `house.py` — builds the main minka structure.
- `garden.py` — clears the front area and builds the garden/path.
- `helper.py` — shared block definitions, RNG helpers, orientation helpers, and shared mutable state.
- `images/` — example outputs used in the report.
- `terrain_plots/` — generated terrain plots written during execution.

## How it works

### 1. Build area and terrain loading

The script connects to GDPC through `Editor`, retrieves the active build area, and loads the world slice heightmap using `MOTION_BLOCKING_NO_LEAVES`.

That heightmap is the basis for all terrain evaluation.

### 2. Terrain evaluation and site selection

The generator scans many overlapping rectangular candidate windows over the build area.

For each candidate region, it computes three scores:

- **Flatness score**: favors terrain that needs little cutting/filling.
- **Water suitability score**: favors dry land and penalizes shoreline-heavy regions.
- **Elevation preference score**: softly prefers moderate elevations around height 70.

These are combined into one final score:

- `0.35 * flatness`
- `0.45 * water suitability`
- `0.20 * elevation preference`

Windows with more than 18% water coverage are rejected.

The best valid site is selected as the final build location.

### 3. Variant selection

The generator does not always build the same footprint. It tries several size options depending on the sampled footprint type:

- compact
- wide
- deep
- annex-based layout

Each candidate size is evaluated on the terrain, and the best one is chosen.

### 4. House generation

After the site is selected, the script builds the minka in stages:

- local terrain flattening
- stone foundation and under-supports
- timber frame
- walls and shoji-style window panels
- one of multiple roof variants
- optional annex
- interior furniture and partitioning
- lanterns, foliage, and decorative details

### 5. Garden generation

The generator clears the front area and builds one of several garden profiles:

- flowers only
- courtyard
- full garden

This depends on how much usable space exists in front of the entrance.

## Randomized variation

Each run samples a new random seed unless you modify the code to fix one.

Variation includes:

- house orientation
- footprint type
- house size
- roof type
- material palette
- entrance offset
- partition location
- annex presence, side, and size
- shoji density and window band height
- foliage density
- garden type, cherry tree count, and spacing

## Generated outputs

Running the generator creates terrain visualizations in `terrain_plots/`:

- `raw_heightmap.png`
- `build_site_score_heatmap.png`

These are useful for debugging and for the report.

## Requirements

You need:

1. **Python 3.10+**
2. A working **Minecraft + GDMC/GDPC** setup
3. An active GDPC HTTP interface / editor connection
4. A selected build area in the Minecraft world

## Python dependencies

Install the Python packages with:

```bash
pip install -r requirements.txt
```

## How to run

From the project directory:

```bash
python mypcg.py
```

If the GDPC connection is working and a build area is defined, the script will:

1. load the world slice
2. scan for a build site
3. save the terrain plots
4. build the house
5. clear the front area and build the garden

## Typical workflow

1. Start Minecraft with the GDMC HTTP interface enabled.
2. Open or create a world.
3. Mark/select a build area (/buildarea set ~ ~ ~ ~100 ~100 ~100).
4. Place this project in your Python environment.
5. Install the dependencies.
6. Run `python mypcg.py`.

## Notes and limitations

- The project assumes a **100x100-style assignment build area**, but it reads the active build area from GDPC.
- The generator deliberately avoids many tiny island-like or water-heavy placements because they are considered less believable.
- Some terrain adaptations can still create exposed platform edges in difficult environments.
- Interior placement is only partially rotation-aware.

## Troubleshooting

### `Could not find a believable build site`

The selected area is probably too wet, too constrained, or too extreme for the current heuristics. Try another build area.

### GDPC connection errors

Make sure Minecraft, the GDMC HTTP mod/server interface, and the selected build area are all active before running the script.

### Missing plot files

The plots are written to `terrain_plots/`. If that folder is missing after a run, the script likely stopped before site-selection finished.

## Reproducibility

By default, the generator uses a random seed each run. To reproduce a specific result, modify the seed handling in `make_rng()` or pass a fixed seed manually in the code.

## Author

Dalia Kamalzadeh
