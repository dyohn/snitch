#!/usr/bin/env python3
"""analyze_results.py — Two-pass SAST experiment results analyzer.

Pass 1:  python analyze_results.py --pass 1
Pass 2:  python analyze_results.py --pass 2 \\
             --annotations analysis/review_annotations.json
Replot:  python analyze_results.py --replot <figure_name>
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPOS = ["beaverhabits", "fail2ban", "yum"]
MODELS = ["gemma3", "llama3.1", "qwen2.5"]
ANALYSIS_DIR = Path("analysis")

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_bandit(repo: str) -> dict:
    path = Path(f"results_bandit/bandit_{repo}.json")
    return json.loads(path.read_text(encoding="utf-8"))


def load_snitch(repo: str, model: str) -> list[dict]:
    path = Path(f"output_{repo}_{model}/snitch_results.json")
    return json.loads(path.read_text(encoding="utf-8"))


def is_skipped(entry: dict) -> bool:
    return all(
        entry.get(k) == "skipped"
        for k in ("where", "what", "why", "fix")
    )


# ---------------------------------------------------------------------------
# False positive / hallucination classification
# ---------------------------------------------------------------------------

_WHERE_FILE_LINE = re.compile(
    r"[\w./\\-]+\.py:\d+", re.IGNORECASE
)

_EGREGIOUS_WHAT_KEYWORDS = frozenset([
    "css", "stylesheet", "comment", "docstring",
    "license", "copyright", "html tag",
])

_STDLIB_RE = re.compile(
    r"\b("
    r"calendar\.\w+"
    r"|os\.path|os\.sep|os\.linesep|os\.devnull"
    r"|sys\.argv"
    r"|string\.ascii\w*"
    r")\b",
    re.IGNORECASE,
)


def classify_fp(entry: dict) -> str | None:
    """Return 'egregious', 'minor', or None (not a FP)."""
    where = entry.get("where", "")
    what = entry.get("what", "").lower()
    why = entry.get("why", "")

    # Stdlib constant flagged as a vulnerability
    if _STDLIB_RE.search(what) or _STDLIB_RE.search(why):
        return "egregious"

    # Non-code artifact (CSS, comment, license, etc.)
    if any(kw in what for kw in _EGREGIOUS_WHAT_KEYWORDS):
        return "egregious"

    # Suspiciously short explanation — likely a hallucination
    if len(why.strip()) < 20:
        return "minor"

    # Where field carries no file:line reference
    if not _WHERE_FILE_LINE.search(where):
        return "minor"

    return None


# ---------------------------------------------------------------------------
# Issue categorisation
# ---------------------------------------------------------------------------

_SNITCH_CATEGORIES = {
    "injection": [
        "sql", "injection", "command", "shell", "exec",
        "xss", "cross-site", "template",
    ],
    "authentication": [
        "auth", "password", "credential", "secret",
        "token", "hardcode", "api key",
    ],
    "cryptography": [
        "crypto", "cipher", "hash", "random", "md5",
        "sha1", "weak", "entropy", "tls", "ssl",
        "hashlib",
    ],
    "subprocess/OS": [
        "subprocess", "popen", "os.system",
        "shell=true", "process", "command execution",
    ],
    "path traversal": [
        "path", "traversal", "directory",
        "file inclusion", "lfi", "rfi",
    ],
    "info disclosure": [
        "disclosure", "leak", "expose",
        "sensitive", "logging", "stack trace",
    ],
}

SNITCH_CATS = list(_SNITCH_CATEGORIES.keys()) + ["other"]


def categorise_snitch(what: str) -> str:
    w = what.lower()
    for cat, keywords in _SNITCH_CATEGORIES.items():
        if any(kw in w for kw in keywords):
            return cat
    return "other"


# Mapping relevant to the test_ids actually present in the data:
# beaverhabits M/H: B104 B113 B324 B701
# fail2ban M/H:     B104 B108 B113 B301 B306 B307 B602 B604 B605 B608
_BANDIT_CATEGORY: dict[str, str] = {
    "B104": "network",           # bind all interfaces
    "B108": "path/file",         # hardcoded tmp directory
    "B113": "other",             # request without timeout
    "B301": "deserialization",   # pickle
    "B306": "path/file",         # mktemp
    "B307": "injection",         # eval
    "B324": "cryptography",      # hashlib insecure
    "B602": "subprocess/OS",     # popen shell=True
    "B604": "subprocess/OS",     # shell=True (any func)
    "B605": "subprocess/OS",     # start_process with shell
    "B608": "injection",         # hardcoded SQL
    "B701": "injection",         # jinja2 autoescape=False
}

BANDIT_CATS = [
    "injection", "subprocess/OS", "cryptography",
    "deserialization", "path/file", "network", "other",
]


def categorise_bandit(test_id: str) -> str:
    return _BANDIT_CATEGORY.get(test_id, "other")


# ---------------------------------------------------------------------------
# LaTeX helpers
# ---------------------------------------------------------------------------


def latex_tabular(
    headers: list[str], rows: list[list]
) -> str:
    col_spec = "l" + "r" * (len(headers) - 1)
    lines = [
        rf"\begin{{tabular}}{{{col_spec}}}",
        r"\hline",
        " & ".join(headers) + r" \\",
        r"\hline",
    ]
    for row in rows:
        lines.append(
            " & ".join(str(c) for c in row) + r" \\"
        )
    lines += [r"\hline", r"\end{tabular}"]
    return "\n".join(lines)


def write_tex(
    path: Path,
    tabular: str,
    caption: str,
    label: str,
) -> None:
    content = "\n".join([
        r"\begin{table}[htbp]",
        r"\centering",
        tabular,
        rf"\caption{{{caption}}}",
        rf"\label{{tab:{label}}}",
        r"\end{table}",
        "",
    ])
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Figure persistence helpers
# ---------------------------------------------------------------------------


def _save_fig(
    fig: plt.Figure, name: str, data: dict
) -> None:
    """Save figure as PDF and persist its source data."""
    pdf = ANALYSIS_DIR / f"{name}.pdf"
    djson = ANALYSIS_DIR / f"{name}_data.json"
    fig.savefig(str(pdf), format="pdf", bbox_inches="tight")
    plt.close(fig)
    djson.write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )
    print(f"  {pdf.name}  +  {djson.name}")


def _load_fig_data(name: str) -> dict:
    p = ANALYSIS_DIR / f"{name}_data.json"
    return json.loads(p.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Plot functions (each self-contained; readable from saved data)
# ---------------------------------------------------------------------------


def plot_bandit_categories(data: dict) -> None:
    """Stacked bar: Bandit MEDIUM/HIGH categories per repo."""
    repos = data["repos"]
    cats = data["categories"]
    counts = data["counts"]  # {cat: [count_per_repo]}

    x = list(range(len(repos)))
    fig, ax = plt.subplots(figsize=(7, 4))
    bottom = [0] * len(repos)
    for cat in cats:
        vals = counts[cat]
        ax.bar(x, vals, 0.5, label=cat, bottom=bottom)
        bottom = [b + v for b, v in zip(bottom, vals)]

    ax.set_xticks(x)
    ax.set_xticklabels([r.capitalize() for r in repos])
    ax.set_ylabel("Finding count")
    ax.set_title("Bandit MEDIUM/HIGH Findings by Category")
    ax.legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    _save_fig(fig, "bandit_categories", data)


def plot_snitch_categories(data: dict) -> None:
    """Grouped bar: Snitch issue categories per model."""
    repo = data["repo"]
    cats = data["categories"]
    models = data["models"]
    counts = data["counts"]  # {model: [count_per_cat]}

    x = list(range(len(cats)))
    n = len(models)
    width = 0.22
    fig, ax = plt.subplots(figsize=(9, 4))
    for i, model in enumerate(models):
        offset = (i - n / 2 + 0.5) * width
        ax.bar(
            [xi + offset for xi in x],
            counts[model],
            width,
            label=model,
        )
    ax.set_xticks(x)
    ax.set_xticklabels(cats, rotation=20, ha="right")
    ax.set_ylabel("Finding count")
    ax.set_title(
        f"Snitch Issue Categories — {repo.capitalize()}"
    )
    ax.legend()
    fig.tight_layout()
    _save_fig(fig, f"snitch_categories_{repo}", data)


def plot_composite_scores(data: dict) -> None:
    """Grouped bar: recall / FP rate / composite per model."""
    repos = data["repos"]
    models = data["models"]
    scores = data["scores"]

    metrics = ["recall", "fp_rate", "composite"]
    labels = ["Recall", "FP Rate", "Composite"]
    colors = ["#4c72b0", "#dd8452", "#55a868"]

    n_repos = len(repos)
    fig, axes = plt.subplots(
        1, n_repos, figsize=(4 * n_repos, 4), sharey=True
    )
    if n_repos == 1:
        axes = [axes]

    for ax, repo in zip(axes, repos):
        x = list(range(len(models)))
        width = 0.22
        for j, (metric, label, color) in enumerate(
            zip(metrics, labels, colors)
        ):
            offset = (j - 1) * width
            vals = [
                scores[repo][m][metric] for m in models
            ]
            ax.bar(
                [xi + offset for xi in x],
                vals,
                width,
                label=label,
                color=color,
            )
        ax.set_title(repo.capitalize())
        ax.set_xticks(x)
        ax.set_xticklabels(
            models, rotation=15, ha="right", fontsize=8
        )
        ax.set_ylim(-1.05, 1.05)
        ax.axhline(0, color="black", linewidth=0.6)

    axes[0].set_ylabel("Score")
    handles, lbls = axes[0].get_legend_handles_labels()
    fig.legend(
        handles, lbls, loc="upper right", fontsize=8
    )
    fig.suptitle("Composite Scores by Repository and LLM")
    fig.tight_layout()
    _save_fig(fig, "composite_scores", data)


# ---------------------------------------------------------------------------
# Pass 1
# ---------------------------------------------------------------------------


def run_pass1() -> None:
    ANALYSIS_DIR.mkdir(exist_ok=True)
    print("=== Pass 1: Analysing results ===\n")

    # --- A. Bandit analysis -------------------------------------------------
    print("A. Bandit — severity counts")
    bandit_all = {repo: load_bandit(repo) for repo in REPOS}

    sev_rows = []
    for repo in REPOS:
        counts: dict[str, int] = defaultdict(int)
        for r in bandit_all[repo]["results"]:
            counts[r["issue_severity"]] += 1
        sev_rows.append([
            repo.capitalize(),
            counts["LOW"],
            counts["MEDIUM"],
            counts["HIGH"],
            counts["LOW"] + counts["MEDIUM"] + counts["HIGH"],
        ])

    write_tex(
        ANALYSIS_DIR / "bandit_severity_table.tex",
        latex_tabular(
            ["Repository", "LOW", "MEDIUM", "HIGH", "TOTAL"],
            sev_rows,
        ),
        caption=(
            "Bandit findings by severity per repository"
        ),
        label="bandit_severity",
    )
    print("  bandit_severity_table.tex")

    print("A. Bandit — MEDIUM/HIGH category breakdown")
    cat_counts: dict[str, dict[str, int]] = {
        repo: defaultdict(int) for repo in REPOS
    }
    for repo in REPOS:
        for r in bandit_all[repo]["results"]:
            if r["issue_severity"] in ("MEDIUM", "HIGH"):
                cat = categorise_bandit(r["test_id"])
                cat_counts[repo][cat] += 1

    cat_rows = [
        [cat] + [cat_counts[repo][cat] for repo in REPOS]
        for cat in BANDIT_CATS
        if any(cat_counts[repo][cat] for repo in REPOS)
    ]

    write_tex(
        ANALYSIS_DIR / "bandit_medium_high_categories.tex",
        latex_tabular(
            ["Category"] + [r.capitalize() for r in REPOS],
            cat_rows,
        ),
        caption=(
            "Bandit MEDIUM/HIGH findings grouped by category"
        ),
        label="bandit_mh_categories",
    )
    print("  bandit_medium_high_categories.tex")

    present_cats = [row[0] for row in cat_rows]
    plot_bandit_categories({
        "repos": REPOS,
        "categories": present_cats,
        "counts": {
            cat: [cat_counts[repo][cat] for repo in REPOS]
            for cat in present_cats
        },
    })

    # --- B. Snitch findings counts -----------------------------------------
    print("\nB. Snitch — findings counts")
    snitch_all: dict[str, dict[str, list[dict]]] = {
        repo: {
            model: load_snitch(repo, model)
            for model in MODELS
        }
        for repo in REPOS
    }

    find_rows = []
    for repo in REPOS:
        row: list = [repo.capitalize()]
        for model in MODELS:
            entries = snitch_all[repo][model]
            skipped = sum(
                1 for e in entries if is_skipped(e)
            )
            row += [len(entries), skipped, len(entries) - skipped]
        find_rows.append(row)

    model_hdrs = [
        f"{m}/{lbl}"
        for m in MODELS
        for lbl in ("total", "skip", "found")
    ]
    write_tex(
        ANALYSIS_DIR / "snitch_findings_table.tex",
        latex_tabular(["Repository"] + model_hdrs, find_rows),
        caption=(
            "Snitch findings per repository and LLM "
            "(total / skipped / actual)"
        ),
        label="snitch_findings",
    )
    print("  snitch_findings_table.tex")

    # --- C. FP / hallucination flagging ------------------------------------
    print("\nC. False positive / hallucination flagging")
    fp_data: dict[str, dict[str, dict]] = {}

    for repo in REPOS:
        fp_data[repo] = {}
        for model in MODELS:
            actual = [
                e for e in snitch_all[repo][model]
                if not is_skipped(e)
            ]
            eg, minor = [], []
            for e in actual:
                v = classify_fp(e)
                if v == "egregious":
                    eg.append(e)
                elif v == "minor":
                    minor.append(e)

            fp_data[repo][model] = {
                "actual": len(actual),
                "egregious": len(eg),
                "minor": len(minor),
                "total": len(eg) + len(minor),
            }

            flagged_path = (
                ANALYSIS_DIR / f"flagged_{repo}_{model}.txt"
            )
            lines = [
                f"Flagged FP/Hallucinations: "
                f"{repo} / {model}",
                "=" * 60, "",
            ]
            for severity, items in (
                ("EGREGIOUS", eg), ("MINOR", minor)
            ):
                if items:
                    lines.append(f"--- {severity} ---")
                    for e in items:
                        lines += [
                            f"  where: {e.get('where','')}",
                            f"  what:  {e.get('what', '')}",
                            f"  why:   {e.get('why', '')}",
                            "",
                        ]
            flagged_path.write_text(
                "\n".join(lines), encoding="utf-8"
            )

    fp_rows = []
    for repo in REPOS:
        row = [repo.capitalize()]
        for model in MODELS:
            d = fp_data[repo][model]
            rate = (
                f"{d['total'] / d['actual']:.0%}"
                if d["actual"] > 0 else "N/A"
            )
            row += [d["total"], rate]
        fp_rows.append(row)

    fp_hdrs = ["Repository"] + [
        f"{m}/{lbl}"
        for m in MODELS
        for lbl in ("flagged", "rate")
    ]
    write_tex(
        ANALYSIS_DIR / "snitch_fp_table.tex",
        latex_tabular(fp_hdrs, fp_rows),
        caption=(
            r"Snitch likely false positives per repository "
            r"and LLM (count and rate as \% of actual findings)"
        ),
        label="snitch_fp",
    )
    print(
        "  snitch_fp_table.tex  +  "
        "flagged_{repo}_{model}.txt files"
    )

    # --- D. Snitch issue categories ----------------------------------------
    print("\nD. Snitch issue category analysis")
    for repo in REPOS:
        cat_by_model: dict[str, list[int]] = {}
        for model in MODELS:
            actual = [
                e for e in snitch_all[repo][model]
                if not is_skipped(e)
                and classify_fp(e) != "egregious"
            ]
            c: dict[str, int] = defaultdict(int)
            for e in actual:
                c[categorise_snitch(e.get("what", ""))] += 1
            cat_by_model[model] = [c[cat] for cat in SNITCH_CATS]

        plot_snitch_categories({
            "repo": repo,
            "categories": SNITCH_CATS,
            "models": MODELS,
            "counts": cat_by_model,
        })

    # --- E. Side-by-side review listings -----------------------------------
    print("\nE. Generating review listings")
    annotations: dict[str, list] = {}

    for repo in REPOS:
        bandit_mh = [
            r for r in bandit_all[repo]["results"]
            if r["issue_severity"] in ("MEDIUM", "HIGH")
        ]

        # Index Snitch non-skipped by basename
        idx: dict[str, dict[str, list[dict]]] = {
            model: defaultdict(list) for model in MODELS
        }
        for model in MODELS:
            for e in snitch_all[repo][model]:
                if not is_skipped(e):
                    key = e["filename"].lower()
                    idx[model][key].append(e)

        review_lines = [
            f"Bandit MEDIUM/HIGH vs Snitch — {repo}",
            "=" * 72, "",
        ]
        ann_entries = []

        for i, finding in enumerate(bandit_mh):
            fname = Path(finding["filename"]).name
            review_lines += [
                f"[{i}] {finding['test_id']} | "
                f"{finding['issue_severity']} | "
                f"{fname}:{finding['line_number']}",
                f"    {finding['issue_text']}",
                "",
            ]
            for model in MODELS:
                matches = idx[model].get(fname.lower(), [])
                review_lines.append(f"  [{model}]")
                if matches:
                    for m in matches:
                        review_lines += [
                            f"    where: {m['where']}",
                            f"    what:  {m['what']}",
                        ]
                else:
                    review_lines.append(
                        "    (no findings in this file)"
                    )
                review_lines.append("")
            review_lines += ["-" * 72, ""]

            ann_entries.append({
                "bandit_id": i,
                "test_id": finding["test_id"],
                "test_name": finding.get("test_name", ""),
                "filename": fname,
                "line_number": finding["line_number"],
                "severity": finding["issue_severity"],
                "issue_text": finding["issue_text"],
                "found_by": {m: None for m in MODELS},
            })

        (ANALYSIS_DIR / f"review_{repo}.txt").write_text(
            "\n".join(review_lines), encoding="utf-8"
        )
        annotations[repo] = ann_entries

    (ANALYSIS_DIR / "review_annotations.json").write_text(
        json.dumps(annotations, indent=2), encoding="utf-8"
    )
    print("  review_{repo}.txt  +  review_annotations.json")

    print("\nPass 1 complete.")
    print(
        "\nNext steps:\n"
        "  1. Review analysis/review_{repo}.txt\n"
        "  2. Fill in analysis/review_annotations.json "
        "(replace null with true / false / \"partial\")\n"
        "  3. python analyze_results.py --pass 2 "
        "--annotations analysis/review_annotations.json"
    )


# ---------------------------------------------------------------------------
# Pass 2
# ---------------------------------------------------------------------------


def run_pass2(annotations_path: Path) -> None:
    ANALYSIS_DIR.mkdir(exist_ok=True)
    print("=== Pass 2: Computing composite scores ===\n")

    if not annotations_path.exists():
        print(
            f"Error: {annotations_path} not found.",
            file=sys.stderr,
        )
        sys.exit(1)

    annotations: dict[str, list] = json.loads(
        annotations_path.read_text(encoding="utf-8")
    )

    # Warn on unannotated entries
    nulls = [
        f"{repo}[{e['bandit_id']}]"
        for repo, entries in annotations.items()
        for e in entries
        if any(v is None for v in e["found_by"].values())
    ]
    if nulls:
        print(
            f"Warning: {len(nulls)} unannotated entries "
            "(null treated as false).",
            file=sys.stderr,
        )

    # Re-derive FP counts from raw data
    fp_counts: dict[str, dict[str, dict]] = {}
    for repo in REPOS:
        fp_counts[repo] = {}
        for model in MODELS:
            entries = load_snitch(repo, model)
            actual = [e for e in entries if not is_skipped(e)]
            flagged = sum(
                1 for e in actual
                if classify_fp(e) is not None
            )
            fp_counts[repo][model] = {
                "actual": len(actual),
                "flagged": flagged,
            }

    scores: dict[str, dict[str, dict]] = {}
    score_rows = []

    for repo in REPOS:
        scores[repo] = {}
        entries = annotations.get(repo, [])
        total_mh = len(entries)

        row: list = [repo.capitalize()]
        for model in MODELS:
            found = sum(
                1 for e in entries
                if e["found_by"].get(model) is True
            )
            partial = sum(
                0.5 for e in entries
                if e["found_by"].get(model) == "partial"
            )
            recall = (
                (found + partial) / total_mh
                if total_mh > 0 else 0.0
            )
            d = fp_counts[repo][model]
            fp_rate = (
                d["flagged"] / d["actual"]
                if d["actual"] > 0 else 0.0
            )
            composite = recall - fp_rate

            scores[repo][model] = {
                "recall": round(recall, 3),
                "fp_rate": round(fp_rate, 3),
                "composite": round(composite, 3),
            }
            row += [
                f"{recall:.2f}",
                f"{fp_rate:.2f}",
                f"{composite:.2f}",
            ]
        score_rows.append(row)

    # Bold best composite per repo
    bold_rows = []
    for i, repo in enumerate(REPOS):
        composites = [
            scores[repo][m]["composite"] for m in MODELS
        ]
        best_i = composites.index(max(composites))
        row = list(score_rows[i])
        # composite col index: 1 + best_i*3 + 2
        col = 1 + best_i * 3 + 2
        row[col] = rf"\textbf{{{row[col]}}}"
        bold_rows.append(row)

    model_hdrs = [
        f"{m}/{lbl}"
        for m in MODELS
        for lbl in ("recall", "FP rate", "composite")
    ]
    write_tex(
        ANALYSIS_DIR / "composite_scores_table.tex",
        latex_tabular(["Repository"] + model_hdrs, bold_rows),
        caption=(
            r"Composite scores per repository and LLM "
            r"(recall $-$ FP rate; best per repo in bold)"
        ),
        label="composite_scores",
    )
    print("  composite_scores_table.tex")

    plot_composite_scores({
        "repos": REPOS,
        "models": MODELS,
        "scores": scores,
    })

    # Missed by ALL models
    missed_rows = []
    for repo in REPOS:
        for e in annotations.get(repo, []):
            if all(
                e["found_by"].get(m) in (False, None)
                for m in MODELS
            ):
                missed_rows.append([
                    repo.capitalize(),
                    e["test_id"],
                    e["filename"],
                    e["line_number"],
                    e["severity"],
                    (e["issue_text"][:55] + "...")
                    if len(e["issue_text"]) > 55
                    else e["issue_text"],
                ])

    write_tex(
        ANALYSIS_DIR / "missed_bandit_issues.tex",
        latex_tabular(
            [
                "Repo", "Test ID", "File",
                "Line", "Sev.", "Issue (truncated)",
            ],
            missed_rows,
        ),
        caption=(
            "Bandit MEDIUM/HIGH issues not found by "
            "any Snitch LLM scan"
        ),
        label="missed_bandit",
    )
    print("  missed_bandit_issues.tex")

    print("\n=== Summary ===")
    for repo in REPOS:
        best = max(
            MODELS, key=lambda m: scores[repo][m]["composite"]
        )
        s = scores[repo][best]
        print(
            f"  {repo.capitalize():<15s} best: {best:<12s}"
            f"recall={s['recall']:.2f}  "
            f"FP rate={s['fp_rate']:.2f}  "
            f"composite={s['composite']:.2f}"
        )
    print(
        f"\n  Missed by all LLMs: {len(missed_rows)} finding(s)"
    )
    print("\nPass 2 complete.")


# ---------------------------------------------------------------------------
# Replot
# ---------------------------------------------------------------------------


def run_replot(name: str) -> None:
    ANALYSIS_DIR.mkdir(exist_ok=True)
    if name.startswith("snitch_categories_"):
        plot_snitch_categories(_load_fig_data(name))
    elif name == "bandit_categories":
        plot_bandit_categories(_load_fig_data(name))
    elif name == "composite_scores":
        plot_composite_scores(_load_fig_data(name))
    else:
        print(
            f"Unknown figure: {name}\n"
            "Available: bandit_categories, composite_scores, "
            "snitch_categories_<repo>",
            file=sys.stderr,
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="analyze_results",
        description=(
            "Two-pass SAST experiment results analyser. "
            "Run --pass 1 first, annotate, then --pass 2."
        ),
    )
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--pass",
        dest="run_pass",
        type=int,
        choices=[1, 2],
        metavar="N",
        help="Run analysis pass 1 or 2",
    )
    group.add_argument(
        "--replot",
        metavar="FIGURE",
        help=(
            "Regenerate a single PDF from its saved "
            "_data.json (e.g., bandit_categories)"
        ),
    )
    p.add_argument(
        "--annotations",
        type=Path,
        default=Path("analysis/review_annotations.json"),
        help="Annotated JSON file (required for --pass 2)",
    )
    return p


def main() -> None:
    args = build_parser().parse_args()
    if args.replot:
        run_replot(args.replot)
    elif args.run_pass == 1:
        run_pass1()
    else:
        run_pass2(args.annotations)


if __name__ == "__main__":
    main()
