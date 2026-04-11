# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Snitch is an agentic application security scanner — an LLM interface for SAST (Static Application Security Testing). Research project at Florida Institute of Technology.

## Development Setup

```bash
bash devSetup.sh   # Creates Python 3.13 venv, installs dev deps (pytest, hatchling) in editable mode
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

## Code Standards

- Python 3.11+
- Ruff for linting/formatting: line length **79**, target `py311`
- Docstring code formatting enabled
