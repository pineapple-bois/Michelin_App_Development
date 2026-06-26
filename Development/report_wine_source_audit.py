"""Interpret the generated Wine source audit outputs.

This script reads the deterministic CSV/JSON files produced by
``wine_workflow.py --audit`` and writes an inspectable plain-English report.
It does not read or write app assets and does not create candidate GeoJSON.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


HERE = Path(__file__).resolve().parent
DEFAULT_AUDIT_DIR = HERE / "WineData" / "generated" / "audit"
EXPECTED_APP_REGIONS = [
    "Alsace",
    "Bordeaux",
    "Bourgogne",
    "Corse",
    "Dordogne",
    "Jura",
    "Languedoc-Roussillon",
    "Loire",
    "Provence",
    "Rhône",
    "Savoie",
    "Sud-Ouest",
]
SIMPLIFICATION_TOLERANCES = "500 m, 1000 m, 2500 m, and 5000 m"


def display_path(path):
    path = Path(path)
    try:
        return str(path.resolve().relative_to(HERE))
    except ValueError:
        return str(path)


def read_audit_inputs(audit_dir):
    audit_dir = Path(audit_dir)
    paths = {
        "contract": audit_dir / "source_contract.json",
        "summary": audit_dir / "region_summary.csv",
        "complexity": audit_dir / "geometry_complexity_by_region.csv",
        "top_aocs": audit_dir / "top_complex_aocs.csv",
    }
    missing = [display_path(path) for path in paths.values() if not path.exists()]
    if missing:
        raise SystemExit("Missing audit input files:\n- " + "\n- ".join(missing))

    with paths["contract"].open(encoding="utf-8") as handle:
        contract = json.load(handle)

    return {
        "contract": contract,
        "summary": pd.read_csv(paths["summary"]),
        "complexity": pd.read_csv(paths["complexity"]),
        "top_aocs": pd.read_csv(paths["top_aocs"]),
    }


def percentage(value, total):
    if not total:
        return 0.0
    return round((float(value) / float(total)) * 100, 2)


def format_int(value):
    return f"{int(value):,}"


def format_pct(value):
    return f"{float(value):.2f}%"


def source_is_fit(contract):
    blockers = [
        contract.get("crs") != "EPSG:4326",
        contract.get("row_count", 0) <= 0,
        bool(contract.get("missing_required_columns")),
        contract.get("null_attribute_values", 0) > 0,
        contract.get("blank_attribute_values", 0) > 0,
        contract.get("duplicate_app_rows", 0) > 0,
        contract.get("missing_geometries", 0) > 0,
        contract.get("empty_geometries", 0) > 0,
    ]
    return not any(blockers)


def classify_aoc_count(summary):
    q1 = summary["aoc_count"].quantile(0.25)
    q3 = summary["aoc_count"].quantile(0.75)
    high = summary[summary["aoc_count"] > q3].sort_values(
        ["aoc_count", "region"], ascending=[False, True], kind="mergesort"
    )
    low = summary[summary["aoc_count"] < q1].sort_values(
        ["aoc_count", "region"], ascending=[True, True], kind="mergesort"
    )
    return high, low


def qa_priority(row):
    share = row["coordinate_share_pct"]
    invalid_count = row["invalid_geometry_count"]
    rank = row["complexity_rank"]
    if rank <= 4 or share >= 10 or invalid_count >= 10:
        return "high"
    if rank <= 8 or share >= 3 or invalid_count > 0:
        return "medium"
    return "low"


def recommended_preview_zoom(row):
    if row["qa_priority"] == "high":
        return "national plus close regional zoom"
    if row["qa_priority"] == "medium":
        return "national plus regional zoom"
    return "national sanity check"


def likely_strategy_risk(row):
    share = row["coordinate_share_pct"]
    part_count = row["geometry_part_count"]
    invalid_count = row["invalid_geometry_count"]
    if share >= 15 or part_count >= 50_000:
        return "high"
    if share >= 5 or invalid_count > 0:
        return "medium"
    return "low"


def region_notes(row):
    notes = []
    if row["coordinate_share_pct"] >= 15:
        notes.append("dominates coordinate payload")
    if row["geometry_part_count"] >= 50_000:
        notes.append("many polygon parts")
    if row["invalid_geometry_count"] > 0:
        notes.append("repair before candidate export")
    if row["aoc_count"] <= 4 and row["coordinate_share_pct"] >= 3:
        notes.append("low AOC count but complex shapes")
    if not notes:
        notes.append("lower-complexity baseline QA")
    return "; ".join(notes)


def build_decision_table(summary, complexity):
    region_frame = complexity.merge(
        summary[["region", "source_coordinate_count"]],
        on="region",
        how="left",
        validate="one_to_one",
    )
    total_coordinates = int(region_frame["approximate_coordinate_count"].sum())
    region_frame["coordinate_share_pct"] = region_frame["approximate_coordinate_count"].apply(
        lambda value: percentage(value, total_coordinates)
    )
    region_frame["complexity_rank"] = (
        region_frame["approximate_coordinate_count"]
        .rank(method="first", ascending=False)
        .astype(int)
    )

    table = region_frame.rename(
        columns={
            "approximate_coordinate_count": "coordinate_count",
            "polygon_part_count": "geometry_part_count",
        }
    )[
        [
            "region",
            "aoc_count",
            "coordinate_count",
            "coordinate_share_pct",
            "geometry_part_count",
            "invalid_geometry_count",
            "complexity_rank",
        ]
    ].copy()
    table["qa_priority"] = table.apply(qa_priority, axis=1)
    table["recommended_preview_zoom"] = table.apply(recommended_preview_zoom, axis=1)
    table["likely_strategy_risk"] = table.apply(likely_strategy_risk, axis=1)
    table["notes"] = table.apply(region_notes, axis=1)
    return table.sort_values(["complexity_rank", "region"], kind="mergesort").reset_index(drop=True)


def markdown_table(frame, columns=None, max_rows=None):
    if columns is not None:
        frame = frame[columns]
    if max_rows is not None:
        frame = frame.head(max_rows)
    if frame.empty:
        return "None."

    rows = []
    headers = [str(column) for column in frame.columns]
    rows.append("| " + " | ".join(headers) + " |")
    rows.append("| " + " | ".join("---" for _ in headers) + " |")
    for _, row in frame.iterrows():
        values = [str(row[column]) for column in frame.columns]
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join(rows)


def source_contract_section(contract):
    fit = source_is_fit(contract)
    geometry_counts = ", ".join(
        f"{key}: {value}" for key, value in sorted(contract.get("geometry_type_counts", {}).items())
    )
    bounds = contract.get("total_bounds", {})
    missing_counts = {
        "missing_required_columns": len(contract.get("missing_required_columns", [])),
        "null_attribute_values": contract.get("null_attribute_values"),
        "blank_attribute_values": contract.get("blank_attribute_values"),
        "duplicate_app_rows": contract.get("duplicate_app_rows"),
        "missing_geometries": contract.get("missing_geometries"),
        "empty_geometries": contract.get("empty_geometries"),
    }

    lines = [
        "## 1. Source contract summary",
        "",
        f"- Source path: `{contract.get('source_path')}`.",
        f"- CRS: `{contract.get('crs')}`.",
        f"- Row count: {format_int(contract.get('row_count', 0))}.",
        f"- Region count: {format_int(contract.get('region_count', 0))}.",
        f"- AOC count: {format_int(contract.get('aoc_count', 0))}.",
        f"- Geometry type counts: {geometry_counts}.",
        f"- Invalid geometry count: {format_int(contract.get('invalid_geometry_count', 0))}.",
        f"- Source file size: {contract.get('source_file_size_mb')} MB.",
        (
            "- Total bounds: "
            f"minx {bounds.get('minx'):.6f}, miny {bounds.get('miny'):.6f}, "
            f"maxx {bounds.get('maxx'):.6f}, maxy {bounds.get('maxy'):.6f}."
        ),
        "- Missing/null field checks:",
    ]
    lines.extend(f"  - {key}: {value}" for key, value in missing_counts.items())
    if fit:
        lines.append(
            "- Fitness judgement: fit for candidate generation. The remaining issue is topology repair, not missing source attribution."
        )
    else:
        lines.append(
            "- Fitness judgement: not fit for candidate generation until the blocking contract issues above are resolved."
        )
    if contract.get("invalid_geometry_count", 0):
        lines.append(
            "- Interpretation: invalid geometries should be repaired in the generation/export step before dissolve and simplification candidates are written."
        )
    return "\n".join(lines)


def coverage_section(summary):
    high, low = classify_aoc_count(summary)
    represented = set(summary["region"])
    missing = [region for region in EXPECTED_APP_REGIONS if region not in represented]
    unexpected = sorted(represented.difference(EXPECTED_APP_REGIONS))
    coverage_note = (
        "All expected app-facing regions are represented."
        if not missing
        else "Missing expected regions: " + ", ".join(missing) + "."
    )
    if unexpected:
        coverage_note += " Unexpected region labels present: " + ", ".join(unexpected) + "."

    lines = [
        "## 2. Region coverage summary",
        "",
        coverage_note,
        "",
        "AOC counts by region:",
        "",
        markdown_table(summary[["region", "aoc_count", "invalid_geometry_count"]]),
        "",
        "Regions with unusually high AOC counts are above the upper quartile of this source:",
        "",
        markdown_table(high[["region", "aoc_count"]]) if not high.empty else "None.",
        "",
        "Regions with unusually low AOC counts are below the lower quartile:",
        "",
        markdown_table(low[["region", "aoc_count"]]) if not low.empty else "None.",
        "",
        "Interpretation: the coverage is broad enough for a 12-region app-facing baseline. Very small regions still need visual checks because low AOC count does not necessarily mean low geometry complexity.",
    ]
    return "\n".join(lines)


def complexity_section(decision_table, contract):
    total_coordinates = int(decision_table["coordinate_count"].sum())
    top5 = decision_table.sort_values(["complexity_rank", "region"], kind="mergesort").head(5)
    source_size = contract.get("source_file_size_mb")

    lines = [
        "## 3. Geometry complexity summary",
        "",
        f"- Approximate total coordinate count: {format_int(total_coordinates)}.",
        f"- Source file size baseline: {source_size} MB. This is source-data scale, not acceptable first-load app payload scale.",
        "- The highest-complexity regions dominate any raw-AOC payload and should drive candidate QA.",
        "",
        "Coordinate and part counts by region:",
        "",
        markdown_table(
            decision_table[
                [
                    "region",
                    "coordinate_count",
                    "coordinate_share_pct",
                    "geometry_part_count",
                    "complexity_rank",
                ]
            ]
        ),
        "",
        "Top 5 most complex regions:",
        "",
        markdown_table(
            top5[
                [
                    "region",
                    "coordinate_count",
                    "coordinate_share_pct",
                    "geometry_part_count",
                    "qa_priority",
                ]
            ]
        ),
    ]
    return "\n".join(lines)


def top_aocs_section(top_aocs, total_coordinates):
    top10 = top_aocs.head(10).copy()
    top10["coordinate_share_pct"] = top10["coordinate_count"].apply(
        lambda value: percentage(value, total_coordinates)
    )
    top3_share = percentage(top10.head(3)["coordinate_count"].sum(), total_coordinates)
    top10_share = percentage(top10["coordinate_count"].sum(), total_coordinates)
    concentration = (
        "strongly concentrated in a handful of AOCs"
        if top10_share >= 35
        else "meaningfully concentrated in the largest AOCs, but still spread across regions"
    )

    lines = [
        "## 4. Top complex AOCs",
        "",
        f"- Top 3 AOCs account for {format_pct(top3_share)} of source coordinates.",
        f"- Top 10 AOCs account for {format_pct(top10_share)} of source coordinates.",
        f"- Interpretation: complexity is {concentration}.",
        "",
        markdown_table(
            top10[
                [
                    "region",
                    "app",
                    "coordinate_count",
                    "polygon_part_count",
                    "coordinate_share_pct",
                    "is_invalid_geometry",
                ]
            ]
        ),
    ]
    return "\n".join(lines)


def strategy_section(decision_table):
    high_priority = decision_table[decision_table["qa_priority"].eq("high")]["region"].tolist()
    medium_priority = decision_table[decision_table["qa_priority"].eq("medium")]["region"].tolist()
    lines = [
        "## 5. Implications for strategy",
        "",
        "- Raw AOC loading is unsuitable for the app first load. The 396.629 MB source and multi-million coordinate baseline are generation inputs, not deployed page data.",
        "- Dissolve-by-region should be the first serious baseline because the mission is an app-facing wine-region map, not an AOC explorer.",
        f"- Test simplify-after-dissolve tolerances first at {SIMPLIFICATION_TOLERANCES}.",
        "- Hull-style reductions should remain stress tests only; they may prove payload floors, but they risk losing recognisable wine geography.",
        "- Repair invalid geometries before export, then compare candidate metrics against this audit baseline.",
        "",
        "High-priority visual QA regions:",
        "",
        ", ".join(high_priority) if high_priority else "None.",
        "",
        "Medium-priority visual QA regions:",
        "",
        ", ".join(medium_priority) if medium_priority else "None.",
    ]
    return "\n".join(lines)


def recommended_actions_section():
    lines = [
        "## 6. Recommended next actions",
        "",
        "1. Generate a dissolved raw 12-region baseline with topology repair, no simplification, and EPSG:4326 export.",
        f"2. Generate simplify-after-dissolve candidates at {SIMPLIFICATION_TOLERANCES}.",
        "3. Generate preview PNGs for national view and high-priority regional zooms.",
        "4. Compare candidate file size, coordinate count, polygon part count, invalid geometry count, and visual quality against this audit baseline.",
        "5. Only after a candidate passes the comparison should app data paths or click-handling behaviour be considered.",
    ]
    return "\n".join(lines)


def build_report(contract, summary, decision_table, top_aocs):
    total_coordinates = int(decision_table["coordinate_count"].sum())
    sections = [
        "# Wine Source Audit Interpretation",
        "",
        "This report interprets the generated source audit for the Wine-page map work. It is a development artifact only; it does not promote GeoJSON into the app.",
        "",
        source_contract_section(contract),
        "",
        coverage_section(summary),
        "",
        complexity_section(decision_table, contract),
        "",
        top_aocs_section(top_aocs, total_coordinates),
        "",
        strategy_section(decision_table),
        "",
        recommended_actions_section(),
        "",
    ]
    return "\n".join(sections)


def write_notebook(path, report_text):
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [line + "\n" for line in report_text.splitlines()],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "from pathlib import Path\n",
                    "import pandas as pd\n",
                    "\n",
                    "AUDIT_DIR = Path('Development/WineData/generated/audit')\n",
                    "if not AUDIT_DIR.exists():\n",
                    "    AUDIT_DIR = Path('WineData/generated/audit')\n",
                    "\n",
                    "decision_table = pd.read_csv(AUDIT_DIR / 'audit_decision_table.csv')\n",
                    "region_summary = pd.read_csv(AUDIT_DIR / 'region_summary.csv')\n",
                    "top_complex_aocs = pd.read_csv(AUDIT_DIR / 'top_complex_aocs.csv')\n",
                    "display(decision_table)\n",
                ],
            },
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def write_report_outputs(audit_dir, write_notebook_report=True):
    audit = read_audit_inputs(audit_dir)
    contract = audit["contract"]
    summary = audit["summary"].sort_values("region", kind="mergesort").reset_index(drop=True)
    complexity = audit["complexity"].sort_values("region", kind="mergesort").reset_index(drop=True)
    top_aocs = audit["top_aocs"].sort_values(
        ["coordinate_count", "polygon_part_count", "region", "app"],
        ascending=[False, False, True, True],
        kind="mergesort",
    ).reset_index(drop=True)

    decision_table = build_decision_table(summary, complexity)
    report = build_report(contract, summary, decision_table, top_aocs)

    audit_dir = Path(audit_dir)
    report_path = audit_dir / "audit_report.md"
    decision_table_path = audit_dir / "audit_decision_table.csv"
    notebook_path = audit_dir / "Wine_Source_Audit_Report.ipynb"

    report_path.write_text(report, encoding="utf-8")
    decision_table.to_csv(decision_table_path, index=False)
    if write_notebook_report:
        write_notebook(notebook_path, report)

    return {
        "report": report_path,
        "decision_table": decision_table_path,
        "notebook": notebook_path if write_notebook_report else None,
    }


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument(
        "--no-notebook",
        action="store_true",
        help="Skip writing the optional Wine_Source_Audit_Report.ipynb.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    outputs = write_report_outputs(
        args.audit_dir,
        write_notebook_report=not args.no_notebook,
    )
    print("Wrote wine source audit interpretation outputs")
    for path in outputs.values():
        if path is not None:
            print(f"- {display_path(path)}")


if __name__ == "__main__":
    main()
