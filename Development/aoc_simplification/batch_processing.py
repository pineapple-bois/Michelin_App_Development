# .venv/bin/python - <<'PY'     # TODO: REMOVE COMMENT (and this)
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import geopandas as gpd

PROJECT_ROOT = Path.cwd()
EXPERIMENT_DIR = PROJECT_ROOT / "Development" / "aoc_simplification"
SOURCE = PROJECT_ROOT / "Development" / "WineData" / "aoc_regions.gpkg"
RUNNER = EXPERIMENT_DIR / "run_experiment.py"
OUTPUTS = EXPERIMENT_DIR / "outputs"

RUN_ID = "close500_smallest_wins"

sys.path.insert(0, str(EXPERIMENT_DIR))
from simplification import slugify_region  # noqa: E402

source = gpd.read_file(
    SOURCE,
    engine="pyogrio",
    columns=["region"],
)

regions = sorted(
    {
        str(value).strip()
        for value in source["region"].dropna()
        if str(value).strip()
    }
)

completed: list[str] = []
skipped: list[str] = []
failed: list[str] = []

for region in regions:
    region_slug = slugify_region(region)
    candidate = OUTPUTS / region_slug / RUN_ID / "candidate.geojson"

    if candidate.is_file():
        print(f"SKIP     {region}: candidate already exists")
        skipped.append(region)
        continue

    print(f"\nRUN      {region}")

    result = subprocess.run(
        [
            str(PROJECT_ROOT / ".venv" / "bin" / "python"),
            str(RUNNER),
            "--region",
            region,
            "--run-id",
            RUN_ID,
            "--buffer",
            "500",
            "--simplify",
            "250",
            "--overlap-strategy",
            "smallest-wins",
        ],
        cwd=PROJECT_ROOT,
        check=False,
    )

    if result.returncode == 0 and candidate.is_file():
        completed.append(region)
    else:
        failed.append(region)
        print(f"FAILED   {region}: exit code {result.returncode}")

print("\nBatch summary")
print(f"Completed: {len(completed)}")
print(f"Skipped:   {len(skipped)}")
print(f"Failed:    {len(failed)}")

if completed:
    print("\nCompleted regions:")
    for region in completed:
        print(f"  - {region}")

if skipped:
    print("\nSkipped existing regions:")
    for region in skipped:
        print(f"  - {region}")

if failed:
    print("\nFailed regions:")
    for region in failed:
        print(f"  - {region}")
    raise SystemExit(1)
# PY   # TODO: REMOVE COMMENT (and this)