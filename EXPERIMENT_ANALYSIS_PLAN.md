# Experiment Results Analysis Plan

## Context

Three Python repositories (beaverhabits, fail2ban, yum) were scanned by both Bandit (baseline SAST tool) and Snitch (LLM-based scanner using gemma3, llama3.1, qwen2.5 — 9 total Snitch scans). The goal is to analyze both sets of results, quantify findings, flag false positives and hallucinations, produce side-by-side listings for manual Bandit↔Snitch comparison, and — after manual annotation — compute a composite recall-minus-FP-rate score to identify the best-performing LLM per repository.

**Count discrepancy note:** RESULTS_README.md shows higher file counts than the JSON files contain because Snitch only processes `.py` files; the README counts all file types. Treat the JSON files as authoritative for `.py` findings; note potential additional data integrity issues.

---

## Two-Pass Approach

Matching Bandit MEDIUM/HIGH findings to Snitch findings cannot be reliably automated due to inconsistent `where` fields across LLMs. The script runs in two passes:

- **Pass 1**: Analyze all data, flag obvious FPs, generate all tables/figures, and produce side-by-side review listings + an annotation template.
- **Pass 2**: After user annotates the template (marking which Bandit M/H issues each LLM found), compute composite scores and produce the final comparison outputs.

---

## Input Files

**Bandit:** `results_bandit/bandit_{beaverhabits,fail2ban,yum}.json`

Each file has `results[]` with fields: `filename`, `issue_severity` (LOW/MEDIUM/HIGH), `issue_confidence`, `test_id`, `test_name`, `issue_text`, `line_number`, `issue_cwe`.

**Snitch:** `output_{repo}_{model}/snitch_results.json` (9 files)

Each file is a JSON array with fields: `filename`, `filepath`, `where`, `what`, `why`, `fix`. Entries where all four analysis fields equal `"skipped"` are skipped entries.

---

## Pass 1: `python analyze_results.py --pass 1`

### A. Bandit Analysis

1. Load all 3 Bandit JSONs.
2. Count findings by severity (LOW / MEDIUM / HIGH) per repo → **LaTeX table** (`bandit_severity_table.tex`): rows = repos, columns = LOW / MEDIUM / HIGH / TOTAL.
3. For MEDIUM + HIGH findings only: group by `test_name` / `test_id`. Identify recurring categories (e.g., subprocess use, crypto weakness, injection) → **LaTeX table** (`bandit_medium_high_categories.tex`): rows = category, columns = repos, cells = count. Also produce a **stacked bar chart** (`bandit_categories.pdf`) for visual aid.

### B. Snitch Analysis

1. Load all 9 Snitch JSONs.
2. For each scan: count total entries, skipped entries, non-skipped ("actual") findings.
3. **LaTeX table** (`snitch_findings_table.tex`): rows = repos, column groups = models, cells = (total / skipped / actual).

### C. False Positive / Hallucination Flagging

Flag an entry as a **likely FP or hallucination** if ANY of:

- `where` matches no `filename.py:digits` pattern (i.e., no file+line reference — function names, class names, `code:N-N`, CSS anchor strings, etc.)
- `what` or `why` mentions CSS, comments, license, copyright, or a known stdlib constant (e.g., `calendar.MONDAY`, `os.path`, `sys.argv`)
- `why` is fewer than 20 characters (likely a hallucination / non-finding)

Distinguish severity:

