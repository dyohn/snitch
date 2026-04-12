# MEMORY.md

Implementation decisions made during development. Each entry records what changed and why. See git history for exact diffs.

---

## `startWork.sh` removed

Developers run `bash devSetup.sh` once for first-time setup, then manually `source venv/bin/activate` / `deactivate` each session. No wrapper script.

## `file_utils.read_all_from_folder` — return `(Path, str)` not `(str, str)`

Returning the full `Path` object instead of just `entry.name` means callers always have the real filepath, not just the bare filename. This is necessary for files in subdirectories where the name alone is ambiguous. Symlinks (file and directory) are skipped to prevent cycles.

## `repo_io.RepositoryIO` — generator instead of `self.files` list

`read_repository()` is a generator that yields `SourceCodeFile` instances one at a time rather than loading all file contents into memory. The `self.files: list` property was removed as it was never populated and would require holding the entire repository in memory. The `path` parameter was also dropped from `read_repository` since `self.repo_path` already holds it.

## `sast_agent.SastAgent` — no changes needed for generator integration

`SastAgent.analyze(text: str)` accepts a plain string, so callers simply iterate the `RepositoryIO` generator and pass `source_file.content`. No modifications to `SastAgent` were required.
