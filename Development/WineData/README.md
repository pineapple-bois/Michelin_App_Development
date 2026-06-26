# WineData

This directory expects the local source file:

```text
aoc_regions.gpkg
```

The file is the cleaned AOC source used by `../Wine_Regions.ipynb` and `../wine_workflow.py`.

Current local contract:

- CRS: EPSG:4326.
- Rows: 354 AOCs.
- Geometry type: MultiPolygon.
- Required columns: `region`, `app`, `colour`, `geometry`.
- Known topology issue: some geometries are invalid before repair. Repair during dissolve/export rather than rerunning legacy merge cleanup.

Do not commit generated GeoJSON outputs here by accident. When candidate outputs are created, write them under a clearly named generated path and record the strategy, simplification tolerance, file size, coordinate count, and visual QA notes before promotion to `assets/data/`.