- **Egregious (hallucination)**: flags a comment, license block, CSS property, or non-code artifact as a security issue.
- **Minor**: misidentifies a real code pattern (e.g., flags a constant that isn't a credential).

Outputs:

- **LaTeX table** (`snitch_fp_table.tex`): rows = repos, column groups = models, cells = (flagged FP count / FP rate as % of actual findings).
- Per-scan flagged entries printed to `analysis/flagged_{repo}_{model}.txt`.

### D. Issue Category Analysis (Snitch)

For non-skipped, non-FP Snitch findings, cluster `what` text into broad categories (injection, authentication, cryptography, subprocess/OS, path traversal, info disclosure, other) using keyword matching. Produce **one grouped bar chart per repo** (`snitch_categories_{repo}.pdf`) showing category counts per model side-by-side.

### E. Side-by-Side Review Listings

For each repo, for each Bandit MEDIUM/HIGH finding:

- Record: `test_id`, `test_name`, `issue_text`, `filename`, `line_number`, `severity`
- For each of the 3 models, list all Snitch non-skipped findings whose `filename` matches the Bandit finding's filename (basename match, case-insensitive)

Output:

- Human-readable `analysis/review_{repo}.txt` — one Bandit finding per block, with matching Snitch entries indented below.
- Machine-readable `analysis/review_annotations.json` — template pre-populated with all Bandit MEDIUM/HIGH findings; `found_by` fields default to `null` for user to fill in as `true`/`false`/`"partial"`.

**Annotation template structure:**

```json
{
  "beaverhabits": [
    {
      "bandit_id": 0,
      "test_id": "B105",
      "filename": "app/auth.py",
      "line_number": 26,
      "severity": "MEDIUM",
      "issue_text": "...",
      "found_by": { "gemma3": null, "llama3.1": null, "qwen2.5": null }
    }
  ]
}
```

---

## Pass 2: `python analyze_results.py --pass 2 --annotations analysis/review_annotations.json`

Requires a completed `review_annotations.json` (all `null` values replaced with `true`, `false`, or `"partial"`).

1. **Recall per (repo, model)** = (# Bandit M/H findings marked `true` or `"partial"`) / (total Bandit M/H findings for that repo). Partial counts as 0.5.
2. **FP rate per (repo, model)** = (flagged FP count from Pass 1) / (actual findings from Pass 1).
3. **Composite score** = Recall − FP\_rate (range: −1 to 1; higher is better).
4. **Best LLM per repo** = model with highest composite score.
5. **Bandit M/H issues missed by all models** = findings where all three `found_by` values are `false`.

Outputs:

- **LaTeX table** (`composite_scores_table.tex`): rows = repos, column groups = models, cells = (recall / FP rate / composite). Best per row highlighted with `\textbf`.
- **Grouped bar chart** (`composite_scores.pdf`): recall, FP rate, and composite score per model per repo.
- **LaTeX table** (`missed_bandit_issues.tex`): missed MEDIUM/HIGH Bandit findings listing `test_id`, `filename`, `line_number`, `issue_text` grouped by repo.
- Summary printed to stdout: best LLM per repo with scores.

---

## New Files

- `analyze_results.py` — single script at repo root, `argparse` flags `--pass` (1 or 2), `--annotations`, and `--replot`. Creates `analysis/` directory. Dependencies: `matplotlib` (add to `pyproject.toml` dev deps). All other dependencies are stdlib (`json`, `re`, `csv`, `pathlib`, `collections`).

### Figure Persistence (Code + Data)

Each figure is saved as a PDF (`savefig(..., format="pdf")`) for lossless insertion into LaTeX. To allow later tweaking without re-running the full analysis:

- The **processed data** behind each figure is serialized to a companion JSON file alongside the PDF (e.g., `bandit_categories.pdf` → `bandit_categories_data.json`). This captures the exact arrays/dicts passed to matplotlib.
- Each figure's **plotting code** is isolated into a small standalone helper function in `analyze_results.py` (e.g., `plot_bandit_categories(data, output_path)`). These functions can read from the companion JSON if called directly, so a figure can be regenerated or restyled without re-parsing all the raw scan data.

Future tweak workflow: edit the plot function → `python analyze_results.py --replot bandit_categories` → new PDF written, data unchanged.

---

## Verification

**Pass 1:**

```bash
source venv/bin/activate
python analyze_results.py --pass 1
ls analysis/  # expect: *.tex, *.pdf, *_data.json, review_*.txt, flagged_*.txt, review_annotations.json
```

Spot-check: confirm `bandit_severity_table.tex` totals match RESULTS_README counts. Confirm `review_beaverhabits.txt` lists the Bandit MEDIUM/HIGH beaverhabits findings.

**Pass 2** (after annotation):

```bash
python analyze_results.py --pass 2 --annotations analysis/review_annotations.json
ls analysis/  # expect: composite_scores_table.tex, composite_scores.pdf, missed_bandit_issues.tex
```

Spot-check: composite score = recall − FP\_rate for at least one (repo, model) pair by hand.
