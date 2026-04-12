# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Snitch is an agentic application security scanner — an LLM interface for SAST (Static Application Security Testing). Research project at Florida Institute of Technology.

## Development Setup

```bash
bash devSetup.sh          # First-time setup: creates venv and installs deps from pyproject.toml
source venv/bin/activate  # Activate venv at the start of each work session
deactivate                # Deactivate venv when done
```

## Commands

```bash
bash runTests.sh             # Run all tests (pytest, outputs JUnit XML)
bash build.sh                # Build wheel distribution
bash clean.sh                # Remove localWheels/ and dist/
bash localPublish.sh         # Copy built wheel to localWheels/
```

Run a single test:

```bash
source venv/bin/activate && pytest tests/path/to/test_file.py::test_name -v
```

## Architecture

Snitch sends source code files to a local LLM (via Ollama) and parses structured JSON responses describing security findings.

### Data flow

```text
RepositoryIO.read_repository() → SastAgent.run() → SastAgent.analyze() → Ollama /api/chat → SastResult
SastResult list → output.write_output() → snitch_results.{json|csv|txt}
```

Each finding dict has four keys: `where` (file:startLine-endLine), `what`, `why`, `fix`.

### Key modules

- **`sast_agent.py`** — `SastAgent` class: the core LLM client. `analyze(text)` sends code to Ollama and returns a finding dict. `run(repo)` iterates a `RepositoryIO` and yields `SastResult` instances.
- **`models.py`** — `SastResult` dataclass: `filename`, `filepath`, `finding` dict. Shared between `sast_agent` and `output`.
- **`repo_io.py`** — `RepositoryIO(repo_path)` with `read_repository()` generator that yields `SourceCodeFile` instances (filename, filepath, content).
- **`file_utils.py`** — `read_sourcecode(path)` reads a file as a UTF-8 string (errors ignored). `read_all_from_folder(path)` recursively walks a directory returning `list[tuple[Path, str]]`; symlinks are skipped.
- **`output.py`** — `write_json`, `write_csv`, `write_text` formatters and `write_output(results, output_dir, fmt)` dispatcher. Output files are named `snitch_results.<fmt>`.
- **`prompts.py`** — `LLM_SAST_PROMPT` (active system prompt) and `LLM_USER_TEMPLATE`. `AMBITIOUS_LLM_SAST_PROMPT` is defined but not wired in.

### CLI

```bash
python run_snitch.py <target_dir> <output_dir> [--format json csv txt] [--model llama3.1] [--ollama-url URL] [--verbose]
```

Requires the venv to be active. Ollama must be running (`ollama serve`) with the target model pulled.

### What's not yet implemented

- Test suite (`tests/` is empty)

## Code Standards

- Python 3.11+
- Ruff for linting/formatting: line length **79**, target `py311`
- Docstring code formatting enabled
