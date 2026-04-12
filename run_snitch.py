#!/usr/bin/env python3
"""run_snitch.py — CLI entry point for the Snitch SAST scanner.

Usage (venv must be active):
    python run_snitch.py <target_dir> <output_dir> [options]
"""

import argparse
import sys
from pathlib import Path

import requests

from snitch.output import write_output
from snitch.repo_io import RepositoryIO
from snitch.sast_agent import SastAgent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run_snitch",
        description="Snitch — agentic SAST scanner powered by Ollama",
    )
    parser.add_argument(
        "target_dir",
        help="Directory to scan for source code files",
    )
    parser.add_argument(
        "output_dir",
        help="Directory where report file(s) will be written",
    )
    parser.add_argument(
        "--format",
        nargs="+",
        choices=["json", "csv", "txt"],
        default=["json"],
        metavar="FORMAT",
        help=(
            "Output format(s): json, csv, txt "
            "(default: json; multiple allowed)"
        ),
    )
    parser.add_argument(
        "--model",
        default="llama3.1",
        help="Ollama model name (default: llama3.1)",
    )
    parser.add_argument(
        "--ollama-url",
        default="http://localhost:11434",
        dest="ollama_url",
        help=(
            "Ollama server base URL "
            "(default: http://localhost:11434)"
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print each filename to stderr as it is scanned",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    target_dir = Path(args.target_dir)
    output_dir = Path(args.output_dir)

    if not target_dir.exists() or not target_dir.is_dir():
        print(
            f"Error: target_dir '{target_dir}' does not exist "
            "or is not a directory.",
            file=sys.stderr,
        )
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    agent = SastAgent(
        model_name=args.model, base_url=args.ollama_url
    )
    repo = RepositoryIO(repo_path=target_dir)

    results = []
    try:
        for result in agent.run(repo):
            results.append(result)
            if args.verbose:
                print(f"  Scanned: {result.filename}", file=sys.stderr)
    except requests.exceptions.ConnectionError:
        print(
            f"Error: cannot connect to Ollama at {args.ollama_url}. "
            "Is `ollama serve` running?",
            file=sys.stderr,
        )
        sys.exit(1)

    for fmt in args.format:
        written = write_output(results, output_dir, fmt)
        print(f"Wrote {fmt.upper()} report: {written}")

    print(f"Scan complete. {len(results)} file(s) scanned.")
    sys.exit(0)


if __name__ == "__main__":
    main()
