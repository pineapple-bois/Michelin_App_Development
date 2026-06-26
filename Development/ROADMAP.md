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

## Current Wine Map Development Status

### Failed candidate experiment: dissolve plus tolerance simplification

The first 12-region candidate experiment tested a plain workflow:

1. Repair invalid AOC geometries.
2. Project to EPSG:2154.
3. Dissolve by region.
4. Simplify with metre-based tolerances.
5. Reproject to EPSG:4326 and export GeoJSON.

The result is not good enough for the app. Key observed metrics:

| Candidate | File size | Coordinate count | Geometry parts | Invalid geometries | Area retained |
| --- | ---: | ---: | ---: | ---: | ---: |
| `dissolved_region_raw.geojson` | 513.407 MB | 12,530,958 | 134,997 | 2 | n/a |
| `dissolved_region_simplified_1000m.geojson` | 40.819 MB | 969,912 | 140,074 | 1 | 72.317% |
| `dissolved_region_simplified_5000m.geojson` | 40.652 MB | 965,781 | 140,572 | 1 | 69.015% |

Increasing simplification tolerance from 1000 m to 5000 m barely reduced file size or coordinate count and increased geometry part count. The limiting problem is excessive polygon fragments and multipart complexity, not simple vertex density. Plain tolerance-based simplification should not be continued as the main path.

Visual inspection confirms the same failure mode: `dissolved_region_simplified_1000m.geojson` renders Languedoc-Roussillon mostly as dense outline and fragment noise, with thousands of tiny polygon parts rather than a readable app-facing region.

Generated candidate files and experiment scripts are development artefacts only. They are not production artefacts, should not be promoted into `assets/data/`, and should not be tracked unless a deliberate artifact-management decision is made.

The failed experiment scripts have been binned under:

```text
Development/_experiments/wine_map_2026_06_failed_dissolve_simplify/
```

That folder is intentionally ignored.

### Next proposed strategy

The next serious candidate-generation strategy should target polygon fragment complexity directly. The previous dissolve + simplify attempt showed that vertex simplification alone does not solve the problem: it leaves a very large, highly fragmented shape that is visually noisy and unsuitable for the app.

The next strategy should treat the Wine map as an app-level regional visualisation rather than an exact AOC-boundary aggregation.

Candidate generation should proceed incrementally:

1. Dissolve source geometries by app-facing region.
2. Explode multipart geometries into individual polygon parts.
3. Prune tiny fragments by area in a metric CRS.
4. Optionally retain only the largest parts per region, with special care for legitimately fragmented regions and islands.
5. Simplify remaining parts.
6. Repair geometries.
7. Prune again after repair/simplification if new fragments appear.
8. Export only after metrics and visual QA show a plausible app payload.

If source-faithful pruning still produces noisy or heavy results, abstracted region shapes are an acceptable fallback. This may include buffered/dissolved envelopes, softened hulls, or manually curated simplified region geometries.

No new app-facing candidate should be considered until it passes visual QA and basic payload criteria:
- 12 app-facing regions
- valid geometries
- no empty geometries
- stable `region`, `app`, `colour`, and `geometry` fields
- substantially reduced file size
- substantially reduced coordinate and part counts
- visually credible at national map scale

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
   This has now been tested as a first baseline and is not sufficient by itself.

3. Repair, project, dissolve, simplify, reproject.
   Plain tolerance-based simplification has been tested and should not be pursued further as the main path.

4. Fragment-pruning candidate.
   Explode dissolved geometries, prune tiny fragments by area, optionally keep largest parts per region, simplify, repair, prune again, and then measure.

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
2. Use `Wine_Regions.ipynb` to inspect source data and candidate assumptions without committing generated outputs.
3. Prototype fragment-pruning in small, inspectable steps.
4. Compare payload and visual quality before touching app data paths.
