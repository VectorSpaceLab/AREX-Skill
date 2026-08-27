#!/usr/bin/env python3
"""Create or validate a safe Marker custom processor skeleton.

This helper never runs a Marker conversion and never downloads models. Use it to
print a reusable processor skeleton or validate that a processor class path is
importable and subclasses marker.processors.BaseProcessor.
"""

from __future__ import annotations

import argparse
import importlib
import sys
import textwrap
from pathlib import Path
from typing import Any


cwd = str(Path.cwd())
if cwd not in sys.path:
    sys.path.insert(0, cwd)


SKELETON = '''\
"""Example Marker custom processor.

Install this module in the runtime environment or make it importable on PYTHONPATH,
then reference it with a full class path such as:

    my_marker_extensions.processors.ExampleProcessor

When passed through ConfigParser with --processors, remember that the processor
list replaces Marker's converter default list; include every processor you need.
"""

from __future__ import annotations

from typing import Annotated

from marker.processors import BaseProcessor
from marker.schema import BlockTypes


class ExampleProcessor(BaseProcessor):
    """Minimal safe processor skeleton.

    Processors mutate the document in place. Avoid network calls, model downloads,
    and expensive work in __init__. Marker passes the same config dictionary used
    by the converter, and BaseProcessor applies matching config keys to class
    attributes.
    """

    block_types = None
    enabled: Annotated[bool, "Enable this processor."] = True
    note: Annotated[str, "Optional note for debugging."] = ""

    def __init__(self, config=None):
        super().__init__(config)

    def __call__(self, document):
        if not self.enabled:
            return None

        # Example traversal pattern. Replace with focused document mutations.
        for page in getattr(document, "pages", []):
            for block in getattr(page, "children", []):
                if self.block_types is not None and block.block_type not in self.block_types:
                    continue
                # Inspect or mutate block fields here. Keep changes deterministic.
                _ = block

        return None
'''


def _import_class(path: str) -> type:
    module_name, class_name = path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def _validate_class_path(path: str) -> tuple[bool, str]:
    try:
        from marker.processors import BaseProcessor
    except Exception as exc:  # noqa: BLE001
        return False, f"Could not import marker.processors.BaseProcessor: {exc}"

    try:
        cls = _import_class(path)
    except ValueError as exc:
        return False, f"Use a full module path like package.module.ClassName: {exc}"
    except Exception as exc:  # noqa: BLE001
        return False, f"Could not import {path}: {type(exc).__name__}: {exc}"

    if not isinstance(cls, type):
        return False, f"Imported object is not a class: {path}"
    if not issubclass(cls, BaseProcessor):
        return False, f"Class imports but is not a BaseProcessor subclass: {path}"

    return True, f"OK: {path} imports and subclasses marker.processors.BaseProcessor"


def _write_skeleton(path: str) -> None:
    target = Path(path)
    if target.exists():
        raise SystemExit(f"Refusing to overwrite existing file: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(SKELETON, encoding="utf-8")
    print(f"Wrote processor skeleton: {target}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Print, write, or validate a Marker custom processor skeleton."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--print-template",
        action="store_true",
        help="Print a reusable processor skeleton to stdout.",
    )
    group.add_argument(
        "--write-template",
        metavar="PATH",
        help="Write the processor skeleton to PATH; refuses to overwrite.",
    )
    group.add_argument(
        "--validate-class-path",
        metavar="CLASS_PATH",
        help="Import and validate a processor class path without running conversion.",
    )
    args = parser.parse_args(argv)

    if args.print_template:
        print(SKELETON)
        return 0

    if args.write_template:
        _write_skeleton(args.write_template)
        return 0

    ok, message = _validate_class_path(args.validate_class_path)
    wrapped = textwrap.fill(message, width=100)
    print(wrapped)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
