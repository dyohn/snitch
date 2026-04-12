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
Source file → read_sourcecode() → SastAgent.analyze() → Ollama HTTP API → _parse_json() → finding dict
```

Each finding dict has four keys: `where` (file:startLine-endLine), `what`, `why`, `fix`.

### Key modules

- **`sast_agent.py`** — `SastAgent` class: the core LLM client. Builds the HTTP payload from prompts, POSTs to Ollama's `/api/chat` endpoint (default: `http://localhost:11434`), and parses the JSON response. Falls back to a `"skipped"` sentinel dict on parse failure.
- **`prompts.py`** — System prompts. `LLM_SAST_PROMPT` is the active prompt (injected via role `system`); `LLM_USER_TEMPLATE` wraps user code. `AMBITIOUS_LLM_SAST_PROMPT` is defined but not yet wired in.
- **`file_utils.py`** — `read_sourcecode(path)` reads a file as a UTF-8 string (errors ignored). `read_all_from_folder(path)` recursively walks a directory and returns `list[tuple[str, str]]` (filename, content); symlinks are skipped.
- **`repo_io.py`** — `SourceCodeFile` dataclass and `RepositoryIO` class skeleton. `RepositoryIO.read_repository()` is a stub.

### What's not yet implemented

- `RepositoryIO.read_repository()` — repository-level file discovery
- Orchestrator / CLI entry point for end-to-end scanning
- Test suite (`tests/` is empty)

## Code Standards

- Python 3.11+
- Ruff for linting/formatting: line length **79**, target `py311`
- Docstring code formatting enabled
