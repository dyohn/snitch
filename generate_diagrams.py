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

_BLUE = dict(fc="#dbeafe", ec="#1d4ed8", lw=1.8)    # snitch module
_YELLOW = dict(fc="#fef9c3", ec="#b45309", lw=1.8)  # external / human
_GRAY = dict(fc="#f1f5f9", ec="#64748b", lw=1.5, ls="--")  # boundary
_GREEN = dict(fc="#dcfce7", ec="#166534", lw=1.8)   # output metric
_PURPLE = dict(fc="#ede9fe", ec="#6d28d9", lw=1.8)  # Bandit baseline

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
# Diagram: Experimental pipeline overview
# ---------------------------------------------------------------------------


def diagram_experimental_pipeline() -> None:
    fig, ax = plt.subplots(figsize=(8.5, 11))
    ax.set_xlim(0, 8.5)
    ax.set_ylim(0, 11)
    ax.set_aspect("auto")
    ax.axis("off")

    C_LN = _C_ARROW
    LW = 1.4

    # ── Target repositories ──────────────────────────────────────────────────

    repos = [("Beaverhabits", 1.5), ("Fail2ban", 4.25), ("Yum", 7.0)]
    for name, cx in repos:
        _box(ax, cx, 10.2, 1.8, 0.6, name, style=_YELLOW)

    # ── Bus bar and fork to parallel scan tracks ─────────────────────────────

    Y_REPO_BOT = 9.9    # repo center 10.2 − h/2 0.3
    Y_BUS = 9.55
    Y_FORK = 9.0
    CX_BANDIT = 2.0
    CX_SNITCH = 5.75    # center of Snitch boundary

    for cx in [r[1] for r in repos]:
        ax.plot([cx, cx], [Y_REPO_BOT, Y_BUS], color=C_LN, lw=LW, zorder=2)
    ax.plot([1.5, 7.0], [Y_BUS, Y_BUS], color=C_LN, lw=LW, zorder=2)
    ax.plot([4.25, 4.25], [Y_BUS, Y_FORK], color=C_LN, lw=LW, zorder=2)
    ax.plot(
        [CX_BANDIT, CX_SNITCH], [Y_FORK, Y_FORK], color=C_LN, lw=LW, zorder=2
    )

    # ── Parallel scan tracks ─────────────────────────────────────────────────

    Y_SCAN = 7.85

    # Left track — Bandit
    _box(ax, CX_BANDIT, Y_SCAN, 2.2, 0.75,
         "Bandit", "Baseline SAST Tool", style=_PURPLE)
    ax.annotate(
        "", xy=(CX_BANDIT, Y_SCAN + 0.375 + 0.04), xytext=(CX_BANDIT, Y_FORK),
        arrowprops=dict(arrowstyle="->", color=C_LN, lw=LW,
                        shrinkA=0, shrinkB=0),
        zorder=2,
    )

    # Right track — Snitch (three model sub-tracks)
    SN_LEFT, SN_W = 3.5, 4.5
    SN_BOT, SN_H = 7.35, 1.1
    ax.add_patch(FancyBboxPatch(
        (SN_LEFT, SN_BOT), SN_W, SN_H,
        boxstyle="round,pad=0.04",
        facecolor=_GRAY["fc"],
        edgecolor=_GRAY["ec"],
        linewidth=_GRAY["lw"],
        linestyle=_GRAY["ls"],
        zorder=1, clip_on=False,
    ))
    ax.text(
        SN_LEFT + 0.15, SN_BOT + SN_H - 0.07,
        "«scanner»  Snitch",
        fontsize=7.5, color="#64748b", style="italic", zorder=4, va="top",
    )
    for label, cx in [("gemma3", 4.3), ("llama3.1", 5.75), ("qwen2.5", 7.2)]:
        _box(ax, cx, Y_SCAN - 0.05, 1.1, 0.58, label, style=_BLUE)

    ax.annotate(
        "", xy=(CX_SNITCH, SN_BOT + SN_H + 0.04), xytext=(CX_SNITCH, Y_FORK),
        arrowprops=dict(arrowstyle="->", color=C_LN, lw=LW,
                        shrinkA=0, shrinkB=0),
        zorder=2,
    )

    # ── Pass 1: generate review listings ────────────────────────────────────

    Y_P1 = 5.7
    _box(ax, 4.25, Y_P1, 5.5, 0.85,
         "Pass 1",
         "Generate Review Listings & Annotation Template",
         style=_BLUE)

    # Bandit → Pass 1 (arcs left, away from Snitch region)
    _arrow(ax, CX_BANDIT, Y_SCAN, 4.25, Y_P1, rad=-0.3)
    # Snitch boundary bottom → Pass 1
    ax.annotate(
        "", xy=(4.25, Y_P1), xytext=(CX_SNITCH, SN_BOT - 0.04),
        arrowprops=dict(arrowstyle="->", color=C_LN, lw=LW,
                        connectionstyle="arc3,rad=0.2",
                        shrinkA=0, shrinkB=10),
        zorder=2,
    )

    # ── Manual annotation (human step) ───────────────────────────────────────

    Y_MAN = 4.2
    _box(ax, 4.25, Y_MAN, 4.2, 0.72,
         "Manual Annotation",
         "Analyst reviews side-by-side listings",
         style=_YELLOW)
    _arrow(ax, 4.25, Y_P1, 4.25, Y_MAN)

    # ── Pass 2: score computation ─────────────────────────────────────────────

    Y_P2 = 2.85
    _box(ax, 4.25, Y_P2, 5.5, 0.85,
         "Pass 2",
         "Cross-Reference & Score Computation",
         style=_BLUE)
    _arrow(ax, 4.25, Y_MAN, 4.25, Y_P2)

    # ── Output metrics ───────────────────────────────────────────────────────

    Y_MET = 1.5
    for label, cx in [("Recall", 1.8), ("FP Rate", 4.25), ("Composite Score", 6.7)]:
        _box(ax, cx, Y_MET, 2.0, 0.65, label, style=_GREEN)

    _arrow(ax, 4.25, Y_P2, 1.8, Y_MET, rad=0.25)
    _arrow(ax, 4.25, Y_P2, 4.25, Y_MET)
    _arrow(ax, 4.25, Y_P2, 6.7, Y_MET, rad=-0.25)

    # ── Legend ───────────────────────────────────────────────────────────────

    ax.legend(
        handles=[
            mpatches.Patch(
                fc=_YELLOW["fc"], ec=_YELLOW["ec"],
                lw=1.5, label="External / Human Step",
            ),
            mpatches.Patch(
                fc=_PURPLE["fc"], ec=_PURPLE["ec"],
                lw=1.5, label="Bandit (Baseline SAST)",
            ),
            mpatches.Patch(
                fc=_BLUE["fc"], ec=_BLUE["ec"],
                lw=1.5, label="Automated Stage",
            ),
            mpatches.Patch(
                fc=_GREEN["fc"], ec=_GREEN["ec"],
                lw=1.5, label="Output Metric",
            ),
        ],
        loc="lower right",
        fontsize=7.5,
        framealpha=0.9,
    )

    ax.set_title(
        "Experimental Pipeline Overview",
        fontsize=13, fontweight="bold", pad=12,
    )

    _save(fig, "experimental_pipeline", {
        "repos": [r[0] for r in repos],
        "models": ["gemma3", "llama3.1", "qwen2.5"],
    })


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

DIAGRAMS = {
    "snitch-components": diagram_snitch_components,
    "experimental-pipeline": diagram_experimental_pipeline,
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
