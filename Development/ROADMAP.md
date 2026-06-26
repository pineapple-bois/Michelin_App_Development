# Wine Region Development Roadmap

## Purpose

`Development/` now holds a clean restart for the Wine-page geometry work. The aim is to build a more comprehensive French wine-region map while keeping the app payload small enough for quick Dash page loads.

The deployable app should continue to read compact GeoJSON from `assets/data/` through `app/app_data.py`. Large AOC source data and notebook-only inspection tooling belong here until a candidate has passed visual and payload checks.

## Current Working State

- `Wine_Regions.ipynb`: active notebook for the fresh workflow.
- `wine_workflow.py`: lightweight command-line source check and strategy summary.
- `WineData/aoc_regions.gpkg`: cleaned AOC source, approximately 397 MB, 354 MultiPolygon rows. Keep local or manage through a large-file/artifact route rather than normal Git staging.
- `Reference_Notebooks/France_Wine1.ipynb`: historical notebook showing earlier cleanup and simplification attempts.
- `Reference_Notebooks/France_Wine2.ipynb`: historical notebook focused on overlap removal and Bordeaux/AOC simplification.
- `functions_wine.py` and `functions_visualisation.py`: inherited helper material retained for reference; do not assume these are required by the fresh workflow.
- `requirements_wine_dev.txt`: optional notebook-regeneration dependencies, separate from production `requirements.txt`.

The previous generated GeoJSON outputs have been removed from `WineData/`:

- `bordeaux_simplified.geojson`
- `regions_simplified.geojson`
- `regions_simplified_wgs84.geojson`
- `wine_regions_cleaned.geojson`

This keeps the restart honest: new candidate outputs should be generated deliberately and named with their strategy/parameters.

## Verified Source Contract

`WineData/aoc_regions.gpkg` is already attribute-clean and should be treated as the source of truth for this development pass:

- Required columns: `region`, `app`, `colour`, `geometry`.
- CRS: EPSG:4326.
- Rows: 354 AOCs.
- Regions: 12.
- No null or blank `region`, `app`, or `colour` values.
- No duplicate `app` rows.
- No missing or empty geometries.
- Some geometries report invalid topology; repair this during dissolve/export rather than rerunning legacy merge work.

## Minimal Checks

From the repository root:

```bash
.venv/bin/python Development/wine_workflow.py
```

This validates the source contract, prints per-region AOC counts, and lists candidate payload-reduction strategies. It does not require Folium, Branca, MapClassify, scikit-learn, or AlphaShape.

For notebook inspection, open:

```text
Development/Wine_Regions.ipynb
```

The fresh notebook should stay short enough that rerunning the early inspection cells is cheap.

## Strategy Questions

The new notebook should answer these in order:

1. What does the raw AOC source contain?
2. What does the national AOC footprint look like by region?
3. How heavy is the raw source, and where does complexity concentrate?
4. Can a dissolved 12-region geometry preserve enough recognisable wine geography?
5. How much simplification is possible before the map becomes misleading?
6. Is AOC-level detail worth keeping as a separate optional layer, or should AOCs remain generation-only provenance?

## Candidate Strategy Ladder

Start with the cheapest honest baselines before trying more elaborate algorithms:

1. Raw AOC inspection only.
   Useful for human QA, too heavy for direct app loading.

2. Dissolve by `region`.
   Creates one region geometry per wine region. This is the first serious baseline.

3. Repair, project, dissolve, simplify, reproject.
   Use a metric CRS for simplification, then write app-facing EPSG:4326 GeoJSON.

4. Compare simplification tolerances.
   Record file size, coordinate count, polygon-part count, and visual acceptability.

5. Test hull-style reductions only as a stress test.
   Very light payloads may be too geographically crude for a wine map.

6. Consider detail-on-demand AOCs later.
   If AOC-level information matters, keep it as a separate deferred data path rather than loading every AOC into the first Wine-page view.

## Promotion Criteria

Before any new file is promoted into `assets/data/`:

1. App-facing GeoJSON is EPSG:4326.
2. Required columns match the app contract: `region`, `colour`, `geometry`.
3. File size stays comfortably below 1 MB.
4. Coordinate count stays modest enough for the Wine page to feel quick.
5. Region coverage gain is explicit and documented.
6. Visual QA checks national view and several regional zooms.
7. Wine click handling no longer depends on fragile curve-number ordering, or the current behaviour is covered by a targeted test.
8. Existing smoke tests pass.

## Package Boundary

Production dependencies should not grow because of notebook experiments. The deployed Wine page should need only compact GeoJSON plus the current app stack.

Notebook-only dependencies belong in `requirements_wine_dev.txt`. Keep Folium, Branca, MapClassify, Matplotlib, Seaborn, scikit-learn, and AlphaShape out of `requirements.txt` unless a supported non-notebook command genuinely needs them.

## Next Steps

1. Run the source scan in `wine_workflow.py`.
2. Use `Wine_Regions.ipynb` to plot the raw AOC source and a dissolved region overview.
3. Add one small generation cell at a time, writing outputs only under a clearly named generated path once parameters are chosen.
4. Compare payload and visual quality before touching app data paths.
