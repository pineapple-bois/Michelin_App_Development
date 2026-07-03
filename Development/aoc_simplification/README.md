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
| `close500_simplify150` | `smallest-wins` | 500 | 150 |

## Smallest-Appellation-Wins Partitioning

The `smallest-wins` strategy creates mutually exclusive app-facing AOC
geometry. Priority is calculated from the area of each complete processed
`region + app` geometry after dissolve, closing, simplification, and repair.
The smallest complete appellation keeps its geometry; progressively broader
appellations lose area already claimed by smaller ones. This removes overlap
from the data itself instead of relying on map trace or rendering order.
Residual overlap is accepted only within floating-point tolerance:
`max(1e-6 m², union area × 1e-9)`. The exact tolerance and measured residual
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

### `close500_simplify150` removal investigation

The newest complete batch is `close500_simplify150`. Its saved metrics show
that all 354 appellations survive source repair, dissolve, closing, and
simplification. Loss happens only during smallest-wins partitioning:

- 347 appellations retain geometry;
- 7 become exactly empty and are omitted from the candidate;
- 148 retained appellations lose some overlap area; and
- 21 retained appellations lose at least 99% of their processed area, leaving
  only a small or sometimes microscopic sliver.

The exactly covered appellations are:

| Region | Fully covered appellation | Earlier equal-area priority row(s) |
| --- | --- | --- |
| Bordeaux | Saint-Emilion grand cru | Saint-Emilion |
| Dordogne | Haut-Montravel | Côtes de Montravel |
| Languedoc-Roussillon | Banyuls grand cru | Banyuls |
| Languedoc-Roussillon | Collioure | Banyuls / Banyuls grand cru |
| Languedoc-Roussillon | Limoux | Crémant de Limoux |
| Languedoc-Roussillon | Muscat de Rivesaltes | Grand Roussillon |
| Rhône | Crémant de Die | Coteaux de Die |

In each case, the saved pre-partition priority area is exactly equal to an
earlier appellation's area. The partition sort uses processed area ascending,
then app label ascending. Coextensive appellations therefore make alphabetical
order an ownership rule: the first label claims the complete footprint and a
later label receives nothing. Near-coextensive cases produce tiny residual
slivers instead of exact empties.

Comparing the earlier 250 m run with the 150 m batch shows essentially the same
near-total-removal set. Lower simplification changes a few empty-versus-sliver
outcomes, but does not resolve coextensive source appellations. All 12 current
`close500_simplify150` candidates reload as valid EPSG:4326 geometry with no
empty features, so invalid export geometry is not the cause of these losses.

Ways to avoid unintended disappearance require an explicit product decision:

- detect coextensive or near-coextensive appellations before partitioning and
  represent them as aliases or a multi-label footprint;
- use a reviewed appellation-priority table instead of area-plus-alphabetical
  tie-breaking;
- preserve fully covered appellations in a separate metadata/catalogue layer
  even when they have no unique app-facing polygon;
- allow selected coextensive appellations to overlap, accepting that strict
  mutual exclusivity no longer holds; or
- add a report-only review gate for fully covered and near-total-removal cases
  before a regional result is accepted.

`source_area_m2` can make priority comparisons more stable and expose source
footprint equivalence, but using it as the priority key would not by itself
solve genuinely identical footprints. Reducing closing or simplification may
alter boundary slivers, but the batch comparison shows it is not the primary
fix for the coextensive cases.

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

## Batch-to-Merge Workflow

The scripts form a staged workflow. Do not treat a successful batch run as an
automatic acceptance decision.

### 1. Configure and run the regional batch

`batch_processing.py` is currently configuration-by-code rather than a CLI.
Before running it, verify that its `RUN_ID` and the runner arguments agree. The
newest completed regime used:

```text
RUN_ID = "close500_simplify150"
--buffer 500
--simplify 150
--overlap-strategy smallest-wins
```

Then run from the repository root:

```bash
.venv/bin/python Development/aoc_simplification/batch_processing.py
```

The batch skips regions whose candidate already exists and exits non-zero if
any region fails. It writes only under ignored `outputs/<region_slug>/<run_id>/`
directories.

### 2. Review removal and validity evidence

Refresh the tracked policy table from the selected run:

```bash
.venv/bin/python Development/aoc_simplification/update_region_policy_metrics.py \
  --run-id close500_simplify150
```

Review `partition.fully_covered_app_names` and `partition.per_app` in each
`metrics.json`. A retained feature with a removal percentage near 100% may be
functionally absent even though its geometry is technically non-empty.

If a candidate is invalid, run the diagnostic utility for that region without
`--repair-in-place` first:

```bash
.venv/bin/python Development/aoc_simplification/diagnose_invalid_candidates.py \
  --region "Bourgogne" \
  --run-id close500_simplify150
```

Diagnostic reports and plots are written beneath
`outputs/_invalid_diagnostics/<region_slug>/<run_id>/`. The normal diagnostic
command is read-only with respect to candidates. `--repair-in-place` is a
separate, deliberately mutating action that creates a timestamped backup; use
it only after reviewing the local repair evidence and area change.

### 3. Merge only a complete, valid run

The merge utility validates schema, CRS, geometry validity, emptiness,
duplicates, region coverage, and numeric `source_area_m2`. It concatenates AOC
features without dissolving or changing geometry:

```bash
.venv/bin/python Development/aoc_simplification/merge_candidates.py \
  --run-id close500_simplify150 \
  --output Development/aoc_simplification/datasets/aoc_regions_close500_simplify150.geojson
```

If that tracked development dataset already exists and replacement is
intentional, add `--overwrite`. App wiring and promotion into `assets/data`
remain separate decisions after regional visual and metric review.

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
