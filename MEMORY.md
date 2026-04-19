# MEMORY.md

Implementation decisions made during development. Each entry records what changed and why. See git history for exact diffs.

---

## `startWork.sh` removed

Developers run `bash devSetup.sh` once for first-time setup, then manually `source venv/bin/activate` / `deactivate` each session. No wrapper script.

## `file_utils.read_all_from_folder` — return `(Path, str)` not `(str, str)`

Returning the full `Path` object instead of just `entry.name` means callers always have the real filepath, not just the bare filename. This is necessary for files in subdirectories where the name alone is ambiguous. Symlinks (file and directory) are skipped to prevent cycles.

## `repo_io.RepositoryIO` — generator instead of `self.files` list

`read_repository()` is a generator that yields `SourceCodeFile` instances one at a time rather than loading all file contents into memory. The `self.files: list` property was removed as it was never populated and would require holding the entire repository in memory. The `path` parameter was also dropped from `read_repository` since `self.repo_path` already holds it.

## `models.py` — new shared dataclass module

`SastResult(filename, filepath, finding)` extracted into its own module to avoid a circular import between `sast_agent.py` (which produces results) and `output.py` (which consumes them). Both import from `models.py`.

## `sast_agent.SastAgent.run()` — orchestration method added

`run(repo: RepositoryIO) -> Iterator[SastResult]` iterates the repository generator and yields one `SastResult` per file. Implemented as a generator so results stream to the caller rather than accumulating in memory. `analyze()` is unchanged.

## `output.py` — new output formatting module

Three formatters (`write_json`, `write_csv`, `write_text`) plus a `write_output()` dispatcher. All accept a materialized `list[SastResult]`. CSV uses `QUOTE_ALL` to handle embedded newlines/commas in LLM-generated text. Text report includes a UTC timestamp header and numbered entries.

## `analyze_results.py` — two-pass experiment results analyser

Standalone script at repo root. `--pass 1` loads all 9 Snitch and 3 Bandit JSONs, produces LaTeX tables (severity counts, M/H categories, findings counts, FP rates), PDF figures (stacked/grouped bar charts), flagged FP text files, and the side-by-side `review_annotations.json` template for manual Bandit↔Snitch matching. `--pass 2` reads the completed annotation file and computes recall, FP rate, and composite score per (repo, model), outputs LaTeX tables and a composite-scores PDF, and lists Bandit M/H issues missed by all LLMs. `--replot <name>` regenerates any single figure PDF from its companion `_data.json` without re-running the full analysis. All figures saved as PDF (LaTeX-ready); matplotlib backend set to `"pdf"`. `matplotlib>=3.8` added to pyproject.toml dev deps.

## `run_snitch.py` — CLI driver at repo root

`argparse`-based script with positional `target_dir` / `output_dir` and optional `--format` (nargs="+"), `--model`, `--ollama-url`, `--verbose`. `--format` accepts multiple values in one invocation. Connection errors from Ollama produce a clear message and exit 1. Run with venv active: `python run_snitch.py <target_dir> <output_dir>`.

---

## Merge from collaborator branch (PR #1, 2026-04-15)

Collaborator fixed the core JSON parsing problem: the LLM wraps its JSON object in prose, so `json.loads` on the full response always failed. Fix added `re.search(r'\{[^{}]*"where"[^{}]*\}', raw, re.DOTALL)` to extract the JSON object from anywhere in the response before falling back to raw parsing. Python requirement also lowered from 3.11 to 3.10. First-pass scan results collected for three repos (beaverhabits, yum, fail2ban) against llama3.1; Bandit baseline results also collected. Comparison spreadsheet and `RESULTS_README.md` added. The `.py` filter and logging instrumentation that had been added in the prior session were reverted in this merge.

## `.py` filter reapplied (2026-04-15)

`file_utils.read_all_from_folder` — `entry.suffix == ".py"` guard restored so non-Python files are skipped. Reverted in the collaborator merge; reapplied by request.

## Logging instrumentation reapplied (2026-04-15)

`sast_agent.py` — `logger = logging.getLogger(__name__)` added. DEBUG log emits raw LLM response; WARNING logs fire on both parse failure paths (regex extraction and final fallback). `run_snitch.py` — `logging.basicConfig` configured in `main()`: DEBUG level when `--verbose` is set, WARNING otherwise.
