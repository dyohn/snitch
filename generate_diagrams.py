#!/usr/bin/env python3
"""generate_diagrams.py — PDF diagrams for the LaTeX paper.

Usage:
    python generate_diagrams.py --diagram snitch-components
    python generate_diagrams.py --diagram all
"""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("pdf")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.patches as mpatches  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

DIAGRAMS_DIR = Path("diagrams")

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------

_BLUE = dict(fc="#dbeafe", ec="#1d4ed8", lw=1.8)  # snitch module
_YELLOW = dict(fc="#fef9c3", ec="#b45309", lw=1.8)  # external entity
_GRAY = dict(fc="#f1f5f9", ec="#64748b", lw=1.5, ls="--")  # pkg boundary

_C_ARROW = "#1e3a5f"
_C_HTTP = "#7c3aed"

# ---------------------------------------------------------------------------
# Shared drawing helpers
# ---------------------------------------------------------------------------


def _save(fig: plt.Figure, name: str, data: dict) -> None:
    """Save figure as PDF and persist source data as JSON."""
    DIAGRAMS_DIR.mkdir(exist_ok=True)
    pdf = DIAGRAMS_DIR / f"{name}.pdf"
    djson = DIAGRAMS_DIR / f"{name}_data.json"
    fig.savefig(str(pdf), format="pdf", bbox_inches="tight")
    plt.close(fig)
    djson.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"  {pdf}  +  {djson.name}")


def _box(
    ax,
    cx: float,
    cy: float,
    w: float,
    h: float,
    title: str,
    subtitle: str = "",
    style: dict = None,
) -> None:
    """Draw a rounded component box centred at (cx, cy)."""
    if style is None:
        style = _BLUE
    ax.add_patch(
        FancyBboxPatch(
            (cx - w / 2, cy - h / 2),
            w,
            h,
            boxstyle="round,pad=0.04",
            facecolor=style["fc"],
            edgecolor=style["ec"],
            linewidth=style.get("lw", 1.5),
            linestyle=style.get("ls", "-"),
            zorder=3,
            clip_on=False,
        )
    )
    if subtitle:
        ax.text(
            cx,
            cy + h * 0.15,
            title,
            ha="center",
            va="center",
            fontsize=8.5,
            fontweight="bold",
            zorder=4,
        )
        ax.text(
            cx,
            cy - h * 0.22,
            subtitle,
            ha="center",
            va="center",
            fontsize=7,
            color="#374151",
            style="italic",
            zorder=4,
        )
    else:
        ax.text(
            cx,
            cy,
            title,
            ha="center",
            va="center",
            fontsize=8.5,
            fontweight="bold",
            zorder=4,
        )


def _arrow(
    ax,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    label: str = "",
    color: str = _C_ARROW,
    rad: float = 0.0,
    lw: float = 1.1,
    dashed: bool = False,
    shrink: int = 10,
) -> None:
    """Draw a dependency arrow with optional mid-point label."""
    ax.annotate(
        "",
        xy=(x2, y2),
        xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle="->",
            color=color,
            connectionstyle=f"arc3,rad={rad}",
            lw=lw,
            linestyle="dashed" if dashed else "solid",
            shrinkA=shrink,
            shrinkB=shrink,
        ),
        zorder=2,
    )
    if label:
        # Offset label perpendicular to the arc
        mx = (x1 + x2) / 2 + rad * (y2 - y1) * 0.3
        my = (y1 + y2) / 2 - rad * (x2 - x1) * 0.3
        ax.text(
            mx,
            my,
            label,
            ha="center",
            va="center",
            fontsize=6.5,
            color=color,
            zorder=5,
            bbox=dict(fc="white", ec="none", pad=1.5),
        )


# ---------------------------------------------------------------------------
# Diagram: Snitch component diagram
# ---------------------------------------------------------------------------


