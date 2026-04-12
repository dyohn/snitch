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

## `run_snitch.py` — CLI driver at repo root

`argparse`-based script with positional `target_dir` / `output_dir` and optional `--format` (nargs="+"), `--model`, `--ollama-url`, `--verbose`. `--format` accepts multiple values in one invocation. Connection errors from Ollama produce a clear message and exit 1. Run with venv active: `python run_snitch.py <target_dir> <output_dir>`.
