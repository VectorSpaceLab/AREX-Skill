#!/usr/bin/env python3
"""Check the HunyuanImage-3.0 Gradio app import surface safely.

The checker never starts Gradio, loads model weights, opens a port, or calls a
network service. It verifies UI dependencies and canonical package imports, and
optionally scans a local source tree for the stale app import lines documented
by this sub-skill.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

CANONICAL_IMPORTS = [
    ("gradio", None),
    ("hunyuan_image_3", None),
    ("hunyuan_image_3.modeling_hunyuan_image_3", "HunyuanImage3ForCausalMM"),
    ("hunyuan_image_3.tokenization_hunyuan_image_3", "ImageInfo"),
    ("hunyuan_image_3.system_prompt", "get_system_prompt"),
]

STALE_IMPORT_LINES = {
    "from hunyuan_image_3.hunyuan import HunyuanImage3ForCausalMM": (
        "stale model import; canonical class is in hunyuan_image_3.modeling_hunyuan_image_3"
    ),
    "from hunyuan_image_3.tokenizer_wrapper import ImageInfo": (
        "stale ImageInfo import; canonical class is in hunyuan_image_3.tokenization_hunyuan_image_3"
    ),
}


def check_import(module_name: str, symbol: str | None) -> tuple[bool, str]:
    try:
        module = importlib.import_module(module_name)
        if symbol is not None:
            getattr(module, symbol)
    except Exception as exc:  # noqa: BLE001 - diagnostic tool should report exact failure
        target = f"{module_name}.{symbol}" if symbol else module_name
        return False, f"FAIL {target}: {type(exc).__name__}: {exc}"

    target = f"{module_name}.{symbol}" if symbol else module_name
    version = getattr(module, "__version__", None) if symbol is None else None
    suffix = f" ({version})" if version else ""
    return True, f"OK   {target}{suffix}"


def scan_source_tree(source_tree: Path) -> tuple[list[str], list[str]]:
    messages: list[str] = []
    problems: list[str] = []
    pipeline_path = source_tree / "app" / "pipeline.py"
    run_path = source_tree / "app" / "run_chatbot.py"

    if not pipeline_path.exists():
        problems.append(f"source scan: missing {pipeline_path}")
        return messages, problems

    text = pipeline_path.read_text(encoding="utf-8")
    for line, explanation in STALE_IMPORT_LINES.items():
        if line in text:
            problems.append(f"source scan: found {line!r} ({explanation})")
        else:
            messages.append(f"source scan: did not find stale line {line!r}")

    if run_path.exists():
        run_text = run_path.read_text(encoding="utf-8")
        if "from app.pipeline import HunyuanImage3AppPipeline" in run_text:
            messages.append("source scan: app entrypoint imports app.pipeline at module import time")
    else:
        problems.append(f"source scan: missing {run_path}")

    return messages, problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Safely check Gradio app imports and known HunyuanImage-3.0 app import breakage."
    )
    parser.add_argument(
        "--source-tree",
        type=Path,
        help="Optional local source tree to scan for the known stale app import lines.",
    )
    parser.add_argument(
        "--no-source-scan-note",
        action="store_true",
        help="Do not print the bundled note about known stale source imports when no source tree is scanned.",
    )
    args = parser.parse_args(argv)

    problems: list[str] = []
    print("# Canonical import checks")
    for module_name, symbol in CANONICAL_IMPORTS:
        ok, message = check_import(module_name, symbol)
        print(message)
        if not ok:
            problems.append(message)

    print()
    if args.source_tree is not None:
        print("# Source-tree app import scan")
        messages, scan_problems = scan_source_tree(args.source_tree)
        for message in messages:
            print(f"OK   {message}")
        for problem in scan_problems:
            print(f"FAIL {problem}")
        problems.extend(scan_problems)
    elif not args.no_source_scan_note:
        print("# Known source-app issue")
        for line, explanation in STALE_IMPORT_LINES.items():
            print(f"WARN app pipeline line {line!r}: {explanation}")
        print("WARN pass --source-tree to confirm whether a local checkout still contains these lines")

    print()
    if problems:
        print("STATUS: blocked - use CLI fallback or patch the app before launching the UI")
        return 1

    print("STATUS: import checks passed; still verify MODEL_ID, host, port, and checkpoint availability before launch")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