def diagram_snitch_components() -> None:
    fig, ax = plt.subplots(figsize=(13, 8.5))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 8.5)
    ax.set_aspect("equal")
    ax.axis("off")

    # Package boundary
    ax.add_patch(
        FancyBboxPatch(
            (1.8, 0.6),
            9.4,
            6.8,
            boxstyle="round,pad=0.1",
            facecolor=_GRAY["fc"],
            edgecolor=_GRAY["ec"],
            linewidth=_GRAY["lw"],
            linestyle=_GRAY["ls"],
            zorder=1,
        )
    )
    ax.text(
        2.1,
        7.28,
        "«package»  snitch",
        fontsize=8,
        color="#64748b",
        style="italic",
        zorder=4,
    )

    # ── External entities ────────────────────────────────────────────────────

    _box(
        ax,
        6.5,
        8.05,
        2.8,
        0.75,
        "run_snitch.py",
        "CLI entry point",
        style=_YELLOW,
    )

    _box(ax, 12.2, 5.5, 1.8, 0.75, "Ollama", "LLM server", style=_YELLOW)

    _box(ax, 0.85, 2.0, 1.6, 0.75, "Source", "target directory", style=_YELLOW)

    _box(ax, 12.2, 2.5, 1.8, 0.75, "Output", "results files", style=_YELLOW)

    # ── Internal components ──────────────────────────────────────────────────

    _box(ax, 6.5, 5.7, 3.0, 1.1, "sast_agent", "SastAgent · run() · analyze()")

    _box(
        ax, 3.5, 5.7, 2.4, 1.1, "prompts", "LLM_SAST_PROMPT\nLLM_USER_TEMPLATE"
    )

    _box(ax, 3.8, 3.7, 2.4, 1.0, "repo_io", "RepositoryIO · read_repository()")

    _box(ax, 6.6, 3.4, 2.4, 1.0, "models", "SastResult · SourceCodeFile")

    _box(
        ax,
        9.3,
        3.7,
        2.4,
        1.0,
        "output",
        "write_json / write_csv\nwrite_text · write_output()",
    )

    _box(
        ax,
        3.8,
        1.8,
        2.4,
        1.0,
        "file_utils",
        "read_sourcecode()\nread_all_from_folder()",
    )

    # ── Dependency arrows ────────────────────────────────────────────────────

    # run_snitch.py → sast_agent
    _arrow(ax, 6.5, 8.05, 6.5, 5.7)

    # run_snitch.py → repo_io (curved left to avoid sast_agent)
    _arrow(ax, 6.5, 8.05, 3.8, 3.7, rad=0.25)

    # run_snitch.py → output (curved right)
    _arrow(ax, 6.5, 8.05, 9.3, 3.7, rad=-0.25)

    # sast_agent → prompts
    _arrow(ax, 6.5, 5.7, 3.5, 5.7)

    # sast_agent → repo_io
    _arrow(ax, 6.5, 5.7, 3.8, 3.7, rad=0.15)

    # sast_agent → models
    _arrow(ax, 6.5, 5.7, 6.6, 3.4)

    # sast_agent → Ollama (HTTP, dashed)
    _arrow(
        ax,
        6.5,
        5.7,
        12.2,
        5.5,
        label="HTTP POST",
        color=_C_HTTP,
        dashed=True,
        shrink=12,
    )

    # repo_io → file_utils
    _arrow(ax, 3.8, 3.7, 3.8, 1.8)

    # repo_io → models (SourceCodeFile)
    _arrow(ax, 3.8, 3.7, 6.6, 3.4, rad=0.15)

    # output → models (reads SastResult)
    _arrow(ax, 9.3, 3.7, 6.6, 3.4, rad=-0.12)

    # file_utils → Source files
    _arrow(ax, 3.8, 1.8, 0.85, 2.0, rad=0.1)

    # output → Output files
    _arrow(ax, 9.3, 3.7, 12.2, 2.5, rad=-0.1)

    # ── Legend ───────────────────────────────────────────────────────────────

    ax.legend(
        handles=[
            mpatches.Patch(
                fc=_BLUE["fc"],
                ec=_BLUE["ec"],
                lw=1.5,
                label="snitch module",
            ),
            mpatches.Patch(
                fc=_YELLOW["fc"],
                ec=_YELLOW["ec"],
                lw=1.5,
                label="external entity",
            ),
            mpatches.Patch(
                fc=_GRAY["fc"],
                ec=_GRAY["ec"],
                lw=1.2,
                ls="dashed",
                label="package boundary",
            ),
        ],
        loc="lower right",
        fontsize=7.5,
        framealpha=0.9,
    )

    # ax.set_title(
    #     "Snitch — Component Diagram",
    #     fontsize=12, fontweight="bold", pad=10,
    # )

    _save(fig, "snitch_components", {"diagram": "snitch-components"})


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

DIAGRAMS = {
    "snitch-components": diagram_snitch_components,
}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="generate_diagrams",
        description="Generate PDF diagrams for the LaTeX paper.",
    )
    p.add_argument(
        "--diagram",
        choices=list(DIAGRAMS.keys()) + ["all"],
        default="all",
        help="Which diagram to generate (default: all)",
    )
    return p


def main() -> None:
    args = build_parser().parse_args()
    targets = (
        list(DIAGRAMS.values())
        if args.diagram == "all"
        else [DIAGRAMS[args.diagram]]
    )
    for fn in targets:
        fn()


if __name__ == "__main__":
    main()
