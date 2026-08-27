#!/usr/bin/env python3
"""Preview or validate VGen text-to-video dataset and prompt lists.

This helper replaces the repo's stale dataset smoke helpers with a safer script
that can validate list formats without deleting outputs and can optionally
render a tiny preview from a VGen checkout.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

try:
    import yaml
except Exception as exc:  # pragma: no cover - help path only
    yaml = None
    YAML_IMPORT_ERROR = exc
else:
    YAML_IMPORT_ERROR = None


DELIM = "|||"


@dataclass
class Problem:
    line_no: int
    message: str
    line: str


@dataclass
class ListReport:
    path: Path
    active: int
    comments: int
    blanks: int
    problems: List[Problem]


@dataclass
class PreviewSample:
    index: int
    caption: str
    frame_count: int
    output_path: Optional[Path]
    note: str


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate or preview VGen text-to-video dataset and prompt lists.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--config",
        required=True,
        type=Path,
        help="Path to a VGen YAML config file.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path('.'),
        help="VGen checkout root used to resolve relative paths.",
    )
    parser.add_argument(
        "--split",
        choices=["auto", "vid", "img", "prompt", "vcomposer"],
        default="auto",
        help="Select which data surface to inspect.",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=2,
        help="Maximum number of samples to render when --render is set.",
    )
    parser.add_argument(
        "--render",
        action="store_true",
        help="Render a tiny preview using the repo datasets and save it under a scratch workspace.",
    )
    parser.add_argument(
        "--no-render",
        action="store_true",
        help="Validate only; do not import torch or render previews.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on malformed or missing inputs instead of only warning.",
    )
    parser.add_argument(
        "--check-exists",
        action="store_true",
        help="When validating list files, verify that referenced media files exist.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional preview output directory. Defaults to a scratch workspace under the repo root.",
    )
    return parser.parse_args(argv)


def load_yaml_with_bases(config_path: Path) -> Dict[str, object]:
    if yaml is None:
        raise RuntimeError(f"PyYAML is required to read {config_path}: {YAML_IMPORT_ERROR}")

    def _load(path: Path) -> Dict[str, object]:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        merged: Dict[str, object] = {}
        for base_key in ("_BASE", "_BASE_RUN", "_BASE_MODEL"):
            base_value = data.get(base_key)
            if not base_value:
                continue
            base_path = (path.parent / base_value).resolve() if not str(base_value).startswith("/") else Path(base_value)
            if base_path.exists():
                merged.update(_load(base_path))
        for key, value in data.items():
            if key in {"_BASE", "_BASE_RUN", "_BASE_MODEL"}:
                continue
            merged[key] = value
        return merged

    return _load(config_path.resolve())


def merge_into(dst: Dict[str, object], src: Dict[str, object]) -> Dict[str, object]:
    for key, value in src.items():
        if isinstance(value, dict) and isinstance(dst.get(key), dict):
            merge_into(dst[key], value)  # type: ignore[index]
        else:
            dst[key] = value
    return dst


def truncate(text: str, limit: int = 140) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def detect_kind(cfg: Dict[str, object], split: str) -> str:
    if split != "auto":
        return split

    task = str(cfg.get("TASK_TYPE", "")).lower()
    cfg_file = str(cfg.get("cfg_file", "")).lower()
    if "vcomposer" in cfg_file or "vcomposer" in task:
        return "vcomposer"
    if "tft2v" in cfg_file or "videolcm" in cfg_file:
        return "vcomposer" if "vcomposer" in cfg_file else "prompt"
    if "higen" in cfg_file or "higen" in task or "sr600" in cfg_file or "sr600" in task:
        return "prompt-or-seed"
    if "train" in cfg_file:
        return "vid"
    if task.startswith("inference_") or task.startswith("train_"):
        if "i2v" in task:
            return "image-caption"
    return "prompt"


def validate_lines(path: Path, *, kind: str, check_exists: bool = False, root: Path = Path(".")) -> ListReport:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return ListReport(path, 0, 0, 0, [Problem(0, f"unable to read list file: {exc}", str(path))])

    active = comments = blanks = 0
    problems: List[Problem] = []

    for line_no, raw_line in enumerate(lines, start=1):
        stripped = raw_line.strip()
        if not stripped:
            blanks += 1
            problems.append(Problem(line_no, "blank lines are not ignored by the source loaders", raw_line))
            continue
        if stripped.startswith("#"):
            comments += 1
            continue

        active += 1
        if kind == "prompt":
            if DELIM in stripped:
                problems.append(Problem(line_no, f"prompt-only lists must not contain {DELIM!r}", raw_line))
            continue

        if kind in {"vid", "img", "image-caption", "vcomposer"}:
            if stripped.count(DELIM) != 1:
                problems.append(Problem(line_no, f"expected exactly one {DELIM!r} delimiter", raw_line))
                continue
            left, right = stripped.split(DELIM)
            if not left or not right:
                problems.append(Problem(line_no, "both path and caption must be non-empty", raw_line))
                continue
            if check_exists:
                candidate = Path(left)
                if not candidate.is_absolute():
                    candidate = root / candidate
                if not candidate.exists():
                    problems.append(Problem(line_no, f"referenced file does not exist: {left}", raw_line))
                elif not candidate.is_file():
                    problems.append(Problem(line_no, f"referenced path is not a regular file: {left}", raw_line))
            continue

        if kind == "prompt-or-seed":
            parts = stripped.split("|")
            if len(parts) not in {1, 2}:
                problems.append(Problem(line_no, "expected 'caption' or 'caption|seed' format", raw_line))
            continue

    return ListReport(path, active, comments, blanks, problems)


def build_preview_dataset(repo_root: Path, cfg: Dict[str, object], kind: str, max_items: int, output_dir: Path) -> List[PreviewSample]:
    try:
        import torch
        import imageio
        import numpy as np
        from PIL import Image, ImageDraw, ImageFont
        import torchvision.transforms as T
        import utils.transforms as data
        from tools.modules.config import cfg as global_cfg
        from utils.registry_class import DATASETS
        import tools  # noqa: F401 - importing registers repo datasets
    except Exception as exc:
        raise RuntimeError(f"rendering requires the VGen runtime stack and dataset registries: {exc}") from exc

    merge_into(global_cfg, cfg)
    cfg_obj = global_cfg

    if kind == "img":
        dataset_cfg = cfg_obj.img_dataset
        dataset_kwargs = {"transforms": None, "vit_transforms": None}
        if cfg_obj.resolution[0] > cfg_obj.vit_resolution[0]:
            crop_size = (cfg_obj.resolution[0], cfg_obj.resolution[0])
        else:
            crop_size = cfg_obj.vit_resolution
        train_trans = data.Compose([
            data.CenterCropWide(size=cfg_obj.resolution),
            data.ToTensor(),
            data.Normalize(mean=cfg_obj.mean, std=cfg_obj.std),
        ])
        vit_trans = data.Compose([
            data.CenterCropWide(size=crop_size),
            data.Resize(cfg_obj.vit_resolution),
            data.ToTensor(),
            data.Normalize(mean=cfg_obj.vit_mean, std=cfg_obj.vit_std),
        ])
        dataset_kwargs = {"transforms": train_trans, "vit_transforms": vit_trans}
    else:
        dataset_cfg = cfg_obj.vid_dataset
        train_trans = data.Compose([
            data.CenterCropWide(size=cfg_obj.resolution),
            data.ToTensor(),
            data.Normalize(mean=cfg_obj.mean, std=cfg_obj.std),
        ])
        vit_trans = data.Compose([
            data.CenterCropWide(size=(cfg_obj.resolution[0], cfg_obj.resolution[0])),
            data.Resize(cfg_obj.vit_resolution),
            data.ToTensor(),
            data.Normalize(mean=cfg_obj.vit_mean, std=cfg_obj.vit_std),
        ])
        dataset_kwargs = {
            "transforms": train_trans,
            "vit_transforms": vit_trans,
            "sample_fps": cfg_obj.sample_fps[0] if isinstance(cfg_obj.sample_fps, (list, tuple)) else cfg_obj.sample_fps,
        }

    dataset = DATASETS.build(dataset_cfg, max_frames=cfg_obj.max_frames if hasattr(cfg_obj, 'max_frames') else 1, **dataset_kwargs)
    output_dir.mkdir(parents=True, exist_ok=True)
    samples: List[PreviewSample] = []
    txt_size = int(cfg_obj.resolution[1])
    nc = max(1, int(38 * (txt_size / 256)))
    font_path = repo_root / "data" / "font" / "DejaVuSans.ttf"
    font = ImageFont.truetype(str(font_path), size=13) if font_path.exists() else ImageFont.load_default()

    video_mean = torch.tensor(cfg_obj.mean).view(1, -1, 1, 1)
    video_std = torch.tensor(cfg_obj.std).view(1, -1, 1, 1)
    img_mean = torch.tensor(cfg_obj.mean).view(-1, 1, 1)
    img_std = torch.tensor(cfg_obj.std).view(-1, 1, 1)

    for idx, item in enumerate(dataset):
        if idx >= max_items:
            break
        output_path: Optional[Path] = None
        note = "preview-only"
        try:
            ref_frame = item[0]
            vit_frame = item[1]
            video_data = item[2]
            caption = str(item[3]) if len(item) > 3 else ""
        except Exception:
            samples.append(PreviewSample(idx, "unreadable item", 0, None, "dataset item shape did not match the bundled preview logic"))
            continue

        frame_count = int(video_data.shape[0]) if hasattr(video_data, "shape") else 1
        if frame_count > 0:
            if video_data.ndim == 4:
                vis = video_data.mul(video_std).add(video_mean).clamp_(0, 1).permute(0, 2, 3, 1)
                vis_frames = [(frame.cpu().numpy() * 255).astype("uint8") for frame in vis]
            else:
                vis_frames = []
        else:
            vis_frames = []

        if vis_frames:
            ref = ref_frame.mul(img_std).add(img_mean).clamp_(0, 1).permute(1, 2, 0)
            ref_np = (ref.cpu().numpy() * 255).astype("uint8")
            txt_img = Image.new("RGB", (txt_size, txt_size), color="white")
            draw = ImageDraw.Draw(txt_img)
            lines = "\n".join(caption[start : start + nc] for start in range(0, len(caption), nc))
            draw.text((0, 0), lines, fill="black", font=font)
            text_np = np.array(txt_img)
            preview_frames = [np.concatenate([ref_np, frame, text_np], axis=1) for frame in vis_frames[:min(len(vis_frames), 8)]]
            output_path = output_dir / f"{idx:04d}.gif"
            imageio.mimwrite(output_path, preview_frames, fps=8)
            note = f"wrote {len(preview_frames)} frame(s)"
        samples.append(PreviewSample(idx, truncate(caption, 80), frame_count, output_path, note))

    return samples


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    config_path = args.config if args.config.is_absolute() else (repo_root / args.config)
    cfg = load_yaml_with_bases(config_path)
    cfg["cfg_file"] = str(config_path)
    cfg["TASK_TYPE"] = str(cfg.get("TASK_TYPE", ""))

    kind = detect_kind(cfg, args.split)

    if kind == "prompt":
        list_path = Path(cfg.get("test_list_path", ""))
    elif kind in {"vid", "img"}:
        list_path = Path(cfg.get("vid_dataset", {}).get("data_list", [""])[0] if kind == "vid" else cfg.get("img_dataset", {}).get("data_list", [""])[0])
    else:
        list_path = Path(cfg.get("test_list_path", ""))

    if not list_path:
        print(f"ERROR: unable to determine list path from {config_path}", file=sys.stderr)
        return 1
    if not list_path.is_absolute():
        list_path = repo_root / list_path

    if kind == "vcomposer":
        validated_kind = "vcomposer"
    elif kind == "img":
        validated_kind = "img"
    elif kind == "vid":
        validated_kind = "vid"
    else:
        task = str(cfg.get("TASK_TYPE", "")).lower()
        validated_kind = "prompt-or-seed" if ("higen" in task or "sr600" in task) else "prompt"

    report = validate_lines(list_path, kind=validated_kind, check_exists=args.check_exists, root=repo_root)
    if report.problems:
        print(f"ERROR: {report.path}", file=sys.stderr)
        for problem in report.problems:
            print(f"line {problem.line_no}: {problem.message}\n  {truncate(problem.line)}", file=sys.stderr)
        print(
            f"Summary: {report.active} active, {report.comments} comment, {report.blanks} blank line(s)",
            file=sys.stderr,
        )
        if args.strict:
            return 1
    else:
        print(
            f"OK: {report.path} — {report.active} active, {report.comments} comment, {report.blanks} blank line(s)",
        )

    if args.no_render or not args.render:
        return 1 if report.problems and args.strict else 0

    output_dir = args.output_dir if args.output_dir is not None else repo_root / "workspace" / "skill_previews" / config_path.stem
    if not output_dir.is_absolute():
        output_dir = repo_root / output_dir

    try:
        samples = build_preview_dataset(repo_root, cfg, kind if kind != "auto" else validated_kind, max(1, args.max_items), output_dir)
    except Exception as exc:
        print(f"ERROR: preview render failed: {exc}", file=sys.stderr)
        return 1

    for sample in samples:
        print(f"sample {sample.index}: frames={sample.frame_count} caption={truncate(sample.caption, 60)} note={sample.note} path={sample.output_path}")

    return 0 if not report.problems or not args.strict else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
