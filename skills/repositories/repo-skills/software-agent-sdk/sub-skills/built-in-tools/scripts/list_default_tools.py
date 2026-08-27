#!/usr/bin/env python3
"""Print the default tool names and registry state."""

from __future__ import annotations

import json
import os


def main() -> int:
    os.environ.setdefault("OPENHANDS_SUPPRESS_BANNER", "1")
    from openhands.sdk.tool.registry import list_registered_tools, list_usable_tools
    from openhands.tools.preset.default import get_default_tools, register_default_tools

    register_default_tools(enable_browser=True)
    payload = {
        "default_no_browser": [t.name for t in get_default_tools(enable_browser=False)],
        "default_with_browser": [
            t.name for t in get_default_tools(enable_browser=True)
        ],
        "registered": list_registered_tools(),
        "usable": list_usable_tools(),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
