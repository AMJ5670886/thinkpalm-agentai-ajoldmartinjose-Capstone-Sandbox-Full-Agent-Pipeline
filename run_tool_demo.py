#!/usr/bin/env python3
"""Demonstrate searchTailwindComponent custom tool."""

import json
import sys

from tools.tailwind_search import search_tailwind_component


def main() -> int:
    widget = sys.argv[1] if len(sys.argv) > 1 else "chart"
    match = search_tailwind_component(widget)
    print(f"searchTailwindComponent({widget!r})")
    print(json.dumps(match.model_dump(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
