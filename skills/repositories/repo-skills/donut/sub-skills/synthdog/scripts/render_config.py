#!/usr/bin/env python3
"""Render a SynthDoG config template with explicit resource paths.

This helper stays inside the skill tree and does not depend on the original
checkout. It validates the external resource layout, replaces placeholder
tokens in a bundled YAML template, and writes a ready-to-run config for
`synthtiger`.

Example:
    python scripts/render_config.py --language en --resource-root ./resources \
        --output-config ./rendered/synthdog_en.yaml
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional

LANGUAGE_CORPUS = {
    "en": "enwiki.txt",
    "ja": "jawiki.txt",
    "ko": "kowiki.txt",
    "zh": "zhwiki.txt",
}
PLACEHOLDERS = {
    "__BACKGROUND_DIR__": "background_dir",
    "__PAPER_DIR__": "paper_dir",
    "__CORPUS_FILE__": "corpus_file",
    "__FONT_DIR__": "font_dir",
}
DIR_SUFFIXES = {
    "background_dir": (".jpg", ".jpeg", ".png", ".bmp", ".webp"),
    "paper_dir": (".jpg", ".jpeg", ".png", ".bmp", ".webp"),
    "font_dir": (".ttf", ".otf", ".ttc"),
}
ROOT = Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Render one of the bundled SynthDoG placeholder configs into a "
            "runnable YAML file."
        )
    )
    parser.add_argument(
        "--language",
        choices=sorted(LANGUAGE_CORPUS),
        default="en",
        help="Language bundle to render: en, ja, ko, or zh.",
    )
    parser.add_argument(
        "--template",
        type=Path,
        help="Path to a YAML template. Defaults to the bundled language template.",
    )
    parser.add_argument(
        "--resource-root",
        type=Path,
        help=(
            "Root directory containing background/, paper/, corpus/, and "
            "font/<language>/."
        ),
    )
    parser.add_argument(
        "--background-dir",
        type=Path,
        help="Override the background image directory.",
    )
    parser.add_argument(
        "--paper-dir",
        type=Path,
        help="Override the paper texture directory.",
    )
    parser.add_argument(
        "--corpus-file",
        type=Path,
        help="Override the UTF-8 corpus file.",
    )
    parser.add_argument(
        "--font-dir",
        type=Path,
        help="Override the font directory for the selected language.",
    )
    parser.add_argument(
        "--output-config",
        type=Path,
        required=True,
        help="Path where the rendered YAML file will be written.",
    )
    parser.add_argument(
        "--print-command",
        action="store_true",
        help="Print the matching synthtiger command after rendering.",
    )
    return parser


def default_template(language: str) -> Path:
    return ROOT / "references" / "configs" / f"config_{language}.yaml"


def resolve_template(args: argparse.Namespace) -> Path:
    template = args.template if args.template else default_template(args.language)
    template = template.expanduser().resolve()
    if not template.is_file():
        raise SystemExit(f"Template file not found: {template}")
    return template


def resolve_resources(args: argparse.Namespace) -> Dict[str, Path]:
    root = args.resource_root.expanduser().resolve() if args.resource_root else None
    resolved: Dict[str, Optional[Path]] = {
        "background_dir": args.background_dir,
        "paper_dir": args.paper_dir,
        "corpus_file": args.corpus_file,
        "font_dir": args.font_dir,
    }
    if root is not None:
        resolved["background_dir"] = resolved["background_dir"] or root / "background"
        resolved["paper_dir"] = resolved["paper_dir"] or root / "paper"
        resolved["corpus_file"] = (
            resolved["corpus_file"] or root / "corpus" / LANGUAGE_CORPUS[args.language]
        )
        resolved["font_dir"] = resolved["font_dir"] or root / "font" / args.language

    missing_values = [name for name, value in resolved.items() if value is None]
    if missing_values:
        raise SystemExit(
            "Provide --resource-root or all of --background-dir, --paper-dir, "
            "--corpus-file, and --font-dir."
        )

    checked: Dict[str, Path] = {}
    errors: List[str] = []
    for key, value in resolved.items():
        path = value.expanduser().resolve()
        checked[key] = path
        expected_dir = key != "corpus_file"
        exists = path.is_dir() if expected_dir else path.is_file()
        if not exists:
            kind = "directory" if expected_dir else "file"
            errors.append(f"{key} expected a {kind}: {path}")
            continue
        if expected_dir:
            suffixes = DIR_SUFFIXES.get(key, ())
            if suffixes and not any(
                child.is_file() and child.suffix.lower() in suffixes
                for child in path.iterdir()
            ):
                suffix_text = ", ".join(suffixes)
                errors.append(f"{key} contains no files with suffixes {suffix_text}: {path}")
        elif key == "corpus_file" and path.stat().st_size == 0:
            errors.append(f"corpus_file is empty: {path}")
    if errors:
        raise SystemExit("Missing resource paths:\n  - " + "\n  - ".join(errors))
    return checked


def render_template(template_text: str, paths: Dict[str, Path]) -> str:
    rendered = template_text
    for placeholder, key in PLACEHOLDERS.items():
        rendered = rendered.replace(placeholder, json.dumps(str(paths[key])))
    leftovers = [placeholder for placeholder in PLACEHOLDERS if placeholder in rendered]
    if leftovers:
        raise SystemExit("Unrendered placeholders remain: " + ", ".join(leftovers))
    return rendered


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    template = resolve_template(args)
    resources = resolve_resources(args)
    rendered = render_template(template.read_text(encoding="utf-8"), resources)

    output = args.output_config.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")

    print(f"Wrote rendered config: {output}")
    print(f"Template: {template}")
    print(f"background_dir={resources['background_dir']}")
    print(f"paper_dir={resources['paper_dir']}")
    print(f"corpus_file={resources['corpus_file']}")
    print(f"font_dir={resources['font_dir']}")
    if args.print_command:
        print(
            "Next command: "
            f"synthtiger -o <output-dir> -c <count> -w <workers> -v "
            f"scripts/template.py SynthDoG {output}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
