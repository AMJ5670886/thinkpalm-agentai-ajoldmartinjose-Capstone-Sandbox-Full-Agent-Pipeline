#!/usr/bin/env python3
"""View or update pipeline memory (preferences, PRD history, layouts)."""

import argparse
import json
import sys

from memory.store import MemoryStore


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage IoT pipeline memory.")
    parser.add_argument(
        "--memory",
        default="data/memory.json",
        help="Path to memory JSON file (default: data/memory.json)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("show", help="Print memory contents (required for demos)")

    set_p = sub.add_parser("set", help="Update user preferences")
    set_p.add_argument("--theme", choices=["light", "dark"])
    set_p.add_argument(
        "--chart-preference",
        dest="chart_preference",
        choices=["line", "bar", "area", "pie"],
    )
    set_p.add_argument(
        "--sidebar-default",
        dest="sidebar_default",
        type=lambda x: x.lower() in ("1", "true", "yes"),
    )

    init_p = sub.add_parser("init", help="Create memory file from example defaults")
    init_p.add_argument(
        "--dark",
        action="store_true",
        help="Initialize with theme=dark, chart_preference=line",
    )

    args = parser.parse_args()
    store = MemoryStore(args.memory)

    if args.command == "show":
        print(store.format_display())
        data = store.load()
        print(json.dumps(data.model_dump(), indent=2))
        return 0

    if args.command == "init":
        if args.dark:
            store.update_preferences(theme="dark", chart_preference="line")
        else:
            store.load()
            store.save()
        print(f"Initialized {store.path}")
        print(store.format_display())
        return 0

    if args.command == "set":
        updates = {}
        if args.theme:
            updates["theme"] = args.theme
        if args.chart_preference:
            updates["chart_preference"] = args.chart_preference
        if args.sidebar_default is not None:
            updates["sidebar_default"] = args.sidebar_default
        if not updates:
            print("No preference flags provided.", file=sys.stderr)
            return 1
        store.update_preferences(**updates)
        print("Updated preferences.")
        print(store.format_display())
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
