#!/usr/bin/env python3
"""Full pipeline with visible memory: PRD → analysis → UI plan → code."""

import argparse
import json
import sys
from pathlib import Path

from memory.store import MemoryStore
from pipeline.orchestrator import PipelineOrchestrator


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Agents 1–3 with JSON file memory (preferences + history)."
    )
    parser.add_argument("prd", help="Path to IoT PRD text file")
    parser.add_argument(
        "-o",
        "--output-dir",
        default="generated",
        help="Directory for generated TSX files (default: generated)",
    )
    parser.add_argument(
        "--memory",
        default="data/memory.json",
        help="Path to memory JSON file (default: data/memory.json)",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Do not write PRD/layout to memory (still reads preferences)",
    )
    parser.add_argument("--model", help="Override GROQ_MODEL")
    args = parser.parse_args()

    prd_path = Path(args.prd)
    if not prd_path.is_file():
        print(f"PRD not found: {prd_path}", file=sys.stderr)
        return 1

    prd_text = prd_path.read_text(encoding="utf-8")
    orchestrator = PipelineOrchestrator(
        memory_path=args.memory,
        model=args.model,
    )
    if args.no_save:
        orchestrator.memory.load()

    result = orchestrator.run(prd_text, save_memory=not args.no_save)

    print(result.memory_display, file=sys.stderr)
    for tc in result.tool_calls:
        print(
            f"TOOL {tc.tool}({tc.input}) -> {tc.output}",
            file=sys.stderr,
        )

    if result.error:
        print(result.error, file=sys.stderr)
        return 1

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if result.code:
        for comp in result.code.get("components", []):
            (out_dir / f"{comp['name']}.tsx").write_text(
                comp["code"] + "\n", encoding="utf-8"
            )
        if result.code.get("entrypoint"):
            (out_dir / "DashboardPage.tsx").write_text(
                result.code["entrypoint"] + "\n", encoding="utf-8"
            )

    print(json.dumps(result.ui_plan, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
