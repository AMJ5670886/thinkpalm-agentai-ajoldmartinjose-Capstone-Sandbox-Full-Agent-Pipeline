#!/usr/bin/env python3
"""CLI entry point for Agent 3 — Code Generator Agent."""

import argparse
import json
import sys
from pathlib import Path

from agents.code_generator import CodeGeneratorAgent
from memory.store import MemoryStore
from schemas.ui_plan import UIPlan


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Agent 3 — Code Generator: convert a UI plan JSON into "
            "React + Tailwind component source code."
        )
    )
    parser.add_argument(
        "ui_plan",
        nargs="?",
        help="Path to UI plan JSON (Agent 2 output), or omit to read from stdin",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        help="Directory to write component files into (default: print JSON to stdout)",
    )
    parser.add_argument(
        "--model",
        help="Override GROQ_MODEL (default: gpt-4o-mini)",
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

    if args.ui_plan:
        plan_payload = Path(args.ui_plan).read_text(encoding="utf-8")
    else:
        plan_payload = sys.stdin.read()

    data = json.loads(plan_payload)
    ui_plan = UIPlan.model_validate(data)

    store = MemoryStore(args.memory)
    if args.show_memory:
        print(store.format_display(), file=sys.stderr)

    agent = CodeGeneratorAgent(model=args.model)
    result = agent.generate(ui_plan, memory_context=store.context_for_agents())

    if args.output_dir:
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        for comp in result.components:
            filename = out_dir / f"{comp.name}.tsx"
            filename.write_text(comp.code + "\n", encoding="utf-8")

        if result.entrypoint:
            (out_dir / "DashboardPage.tsx").write_text(
                result.entrypoint + "\n", encoding="utf-8"
            )

        print(f"Wrote {len(result.components)} components to {out_dir}", file=sys.stderr)
        if result.entrypoint:
            print("Wrote DashboardPage.tsx entrypoint", file=sys.stderr)
    else:
        # Just print the structured JSON for inspection
        payload = json.dumps(result.model_dump(), indent=2)
        print(payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

