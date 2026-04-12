import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from snitch.models import SastResult


def write_json(results: list[SastResult], output_path: Path) -> None:
    """Write findings as a JSON array to output_path."""
    rows = [
        {
            "filename": r.filename,
            "filepath": str(r.filepath),
            **r.finding,
        }
        for r in results
    ]
    output_path.write_text(
        json.dumps(rows, indent=2), encoding="utf-8"
    )


def write_csv(results: list[SastResult], output_path: Path) -> None:
    """Write findings as a CSV file to output_path."""
    fieldnames = ["filename", "filepath", "where", "what", "why", "fix"]
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL
        )
        writer.writeheader()
        for r in results:
            writer.writerow(
                {
                    "filename": r.filename,
                    "filepath": str(r.filepath),
                    **r.finding,
                }
            )


def write_text(results: list[SastResult], output_path: Path) -> None:
    """Write findings as a human-readable text report to output_path."""
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    divider = "=" * 72
    separator = "-" * 72

    lines = [
        "SNITCH SAST REPORT",
        f"Generated: {timestamp}",
        f"Total findings: {len(results)}",
        divider,
        "",
    ]

    for i, r in enumerate(results, start=1):
        lines += [
            f"[{i}] {r.filename}",
            f"    File:  {r.filepath}",
            f"    Where: {r.finding.get('where', '')}",
            f"    What:  {r.finding.get('what', '')}",
            f"    Why:   {r.finding.get('why', '')}",
            f"    Fix:   {r.finding.get('fix', '')}",
            "",
            separator,
            "",
        ]

    output_path.write_text("\n".join(lines), encoding="utf-8")


FORMAT_WRITERS = {
    "json": write_json,
    "csv": write_csv,
    "txt": write_text,
}


def write_output(
    results: list[SastResult],
    output_dir: Path,
    fmt: str,
    stem: str = "snitch_results",
) -> Path:
    """Write results in fmt format to output_dir/stem.<fmt>.

    Returns the path of the written file.
    """
    output_path = output_dir / f"{stem}.{fmt}"
    FORMAT_WRITERS[fmt](results, output_path)
    return output_path
