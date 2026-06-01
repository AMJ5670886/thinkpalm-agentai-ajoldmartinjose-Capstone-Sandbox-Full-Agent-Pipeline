#!/usr/bin/env python3
"""CLI entry point for Agent 2 — UI Planner Agent."""

import argparse
import json
import sys
from pathlib import Path

from agents.ui_planner import UIPlannerAgent
from memory.store import MemoryStore
from schemas.prd_analysis import PRDAnalysisResult


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Agent 2 — UI Planner: convert Agent 1's analysis JSON into "
            "a layout + Tailwind component plan."
        )
    )
    parser.add_argument(
        "analysis",
        nargs="?",
        help="Path to Agent 1 JSON output, or omit to read from stdin",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Write JSON result to this file (default: stdout)",
    )
    parser.add_argument(
        "--model",
        help="Override OPENAI_MODEL (default: gpt-4o-mini)",
    )
    parser.add_argument(
        "--memory",
        default="data/memory.json",
        help="Memory file for user preferences (default: data/memory.json)",
    )
    parser.add_argument(
        "--show-memory",
        action="store_true",
        help="Print memory block before running",
    )
    args = parser.parse_args()

    if args.analysis:
        analysis_payload = Path(args.analysis).read_text(encoding="utf-8")
    else:
        analysis_payload = sys.stdin.read()

    data = json.loads(analysis_payload)
    analysis = PRDAnalysisResult.model_validate(data)

    store = MemoryStore(args.memory)
    if args.show_memory:
        print(store.format_display(), file=sys.stderr)

    agent = UIPlannerAgent(model=args.model)
    ui_plan = agent.plan(analysis, memory_context=store.context_for_agents())
    payload = json.dumps(ui_plan.model_dump(), indent=2)

    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        print(payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

