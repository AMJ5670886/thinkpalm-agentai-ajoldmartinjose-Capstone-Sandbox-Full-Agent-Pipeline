#!/usr/bin/env python3
"""CLI entry point for Agent 1 — PRD Analysis Agent."""

import argparse
import json
import sys
from pathlib import Path

from agents.prd_analysis import PRDAnalysisAgent


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Agent 1 — PRD Analysis: extract devices and widgets from an IoT PRD."
    )
    parser.add_argument(
        "prd",
        nargs="?",
        help="Path to PRD file, or omit to read from stdin",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Write JSON result to this file (default: stdout)",
    )
    parser.add_argument(
        "--model",
        help="Override GROQ_MODEL (default: gpt-4o-mini)",
    )
    args = parser.parse_args()

    if args.prd:
        prd_text = Path(args.prd).read_text(encoding="utf-8")
    else:
        prd_text = sys.stdin.read()

    agent = PRDAnalysisAgent(model=args.model)
    result = agent.analyze(prd_text)
    payload = json.dumps(result.model_dump(), indent=2)

    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        print(payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
