# AOC Simplification Experiments

This tracked development area turns the visual AOC-first notebook strategy into
small, reproducible, one-region experiments. It never writes to `assets/data`.
Generated candidates are inspection artefacts, not production data.

## Active Strategy

The current geometry pipeline is:

1. repair AOC geometry;
2. dissolve by `region`, `app`, and `colour`;
3. apply morphological closing with an outward and inward metric buffer;
4. simplify with topology preservation;
5. repair again;
6. optionally partition overlaps, with smaller complete appellations taking
   priority;
7. perform final polygon-only repair and validation;
8. reproject to EPSG:4326; and
9. compare the result with the deployed app geometry.

Smallest-wins partitioning is the final geometry-changing operation: the
result is not buffered or simplified again. This prevents later processing
from recreating overlap.

There are deliberately no minimum-area, maximum-part, or largest-polygon
controls. Earlier experiments showed that those controls can destroy local
coverage.

## Notebook And Scripts

`AOC_Simplification_Strategy_Lab.ipynb` remains the visual sense-check tool for
understanding geometry changes. `simplification.py` contains the reusable
geometry operations. `run_experiment.py` performs one named regional run and
writes its candidate, plots, parameters, and metrics. The notebook is not
rewritten around the module; it can continue to be inspected independently.

Inputs:

- `Development/WineData/aoc_regions.gpkg`: inherited AOC source;
- `assets/data/wine_regions_cleaned.geojson`: old app comparison baseline.

Outputs are ignored by Git and live at:

```text
Development/aoc_simplification/outputs/<region_slug>/<run_id>/
├── candidate.geojson
├── preview.png
├── comparison.png
├── overlap_comparison.png
├── metrics.json
└── params.json
```

Region and run slugs use lowercase ASCII, remove accents, and replace
punctuation with underscores. The original display name remains in candidate
data and metadata. Examples include `Rhône` to `rhone`, `Sud-Ouest` to
`sud_ouest`, and `Languedoc-Roussillon` to `languedoc_roussillon`.

## Running One Experiment

From the repository root:

```bash
.venv/bin/python Development/aoc_simplification/run_experiment.py \
  --region "Bordeaux" \
  --run-id close500_smallest_wins \
  --buffer 500 \
  --simplify 250 \
  --overlap-strategy smallest-wins
```

Runs do not overwrite one another. Pass `--overwrite` only when deliberately
replacing the same region/run ID.

## Initial Ladder

Use this as a small starting ladder, one region at a time:

| Run ID | Overlap strategy | Buffer (m) | Simplify (m) |
| --- | --- | ---: | ---: |
| `raw_simplified` | `none` | 0 | 250 |
| `close250` | `none` | 250 | 250 |
| `close500` | `none` | 500 | 250 |
| `close500_simple500` | `none` | 500 | 500 |
| `close500_smallest_wins` | `smallest-wins` | 500 | 250 |

## Smallest-Appellation-Wins Partitioning

The `smallest-wins` strategy creates mutually exclusive app-facing AOC
geometry. Priority is calculated from the area of each complete processed
`region + app` geometry after dissolve, closing, simplification, and repair.
The smallest complete appellation keeps its geometry; progressively broader
appellations lose area already claimed by smaller ones. This removes overlap
from the data itself instead of relying on map trace or rendering order.
Residual overlap is accepted only within floating-point tolerance:
`max(1e-6 m², union area × 1e-10)`. The exact tolerance and measured residual
are recorded in `metrics.json` and `params.json`.

Area is only a practical proxy for appellation specificity, not a formal legal
hierarchy. The strategy is therefore a regional candidate for manual review,
not a final policy for every wine region. Run Bordeaux with:

```bash
.venv/bin/python Development/aoc_simplification/run_experiment.py \
  --region "Bordeaux" \
  --run-id close500_smallest_wins \
  --buffer 500 \
  --simplify 250 \
  --overlap-strategy smallest-wins
```

After reviewing Bordeaux, a separate Bourgogne run is:

```bash
.venv/bin/python Development/aoc_simplification/run_experiment.py \
  --region "Bourgogne" \
  --run-id close500_smallest_wins \
  --buffer 500 \
  --simplify 250 \
  --overlap-strategy smallest-wins
```

`overlap_comparison.png` aligns the simplified pre-partition geometry, the
partitioned result, and the area removed from broader appellations. Review it
with `preview.png`, `comparison.png`, and the per-app removed-area diagnostics
in `metrics.json`. Fully covered appellations are reported as warnings rather
than disappearing silently. Accept or reject one regional result before
moving to the next region.

Inspect `preview.png` for the candidate alone, `comparison.png` for aligned
old/source/candidate panels, and `overlap_comparison.png` for the partition
effect. Use `metrics.json` to compare validity, overlap, per-app removed area,
coordinates, polygon parts, and approximate payload. Record a preferred run in
`region_policy.csv` only after the visual and metric checks agree; keep status
and notes provisional until a candidate is genuinely accepted.

## Region Decision Table

`region_policy.csv` is the central old-versus-raw-versus-candidate decision
table. Refresh its metrics from completed experiment folders with:

```bash
.venv/bin/python Development/aoc_simplification/update_region_policy_metrics.py
```

The old app geometry is a payload and detail benchmark, not necessarily a
fidelity benchmark; some old regions are intentionally or grossly simplified.
Raw-to-candidate ratios show the simplification and area change introduced by
an experiment. Old-to-candidate ratios show how much heavier or more detailed
the candidate is than the current app layer. These values are evidence rather
than automatic pass/fail thresholds: size, area, part count, and coordinate
count each require interpretation. Complete the human assessment and notes
fields only after viewing the experiment's comparison plots.

## Merged Development Dataset

`datasets/aoc_regions_close500.geojson` combines the completed regional
`outputs/*/close500/candidate.geojson` files into one development test asset.
The merge utility validates every candidate and concatenates the rows in
deterministic region-slug order. It preserves AOC-level features rather than
dissolving by region or app.

The merge performs no repair, simplification, buffering, clipping, pruning, or
other geometry processing. It only normalises CRS to EPSG:4326 when necessary,
then refuses to write invalid, empty, malformed, or duplicate features. Run it
from the repository root with:

```bash
.venv/bin/python Development/aoc_simplification/merge_candidates.py
```

The utility protects an existing merged dataset by default. To regenerate it
deliberately after candidate changes, use:

```bash
.venv/bin/python Development/aoc_simplification/merge_candidates.py --overwrite
```

The merged GeoJSON and its adjacent metrics JSON are tracked development
artifacts. They are not production assets, are not read by the app, and will be
wired into the Wine page only in a separate future change.

The entire `outputs/` tree is intentionally untracked. No command in this
directory promotes or copies a candidate into `assets/data`.
