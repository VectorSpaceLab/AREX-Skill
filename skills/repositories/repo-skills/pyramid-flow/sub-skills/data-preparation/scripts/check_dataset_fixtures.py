#!/usr/bin/env python3
"""Validate Pyramid-Flow annotation rows and precompute fixture shapes.

The checks are deterministic and small. They do not download datasets or model
checkpoints. Optional loader smoke tests require Pyramid-Flow's `dataset` package
to be importable from the current process or from --repo-root.
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable, Sequence


KIND_REQUIRED_FIELDS = {
    "image-text": ("image", "text"),
    "video-training": ("video", "text", "latent", "text_fea"),
    "text-features": ("text", "text_fea"),
    "vae-latents": ("video", "latent"),
    "vae-video": ("video",),
    "vae-image": ("image",),
}
DEFAULT_IMPORT_MODULES = ("jsonlines", "cv2", "timm", "sentencepiece", "PIL", "torch", "torchvision")
RESOLUTION_TO_LATENT_HW = {
    "384p": (48, 80),
    "768p": (96, 160),
}


class ValidationError(ValueError):
    """Readable user-facing validation failure."""


def load_jsonl(path: Path, limit: int | None = None) -> Iterable[tuple[int, dict[str, Any]]]:
    if not path.exists():
        raise ValidationError(f"annotation file does not exist: {path}")
    if not path.is_file():
        raise ValidationError(f"annotation path is not a file: {path}")

    seen = 0
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValidationError(f"row {line_number} is not valid JSON: {exc.msg}") from exc
            if not isinstance(row, dict):
                raise ValidationError(f"row {line_number} must be a JSON object")
            yield line_number, row
            seen += 1
            if limit and seen >= limit:
                break
    if seen == 0:
        raise ValidationError(f"annotation file has no JSON rows: {path}")


def validate_row_fields(row: dict[str, Any], *, line_number: int, kind: str) -> None:
    required = KIND_REQUIRED_FIELDS[kind]
    missing = [field for field in required if field not in row]
    if missing:
        raise ValidationError(
            f"row {line_number} missing required field(s) for {kind}: {', '.join(missing)}"
        )
    for field in required:
        if not isinstance(row[field], str) or not row[field].strip():
            raise ValidationError(f"row {line_number} field {field!r} for {kind} must be a non-empty string")
    if "text" in required and not isinstance(row.get("text"), str):
        raise ValidationError(f"row {line_number} field 'text' for {kind} must be a string")
    if "frames" in row:
        frames = row["frames"]
        if not isinstance(frames, list) or not all(isinstance(item, int) and item >= 0 for item in frames):
            raise ValidationError(f"row {line_number} optional field 'frames' must be a list of non-negative integers")


def resolve_data_path(raw_path: str, base_dir: Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return base_dir / path


def validate_jsonl(args: argparse.Namespace) -> dict[str, Any]:
    annotation = Path(args.annotation)
    base_dir = Path(args.base_dir) if args.base_dir else annotation.parent
    rows = 0
    for line_number, row in load_jsonl(annotation, limit=args.limit):
        validate_row_fields(row, line_number=line_number, kind=args.kind)
        rows += 1
        if args.check_paths:
            for field in KIND_REQUIRED_FIELDS[args.kind]:
                if field == "text":
                    continue
                candidate = resolve_data_path(row[field], base_dir)
                if not candidate.exists():
                    raise ValidationError(f"row {line_number} field {field!r} path does not exist: {candidate}")
        if args.validate_artifacts:
            if "latent" in row:
                validate_latent_path(resolve_data_path(row["latent"], base_dir), args.resolution, None, None)
            if "text_fea" in row:
                validate_text_feature_path(resolve_data_path(row["text_fea"], base_dir))
    return {"annotation": str(annotation), "kind": args.kind, "rows_checked": rows}


def import_torch():
    try:
        return importlib.import_module("torch")
    except Exception as exc:  # pragma: no cover - environment specific.
        raise ValidationError(f"torch is required to inspect .pt artifacts: {exc}") from exc


def safe_torch_load(path: Path) -> Any:
    torch = import_torch()
    try:
        return torch.load(path, map_location="cpu", weights_only=True)
    except TypeError:
        return torch.load(path, map_location="cpu")
    except Exception as exc:
        raise ValidationError(f"could not load torch artifact {path}: {exc}") from exc


def shape_of(value: Any) -> tuple[int, ...] | None:
    shape = getattr(value, "shape", None)
    if shape is None:
        return None
    try:
        return tuple(int(dim) for dim in shape)
    except Exception:
        return None


def expected_hw(resolution: str, expected_latent_height: int | None, expected_latent_width: int | None) -> tuple[int, int, str]:
    if resolution == "custom":
        if expected_latent_height is None or expected_latent_width is None:
            raise ValidationError("custom resolution requires --expected-latent-height and --expected-latent-width")
        return expected_latent_height, expected_latent_width, "custom"
    if resolution not in RESOLUTION_TO_LATENT_HW:
        raise ValidationError(f"resolution must be one of {', '.join(sorted(RESOLUTION_TO_LATENT_HW))} or custom")
    h, w = RESOLUTION_TO_LATENT_HW[resolution]
    return h, w, resolution


def validate_latent_path(
    path: Path,
    resolution: str,
    expected_latent_height: int | None,
    expected_latent_width: int | None,
) -> dict[str, Any]:
    if not path.exists():
        raise ValidationError(f"latent file does not exist: {path}")
    latent = safe_torch_load(path)
    shape = shape_of(latent)
    if shape is None:
        raise ValidationError(f"latent artifact is not tensor-like and has no shape: {path}")
    if len(shape) != 5:
        raise ValidationError(f"latent shape rank is {len(shape)}; expected 5D [N, 16, T, H, W], got {shape}")
    if shape[1] != 16:
        raise ValidationError(f"latent channel dimension is {shape[1]}; expected 16 at shape[1], got {shape}")
    if shape[2] <= 0:
        raise ValidationError(f"latent temporal dimension must be positive, got {shape}")
    exp_h, exp_w, label = expected_hw(resolution, expected_latent_height, expected_latent_width)
    actual_h, actual_w = shape[-2], shape[-1]
    if (actual_h, actual_w) != (exp_h, exp_w):
        raise ValidationError(
            f"latent spatial shape is {actual_h}x{actual_w}; expected {exp_h}x{exp_w} for {label}"
        )
    return {"path": str(path), "shape": list(shape), "resolution": label}


def validate_text_feature_path(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValidationError(f"text feature file does not exist: {path}")
    obj = safe_torch_load(path)
    if not isinstance(obj, dict):
        raise ValidationError(f"text feature artifact must be a dict, got {type(obj).__name__}: {path}")
    required = ("prompt_embed", "prompt_attention_mask", "pooled_prompt_embed")
    missing = [field for field in required if field not in obj]
    if missing:
        raise ValidationError(f"text feature artifact missing required key(s): {', '.join(missing)}")
    shapes: dict[str, list[int]] = {}
    for field in required:
        shape = shape_of(obj[field])
        if shape is None:
            raise ValidationError(f"text feature key {field!r} is not tensor-like")
        if len(shape) == 0:
            raise ValidationError(f"text feature key {field!r} must have at least one dimension")
        shapes[field] = list(shape)
    return {"path": str(path), "shapes": shapes}


def write_jsonl(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def create_smoke_fixtures(work_dir: Path) -> dict[str, Path]:
    torch = import_torch()
    try:
        from PIL import Image
    except Exception as exc:  # pragma: no cover - environment specific.
        raise ValidationError(f"PIL is required for image smoke fixtures: {exc}") from exc

    work_dir.mkdir(parents=True, exist_ok=True)
    image_path = work_dir / "tiny.png"
    latent_path = work_dir / "latent-384.pt"
    text_feature_path = work_dir / "text-feature.pt"
    image_jsonl = work_dir / "image_text.jsonl"
    video_jsonl = work_dir / "video_text.jsonl"

    Image.new("RGB", (16, 16), color=(32, 64, 96)).save(image_path)
    torch.save(torch.zeros(1, 16, 2, 48, 80), latent_path)
    torch.save(
        {
            "prompt_embed": torch.zeros(1, 2, 4),
            "prompt_attention_mask": torch.ones(1, 2),
            "pooled_prompt_embed": torch.zeros(1, 4),
        },
        text_feature_path,
    )
    write_jsonl(image_jsonl, [{"image": str(image_path.resolve()), "text": "tiny image prompt"}])
    write_jsonl(
        video_jsonl,
        [
            {
                "video": str((work_dir / "not-needed-for-latent-loader.mp4").resolve()),
                "text": "tiny video prompt",
                "latent": str(latent_path.resolve()),
                "text_fea": str(text_feature_path.resolve()),
            }
        ],
    )
    return {
        "work_dir": work_dir,
        "image": image_path,
        "latent": latent_path,
        "text_feature": text_feature_path,
        "image_jsonl": image_jsonl,
        "video_jsonl": video_jsonl,
    }


def exercise_dataset_loaders(fixtures: dict[str, Path], repo_root: str) -> dict[str, Any]:
    if repo_root:
        repo_path = str(Path(repo_root))
        if repo_path not in sys.path:
            sys.path.insert(0, repo_path)
    try:
        from dataset.dataset_cls import ImageTextDataset, LengthGroupedVideoTextDataset
    except Exception as exc:
        raise ValidationError(f"could not import Pyramid-Flow dataset loaders: {exc}") from exc

    image_dataset = ImageTextDataset(
        str(fixtures["image_jsonl"]),
        add_normalize=False,
        ratios=[1.0],
        sizes=[(16, 16)],
        crop_mode="center",
    )
    image_item = image_dataset[0]
    image_keys = sorted(image_item.keys())
    if image_keys != ["identifier", "text", "video"]:
        raise ValidationError(f"ImageTextDataset returned keys {image_keys}; expected identifier, text, video")
    image_shape = shape_of(image_item["video"])
    if image_shape != (3, 16, 16):
        raise ValidationError(f"ImageTextDataset video shape is {image_shape}; expected (3, 16, 16)")

    video_dataset = LengthGroupedVideoTextDataset(
        str(fixtures["video_jsonl"]),
        max_frames=16,
        resolution="384p",
        load_vae_latent=True,
        load_text_fea=True,
    )
    video_item = video_dataset[0]
    video_keys = sorted(video_item.keys())
    expected_video_keys = ["identifier", "pooled_prompt_embed", "prompt_attention_mask", "prompt_embed", "video"]
    if video_keys != expected_video_keys:
        raise ValidationError(f"LengthGroupedVideoTextDataset returned keys {video_keys}; expected {expected_video_keys}")
    video_shape = shape_of(video_item["video"])
    if video_shape != (1, 16, 2, 48, 80):
        raise ValidationError(f"video latent item shape is {video_shape}; expected (1, 16, 2, 48, 80)")

    return {
        "image_loader_keys": image_keys,
        "image_video_shape": list(image_shape),
        "video_loader_keys": video_keys,
        "video_latent_shape": list(video_shape),
    }


def run_smoke_fixtures(args: argparse.Namespace) -> dict[str, Any]:
    cleanup = False
    if args.work_dir:
        work_dir = Path(args.work_dir)
        work_dir.mkdir(parents=True, exist_ok=True)
    else:
        work_dir = Path(tempfile.mkdtemp(prefix="pyramid-flow-data-fixtures-"))
        cleanup = True
    fixture_dir = work_dir / "fixtures"
    if fixture_dir.exists():
        shutil.rmtree(fixture_dir)
    try:
        fixtures = create_smoke_fixtures(fixture_dir)
        image_summary = validate_jsonl(
            argparse.Namespace(
                annotation=str(fixtures["image_jsonl"]),
                base_dir=None,
                kind="image-text",
                limit=10,
                check_paths=True,
                validate_artifacts=False,
                resolution="384p",
            )
        )
        video_summary = validate_jsonl(
            argparse.Namespace(
                annotation=str(fixtures["video_jsonl"]),
                base_dir=None,
                kind="video-training",
                limit=10,
                check_paths=False,
                validate_artifacts=True,
                resolution="384p",
            )
        )
        latent_summary = validate_latent_path(fixtures["latent"], "384p", None, None)
        text_summary = validate_text_feature_path(fixtures["text_feature"])
        result: dict[str, Any] = {
            "fixtures": {name: str(path) for name, path in fixtures.items()},
            "image_jsonl": image_summary,
            "video_jsonl": video_summary,
            "latent": latent_summary,
            "text_feature": text_summary,
        }
        if args.exercise_loaders:
            result["dataset_loaders"] = exercise_dataset_loaders(fixtures, args.repo_root)
        return result
    finally:
        if cleanup and not args.keep:
            shutil.rmtree(work_dir, ignore_errors=True)
        elif not args.keep and args.work_dir and fixture_dir.exists():
            shutil.rmtree(fixture_dir, ignore_errors=True)


def check_imports(args: argparse.Namespace) -> dict[str, Any]:
    modules = args.modules or DEFAULT_IMPORT_MODULES
    versions: dict[str, str] = {}
    for module_name in modules:
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:
            raise ValidationError(f"could not import {module_name}: {exc}") from exc
        versions[module_name] = str(getattr(module, "__version__", "import-ok"))
    return {"imports": versions}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    imports = subparsers.add_parser("check-imports", help="Check data/precompute helper imports.")
    imports.add_argument("--modules", nargs="*", help="Override the default module list.")

    jsonl = subparsers.add_parser("validate-jsonl", help="Validate JSONL rows for a Pyramid-Flow data stage.")
    jsonl.add_argument("--annotation", required=True, help="JSONL annotation file to inspect.")
    jsonl.add_argument("--kind", choices=sorted(KIND_REQUIRED_FIELDS), required=True, help="Annotation stage kind.")
    jsonl.add_argument("--limit", type=int, default=100, help="Maximum non-empty rows to inspect.")
    jsonl.add_argument("--base-dir", help="Base directory for relative path checks; defaults to annotation parent.")
    jsonl.add_argument("--check-paths", action="store_true", help="Require non-text path fields to exist.")
    jsonl.add_argument("--validate-artifacts", action="store_true", help="Load latent/text_fea artifacts referenced by rows.")
    jsonl.add_argument("--resolution", choices=("384p", "768p"), default="384p", help="Expected latent resolution when validating artifacts.")

    latent = subparsers.add_parser("validate-latent", help="Validate one VAE latent .pt tensor shape.")
    latent.add_argument("--path", required=True, help="Latent .pt file to load.")
    latent.add_argument("--resolution", choices=("384p", "768p", "custom"), default="384p")
    latent.add_argument("--expected-latent-height", type=int, help="Required for --resolution custom.")
    latent.add_argument("--expected-latent-width", type=int, help="Required for --resolution custom.")

    text_feature = subparsers.add_parser("validate-text-feature", help="Validate one text feature .pt dictionary.")
    text_feature.add_argument("--path", required=True, help="Text feature .pt file to load.")

    smoke = subparsers.add_parser("smoke-fixtures", help="Create and validate tiny synthetic fixtures.")
    smoke.add_argument("--work-dir", help="Directory in which to create a temporary fixtures/ subtree.")
    smoke.add_argument("--keep", action="store_true", help="Keep generated fixture files instead of deleting them.")
    smoke.add_argument("--exercise-loaders", action="store_true", help="Import and exercise Pyramid-Flow dataset loaders.")
    smoke.add_argument("--repo-root", default=".", help="Repo root to add to sys.path for --exercise-loaders.")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "check-imports":
            result = check_imports(args)
        elif args.command == "validate-jsonl":
            result = validate_jsonl(args)
        elif args.command == "validate-latent":
            result = validate_latent_path(
                Path(args.path),
                args.resolution,
                args.expected_latent_height,
                args.expected_latent_width,
            )
        elif args.command == "validate-text-feature":
            result = validate_text_feature_path(Path(args.path))
        elif args.command == "smoke-fixtures":
            result = run_smoke_fixtures(args)
        else:  # pragma: no cover - argparse prevents this.
            raise ValidationError(f"unknown command: {args.command}")
        print(json.dumps({"ok": True, **result}, indent=2))
        return 0
    except ValidationError as exc:
        print(f"VALIDATION FAILED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
