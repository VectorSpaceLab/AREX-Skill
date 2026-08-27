#!/usr/bin/env python3
"""Inspect a DeepPavlov config without downloading or installing anything.

This helper is intentionally read-only. It resolves the config path, prints the
main Chainer endpoints, and summarizes nested configs, component classes,
requirements files, and download references.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, Any


# Make the helper runnable directly from a repository checkout without requiring
# the package to be installed first. The search stops at the first ancestor that
# contains the DeepPavlov package root.
for _candidate in [Path(__file__).resolve().parent, *Path(__file__).resolve().parents]:
    if (_candidate / "deeppavlov" / "__init__.py").is_file():
        sys.path.insert(0, str(_candidate))
        break

from deeppavlov.core.commands.utils import parse_config
from deeppavlov.core.common.file import find_config
from deeppavlov.core.data.utils import get_all_elems_from_json
from deeppavlov.download import get_config_downloads
from deeppavlov.utils.pip_wrapper import get_config_requirements


def unique_preserve_order(items: Iterable[Any]) -> list[Any]:
    """Return unique items in first-seen order without mutating the inputs."""
    seen = set()
    result = []
    for item in items:
        marker = json.dumps(item, sort_keys=True, default=str) if isinstance(item, (dict, list)) else str(item)
        if marker in seen:
            continue
        seen.add(marker)
        result.append(item)
    return result


def build_summary(config_path: str) -> dict[str, Any]:
    """Collect a safe inspection summary for the given config path or stem."""
    resolved = find_config(config_path)
    parsed = parse_config(resolved)

    chainer = parsed.get("chainer", {})
    class_names = unique_preserve_order(get_all_elems_from_json(parsed, "class_name"))
    nested_config_paths = unique_preserve_order(get_all_elems_from_json(parsed, "config_path"))
    requirement_files = sorted(str(Path(path)) for path in get_config_requirements(parsed))
    downloads = [
        {"url": url, "destination": str(destination)}
        for url, destination in sorted(get_config_downloads(parsed), key=lambda item: (item[0], str(item[1])))
    ]

    return {
        "resolved_config_path": str(resolved),
        "chainer": {
            "in": chainer.get("in", []),
            "out": chainer.get("out", []),
            "in_y": chainer.get("in_y", []),
            "pipe_length": len(chainer.get("pipe", [])),
        },
        "class_names": class_names,
        "nested_config_paths": [str(path) for path in nested_config_paths],
        "metadata": {
            "imports": list(parsed.get("metadata", {}).get("imports", [])),
            "variables": parsed.get("metadata", {}).get("variables", {}),
            "requirements": requirement_files,
        },
        "downloads": downloads,
    }


def print_human(summary: dict[str, Any]) -> None:
    """Render the summary in a compact, human-readable format."""
    print(f"Resolved config: {summary['resolved_config_path']}")
    print("Chainer:")
    for key, value in summary["chainer"].items():
        print(f"  {key}: {value}")

    print("Component class names:")
    for name in summary["class_names"]:
        print(f"  - {name}")

    print("Nested config paths:")
    if summary["nested_config_paths"]:
        for path in summary["nested_config_paths"]:
            print(f"  - {path}")
    else:
        print("  - (none)")

    print("Metadata imports:")
    if summary["metadata"]["imports"]:
        for item in summary["metadata"]["imports"]:
            print(f"  - {item}")
    else:
        print("  - (none)")

    print("Metadata variables:")
    if summary["metadata"]["variables"]:
        for key, value in summary["metadata"]["variables"].items():
            print(f"  - {key}: {value}")
    else:
        print("  - (none)")

    print("Requirement files:")
    if summary["metadata"]["requirements"]:
        for item in summary["metadata"]["requirements"]:
            print(f"  - {item}")
    else:
        print("  - (none)")

    print("Downloads:")
    if summary["downloads"]:
        for item in summary["downloads"]:
            print(f"  - {item['url']} -> {item['destination']}")
    else:
        print("  - (none)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect a DeepPavlov config without downloading or installing anything.",
    )
    parser.add_argument(
        "config_path",
        help="Config file path or config stem understood by DeepPavlov.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of the human summary.",
    )
    args = parser.parse_args(argv)

    try:
        summary = build_summary(args.config_path)
    except Exception as exc:  # pragma: no cover - keep the helper informative in failure cases
        print(f"Error while inspecting config: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_human(summary)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
