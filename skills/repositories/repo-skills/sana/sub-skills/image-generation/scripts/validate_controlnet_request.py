#!/usr/bin/env python3
"""Validate a Sana ControlNet JSON request without running the model.

The native ControlNet inference path expects a JSON list. Each item must contain
a non-empty prompt and exactly one of ref_image_path or ref_controlmap_path.
This script checks JSON structure, referenced image/control-map files, optional
config shape, and HED annotator checkpoint presence. It never imports Sana,
initializes HED, downloads checkpoints, or uses CUDA.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
DEFAULT_ANNOTATOR_CKPT = "tools/controlnet/annotator/ckpts/ControlNetHED.pth"


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    infos: list[str] = field(default_factory=list)

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def info(self, msg: str) -> None:
        self.infos.append(msg)

    def exit_code(self, strict: bool) -> int:
        if self.errors or (strict and self.warnings):
            return 1
        return 0


def load_json(path: Path, report: Report) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        report.error(f"JSON file is missing: {path}")
    except json.JSONDecodeError as exc:
        report.error(f"Invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}")
    except OSError as exc:
        report.error(f"Could not read JSON file {path}: {exc}")
    return None


def resolve_existing(path_text: str, project_dir: Path, json_dir: Path) -> tuple[Path | None, list[Path]]:
    p = Path(path_text)
    candidates = [p] if p.is_absolute() else [project_dir / p, json_dir / p, Path.cwd() / p]
    seen: set[Path] = set()
    unique: list[Path] = []
    for c in candidates:
        try:
            key = c.resolve(strict=False)
        except OSError:
            key = c
        if key not in seen:
            unique.append(c)
            seen.add(key)
    for c in unique:
        if c.exists():
            return c, unique
    return None, unique


def validate_image_file(label: str, path_text: str, project_dir: Path, json_dir: Path, report: Report, inspect_image: bool) -> None:
    found, candidates = resolve_existing(path_text, project_dir, json_dir)
    if found is None:
        report.error(f"{label} missing: {path_text} (checked {', '.join(str(c) for c in candidates)})")
        return
    if found.suffix.lower() not in IMAGE_SUFFIXES:
        report.warn(f"{label} has unusual image suffix {found.suffix!r}: {path_text}")
    if not inspect_image:
        report.info(f"{label} exists: {path_text}")
        return
    try:
        from PIL import Image
    except Exception as exc:  # pragma: no cover - depends on environment
        report.warn(f"PIL is unavailable, so image dimensions were not inspected: {exc}")
        return
    try:
        with Image.open(found) as img:
            width, height = img.size
            if width <= 0 or height <= 0:
                report.error(f"{label} has invalid dimensions {width}x{height}: {path_text}")
            else:
                report.info(f"{label} opens as {width}x{height} {img.mode}: {path_text}")
            if width % 32 != 0 or height % 32 != 0:
                report.warn(f"{label} dimensions are not multiples of 32; Sana will resize/bin/crop internally: {path_text}")
    except Exception as exc:
        report.error(f"{label} exists but PIL cannot open it: {path_text}: {exc}")


def validate_items(data: Any, project_dir: Path, json_dir: Path, report: Report, inspect_image: bool) -> tuple[int, int]:
    if not isinstance(data, list):
        report.error("ControlNet JSON must be a top-level list of request objects.")
        return 0, 0
    if not data:
        report.warn("ControlNet JSON list is empty; no images would be generated.")
    ref_image_count = 0
    ref_control_count = 0
    for idx, item in enumerate(data):
        prefix = f"item[{idx}]"
        if not isinstance(item, dict):
            report.error(f"{prefix} must be an object, got {type(item).__name__}.")
            continue
        prompt = item.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            report.error(f"{prefix}.prompt must be a non-empty string.")
        has_ref_image = "ref_image_path" in item and item.get("ref_image_path") not in (None, "")
        has_ref_control = "ref_controlmap_path" in item and item.get("ref_controlmap_path") not in (None, "")
        if has_ref_image == has_ref_control:
            report.error(f"{prefix} must contain exactly one of ref_image_path or ref_controlmap_path.")
            continue
        if has_ref_image:
            ref_image_count += 1
            value = item.get("ref_image_path")
            if not isinstance(value, str):
                report.error(f"{prefix}.ref_image_path must be a string path.")
            else:
                validate_image_file(f"{prefix}.ref_image_path", value, project_dir, json_dir, report, inspect_image)
        if has_ref_control:
            ref_control_count += 1
            value = item.get("ref_controlmap_path")
            if not isinstance(value, str):
                report.error(f"{prefix}.ref_controlmap_path must be a string path.")
            else:
                validate_image_file(f"{prefix}.ref_controlmap_path", value, project_dir, json_dir, report, inspect_image)
        extra = sorted(set(item) - {"prompt", "ref_image_path", "ref_controlmap_path"})
        if extra:
            report.warn(f"{prefix} has extra keys ignored by the native ControlNet script: {', '.join(extra)}")
    return ref_image_count, ref_control_count


def validate_config(config_text: str | None, project_dir: Path, json_dir: Path, report: Report) -> None:
    if not config_text:
        report.warn("No --config supplied; use a Sana ControlNet config, not a plain image config.")
        return
    found, candidates = resolve_existing(config_text, project_dir, json_dir)
    if found is None:
        report.error(f"Config file is missing: {config_text} (checked {', '.join(str(c) for c in candidates)})")
        return
    if found.suffix.lower() not in {".yaml", ".yml"}:
        report.warn(f"Config does not look like YAML: {config_text}")
    try:
        text = found.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = found.read_text(errors="ignore")
    except OSError as exc:
        report.error(f"Could not read config {config_text}: {exc}")
        return
    lowered = text.lower()
    if "controlnet" not in lowered and "sanamscontrolnet" not in lowered:
        report.warn("Config text does not mention ControlNet/SanaMSControlNet; verify this is not a plain Sana image config.")
    else:
        report.info(f"Config appears ControlNet-related: {config_text}")
    if "image_size" in lowered and "1024" not in lowered:
        report.warn("ControlNet source configs are 1024px; verify any non-1024 image_size deliberately.")


def validate_annotator(ref_image_count: int, annotator_ckpt: str, project_dir: Path, json_dir: Path, require: bool, report: Report) -> None:
    if ref_image_count == 0:
        report.info("No ref_image_path items; HED annotator checkpoint is not required when using only ref_controlmap_path.")
        return
    found, candidates = resolve_existing(annotator_ckpt, project_dir, json_dir)
    if found is None:
        msg = (
            "HED annotator checkpoint is not present. Native ref_image_path preprocessing will try to obtain "
            "ControlNetHED.pth and then move the annotator to CUDA. Use ref_controlmap_path to bypass HED. "
            f"Checked {', '.join(str(c) for c in candidates)}"
        )
        if require:
            report.error(msg)
        else:
            report.warn(msg)
    else:
        report.info(f"HED annotator checkpoint exists: {annotator_ckpt}")


def print_human(report: Report, item_count: int, ref_image_count: int, ref_control_count: int) -> None:
    print("# Sana ControlNet request validation")
    print(f"items: {item_count}")
    print(f"ref_image_path items: {ref_image_count}")
    print(f"ref_controlmap_path items: {ref_control_count}")
    print()
    for title, values in (("ERRORS", report.errors), ("WARNINGS", report.warnings), ("INFO", report.infos)):
        print(f"## {title}")
        if values:
            for value in values:
                print(f"- {value}")
        else:
            print("- none")
        print()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--json-file", required=True, help="ControlNet JSON list to validate.")
    parser.add_argument("--project-dir", default=".", help="Base directory for paths stored relative to a Sana project directory.")
    parser.add_argument("--config", default=None, help="Optional ControlNet config path to sanity-check.")
    parser.add_argument("--annotator-ckpt", default=DEFAULT_ANNOTATOR_CKPT, help="Expected HED checkpoint path for ref_image_path preprocessing.")
    parser.add_argument("--require-annotator-ckpt", action="store_true", help="Treat missing HED checkpoint as an error instead of a warning.")
    parser.add_argument("--no-image-open", action="store_true", help="Only check that image paths exist; do not open with PIL.")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero on warnings as well as errors.")
    parser.add_argument("--json-report", action="store_true", help="Emit machine-readable JSON report.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    report = Report()
    json_path = Path(args.json_file)
    json_dir = json_path.parent if json_path.parent != Path("") else Path(".")
    project_dir = Path(args.project_dir)
    data = load_json(json_path, report)
    item_count = len(data) if isinstance(data, list) else 0
    ref_image_count = ref_control_count = 0
    if data is not None:
        ref_image_count, ref_control_count = validate_items(
            data,
            project_dir=project_dir,
            json_dir=json_dir,
            report=report,
            inspect_image=not args.no_image_open,
        )
    validate_config(args.config, project_dir, json_dir, report)
    validate_annotator(
        ref_image_count,
        args.annotator_ckpt,
        project_dir,
        json_dir,
        args.require_annotator_ckpt,
        report,
    )
    if args.json_report:
        print(json.dumps({
            "items": item_count,
            "ref_image_path_items": ref_image_count,
            "ref_controlmap_path_items": ref_control_count,
            "errors": report.errors,
            "warnings": report.warnings,
            "infos": report.infos,
            "strict": args.strict,
        }, indent=2))
    else:
        print_human(report, item_count, ref_image_count, ref_control_count)
    return report.exit_code(args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
