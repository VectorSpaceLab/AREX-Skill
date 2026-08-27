#!/usr/bin/env python3
"""Create tiny DeepLabCut-style projects for data-format checks.

The generated project contains config.yaml, labeled PNG frames, a small synthetic
video, and CollectedData_<scorer>.h5/.csv annotation files. It performs no
training, downloads, GUI actions, or DeepLabCut imports.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

np = None
pd = None
Image = None
ImageDraw = None


@dataclass(frozen=True)
class ProjectSpec:
    mode: str
    frames: int
    width: int
    height: int
    bodyparts: int
    individuals: int
    unique_bodyparts: int
    scorer: str
    task: str
    seed: int
    video_name: str


def import_required_dependencies() -> None:
    """Import third-party dependencies only after argparse has handled --help."""
    global np, pd, Image, ImageDraw
    try:
        import numpy as _np
        import pandas as _pd
        from PIL import Image as _Image
        from PIL import ImageDraw as _ImageDraw
    except ImportError as exc:  # pragma: no cover - environment-specific message
        raise SystemExit(
            "create_tiny_dlc_project.py requires numpy, pandas, and pillow. "
            "Run it inside a DeepLabCut-compatible Python environment. "
            f"Missing dependency: {exc.name or exc}"
        ) from exc

    np = _np
    pd = _pd
    Image = _Image
    ImageDraw = _ImageDraw


def choose_names(prefix: str, count: int, preferred: list[str]) -> list[str]:
    if count <= len(preferred):
        return preferred[:count]
    return preferred + [f"{prefix}_{i}" for i in range(len(preferred), count)]


def bodypart_names(count: int) -> list[str]:
    return choose_names(
        "bodypart",
        count,
        ["nose", "left_ear", "right_ear", "tailbase", "left_paw", "right_paw", "spine", "tailtip"],
    )


def unique_names(count: int) -> list[str]:
    return choose_names("unique", count, ["arena_corner", "object_center", "perch"])


def individual_names(count: int) -> list[str]:
    return [f"animal_{i}" for i in range(count)]


def bounded_coord(raw: float, limit: int, margin: int = 8) -> float:
    usable = max(1, limit - 2 * margin)
    return float(margin + (int(round(raw)) % usable))


def build_columns(spec: ProjectSpec) -> tuple[list[tuple[str, ...]], list[str], list[str], list[str]]:
    bpts = bodypart_names(spec.bodyparts)
    uniques = unique_names(spec.unique_bodyparts if spec.mode == "multianimal" else 0)
    individuals = individual_names(spec.individuals if spec.mode == "multianimal" else 1)

    columns: list[tuple[str, ...]] = []
    if spec.mode == "standard":
        for bodypart in bpts:
            columns.extend([(spec.scorer, bodypart, "x"), (spec.scorer, bodypart, "y")])
    else:
        for individual in individuals:
            for bodypart in bpts:
                columns.extend(
                    [
                        (spec.scorer, individual, bodypart, "x"),
                        (spec.scorer, individual, bodypart, "y"),
                    ]
                )
        for bodypart in uniques:
            columns.extend(
                [
                    (spec.scorer, "single", bodypart, "x"),
                    (spec.scorer, "single", bodypart, "y"),
                ]
            )
    return columns, bpts, individuals, uniques


def generate_pose_matrix(spec: ProjectSpec, columns: list[tuple[str, ...]]) -> Any:
    rng = np.random.default_rng(spec.seed)
    values = np.empty((spec.frames, len(columns)), dtype=float)
    values[:] = np.nan

    if spec.mode == "standard":
        for frame_idx in range(spec.frames):
            for bpt_idx in range(spec.bodyparts):
                col = 2 * bpt_idx
                x = bounded_coord(12 + frame_idx * 5 + bpt_idx * 13, spec.width)
                y = bounded_coord(14 + frame_idx * 3 + bpt_idx * 9, spec.height)
                values[frame_idx, col] = x
                values[frame_idx, col + 1] = y
        if spec.frames >= 4 and spec.bodyparts >= 2:
            values[1, 2:4] = np.nan  # one occluded point
        if spec.frames >= 6:
            values[spec.frames // 2, :] = np.nan  # an unlabeled frame
        return values

    col = 0
    base_radius = max(5, min(spec.width, spec.height) // 12)
    for individual_idx in range(spec.individuals):
        angle = 2 * math.pi * individual_idx / max(1, spec.individuals)
        base_x = spec.width / 2 + math.cos(angle) * spec.width / 4
        base_y = spec.height / 2 + math.sin(angle) * spec.height / 4
        for bpt_idx in range(spec.bodyparts):
            dx = (bpt_idx - (spec.bodyparts - 1) / 2) * base_radius
            dy = ((bpt_idx % 2) - 0.5) * base_radius
            for frame_idx in range(spec.frames):
                jitter_x = rng.integers(-2, 3) + frame_idx * (individual_idx + 1)
                jitter_y = rng.integers(-2, 3) + frame_idx
                values[frame_idx, col] = bounded_coord(base_x + dx + jitter_x, spec.width)
                values[frame_idx, col + 1] = bounded_coord(base_y + dy + jitter_y, spec.height)
            col += 2

    for unique_idx in range(spec.unique_bodyparts):
        for frame_idx in range(spec.frames):
            values[frame_idx, col] = bounded_coord(10 + unique_idx * 19 + frame_idx, spec.width)
            values[frame_idx, col + 1] = bounded_coord(10 + unique_idx * 11, spec.height)
        col += 2

    if spec.frames >= 4 and spec.bodyparts >= 1:
        values[1, 0 : 2 * spec.bodyparts] = np.nan  # one animal absent/occluded
    if spec.frames >= 6:
        values[spec.frames // 2, :] = np.nan  # one fully unlabeled frame
    if spec.unique_bodyparts and spec.frames >= 3:
        values[-1, -2:] = np.nan  # missing unique bodypart on final frame
    return values


def make_dataframe(project_root: Path, spec: ProjectSpec, video_name: str) -> tuple[Any, list[tuple[str, ...]]]:
    columns, _bpts, _individuals, _uniques = build_columns(spec)
    index = pd.MultiIndex.from_tuples(
        [("labeled-data", video_name, f"img{idx:04d}.png") for idx in range(spec.frames)]
    )
    column_names = ["scorer", "bodyparts", "coords"] if spec.mode == "standard" else [
        "scorer",
        "individuals",
        "bodyparts",
        "coords",
    ]
    df = pd.DataFrame(
        generate_pose_matrix(spec, columns),
        index=index,
        columns=pd.MultiIndex.from_tuples(columns, names=column_names),
    )
    return df, columns


def color_for_column(column: tuple[str, ...], idx: int) -> tuple[int, int, int]:
    palette = [
        (230, 57, 70),
        (29, 53, 87),
        (42, 157, 143),
        (233, 196, 106),
        (244, 162, 97),
        (131, 56, 236),
        (255, 0, 110),
        (58, 134, 255),
    ]
    return palette[idx % len(palette)]


def draw_frame(project_root: Path, row: Any, columns: list[tuple[str, ...]], width: int, height: int) -> None:
    image = Image.new("RGB", (width, height), color=(12, 12, 16))
    draw = ImageDraw.Draw(image)

    # Faint grid helps humans spot coordinate flips in check-label renders.
    for x in range(0, width, max(8, width // 6)):
        draw.line((x, 0, x, height), fill=(24, 24, 30))
    for y in range(0, height, max(8, height // 6)):
        draw.line((0, y, width, y), fill=(24, 24, 30))

    values = row.to_numpy(dtype=float)
    for pair_idx in range(0, len(values), 2):
        x, y = values[pair_idx], values[pair_idx + 1]
        if np.isnan(x) or np.isnan(y):
            continue
        radius = 3
        color = color_for_column(columns[pair_idx], pair_idx // 2)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)

    image_path = project_root / Path(*row.name)
    image_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(image_path)


def write_video(image_paths: list[Path], output_path: Path, fps: int = 5) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not image_paths:
        raise RuntimeError("No images were generated, so no video can be written.")

    first = Image.open(image_paths[0]).convert("RGB")
    width, height = first.size

    try:
        import cv2  # type: ignore

        fourcc = cv2.VideoWriter_fourcc(*"MJPG")
        writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
        if writer.isOpened():
            for path in image_paths:
                frame = np.asarray(Image.open(path).convert("RGB"))[:, :, ::-1]
                writer.write(frame)
            writer.release()
            return
        writer.release()
    except Exception:
        pass

    try:
        import imageio.v2 as imageio  # type: ignore

        with imageio.get_writer(str(output_path), fps=fps) as writer:
            for path in image_paths:
                writer.append_data(np.asarray(Image.open(path).convert("RGB")))
        return
    except Exception as exc:  # pragma: no cover - depends on optional codecs
        raise RuntimeError(
            "Could not write the synthetic video. Install OpenCV or imageio with a working video codec."
        ) from exc


def yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value))


def fallback_yaml(data: Any, indent: int = 0) -> str:
    pad = " " * indent
    if isinstance(data, dict):
        lines: list[str] = []
        for key, value in data.items():
            key_text = json.dumps(str(key)) if any(ch in str(key) for ch in [":", "#", "{", "}", "[", "]"]) else str(key)
            if isinstance(value, (dict, list)) and value:
                lines.append(f"{pad}{key_text}:")
                lines.append(fallback_yaml(value, indent + 2))
            elif isinstance(value, list) and not value:
                lines.append(f"{pad}{key_text}: []")
            elif isinstance(value, dict) and not value:
                lines.append(f"{pad}{key_text}: {{}}")
            else:
                lines.append(f"{pad}{key_text}: {yaml_scalar(value)}")
        return "\n".join(lines)
    if isinstance(data, list):
        lines = []
        for item in data:
            if isinstance(item, (dict, list)):
                lines.append(f"{pad}-")
                lines.append(fallback_yaml(item, indent + 2))
            else:
                lines.append(f"{pad}- {yaml_scalar(item)}")
        return "\n".join(lines)
    return f"{pad}{yaml_scalar(data)}"


def write_config(config_path: Path, config: dict[str, Any]) -> None:
    try:
        import yaml  # type: ignore

        text = yaml.safe_dump(config, sort_keys=False)
    except Exception:
        text = fallback_yaml(config) + "\n"
    config_path.write_text(text, encoding="utf-8")


def create_project(project_root: Path, spec: ProjectSpec) -> dict[str, Path]:
    if spec.mode not in {"standard", "multianimal"}:
        raise ValueError(f"Unsupported project mode: {spec.mode}")

    video_name = spec.video_name
    project_root.mkdir(parents=True, exist_ok=False)
    df, columns = make_dataframe(project_root, spec, video_name)

    label_dir = project_root / "labeled-data" / video_name
    label_dir.mkdir(parents=True, exist_ok=True)
    image_paths: list[Path] = []
    for _, row in df.iterrows():
        draw_frame(project_root, row, columns, spec.width, spec.height)
        image_paths.append(project_root / Path(*row.name))

    h5_path = label_dir / f"CollectedData_{spec.scorer}.h5"
    csv_path = label_dir / f"CollectedData_{spec.scorer}.csv"
    try:
        df.to_hdf(h5_path, key="df_with_missing", mode="w")
    except Exception as exc:  # pragma: no cover - depends on pandas HDF installation
        raise RuntimeError(
            "Could not write HDF labels. Pandas HDF support, typically PyTables, is required."
        ) from exc
    df.to_csv(csv_path)

    video_path = project_root / "videos" / f"{video_name}.avi"
    write_video(image_paths, video_path)

    bpts = bodypart_names(spec.bodyparts)
    uniques = unique_names(spec.unique_bodyparts if spec.mode == "multianimal" else 0)
    individuals = individual_names(spec.individuals if spec.mode == "multianimal" else 1)
    config: dict[str, Any] = {
        "Task": spec.task,
        "scorer": spec.scorer,
        "date": "Jan01",
        "project_path": str(project_root.resolve()),
        "video_sets": {str(video_path.resolve()): {"crop": f"0, {spec.width}, 0, {spec.height}"}},
        "TrainingFraction": [0.8],
        "iteration": 0,
        "engine": "pytorch",
        "default_net_type": "resnet_50",
        "default_augmenter": "albumentations",
        "default_track_method": "ellipse",
        "snapshotindex": "all",
        "batch_size": 1,
        "pcutoff": 0.6,
        "dotsize": 4,
        "alphavalue": 0.7,
        "colormap": "rainbow",
        "skeleton": [],
        "skeleton_color": "black",
        "start": 0,
        "stop": 1,
        "numframes2pick": min(5, spec.frames),
    }
    if spec.mode == "standard":
        config.update({"multianimalproject": False, "bodyparts": bpts})
    else:
        config.update(
            {
                "multianimalproject": True,
                "identity": False,
                "bodyparts": "MULTI!",
                "individuals": individuals,
                "multianimalbodyparts": bpts,
                "uniquebodyparts": uniques,
            }
        )

    config_path = project_root / "config.yaml"
    write_config(config_path, config)
    return {"config": config_path, "h5": h5_path, "csv": csv_path, "video": video_path}


def validate_args(args: argparse.Namespace) -> None:
    if args.frames < 3:
        raise SystemExit("--frames must be at least 3 so the fixture includes missing-label cases.")
    if args.width < 32 or args.height < 32:
        raise SystemExit("--width and --height must both be at least 32 pixels.")
    if args.bodyparts < 1:
        raise SystemExit("--bodyparts must be at least 1.")
    if args.individuals < 1:
        raise SystemExit("--individuals must be at least 1.")
    if args.unique_bodyparts < 0:
        raise SystemExit("--unique-bodyparts cannot be negative.")


def prepare_output(path: Path, force: bool) -> None:
    resolved = path.resolve()
    if resolved == resolved.parent:
        raise SystemExit("Refusing to create or delete the filesystem root.")
    if path.exists():
        if not force:
            raise SystemExit(f"Output exists: {path}. Use --force to replace it.")
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create tiny standard or multi-animal DeepLabCut-style fixture projects."
    )
    parser.add_argument("output", type=Path, help="Output project directory, or container directory for --mode both.")
    parser.add_argument("--mode", choices=["standard", "multianimal", "both"], default="standard")
    parser.add_argument("--force", action="store_true", help="Replace output if it already exists.")
    parser.add_argument("--frames", type=int, default=8, help="Number of labeled images per project.")
    parser.add_argument("--width", type=int, default=96, help="Synthetic image/video width in pixels.")
    parser.add_argument("--height", type=int, default=72, help="Synthetic image/video height in pixels.")
    parser.add_argument("--bodyparts", type=int, default=4, help="Number of standard or multi-animal bodyparts.")
    parser.add_argument("--individuals", type=int, default=2, help="Number of individuals for multi-animal fixtures.")
    parser.add_argument("--unique-bodyparts", type=int, default=1, help="Number of unique bodyparts for multi-animal fixtures.")
    parser.add_argument("--scorer", default="synthetic", help="Scorer/annotator name to write in labels and config.")
    parser.add_argument("--task", default="TinyDLCData", help="Task name prefix for generated config files.")
    parser.add_argument("--seed", type=int, default=0, help="Random seed for small coordinate jitter.")
    parser.add_argument("--video-name", default="tiny_video", help="Video stem and labeled-data folder name.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    validate_args(args)
    import_required_dependencies()
    prepare_output(args.output, args.force)

    modes = ["standard", "multianimal"] if args.mode == "both" else [args.mode]
    created: list[dict[str, str]] = []
    for mode in modes:
        project_root = args.output / mode if args.mode == "both" else args.output
        suffix = "Standard" if mode == "standard" else "MultiAnimal"
        spec = ProjectSpec(
            mode=mode,
            frames=args.frames,
            width=args.width,
            height=args.height,
            bodyparts=args.bodyparts,
            individuals=args.individuals,
            unique_bodyparts=args.unique_bodyparts,
            scorer=args.scorer,
            task=f"{args.task}{suffix}" if args.mode == "both" else args.task,
            seed=args.seed + (0 if mode == "standard" else 1000),
            video_name=args.video_name,
        )
        paths = create_project(project_root, spec)
        created.append({key: str(value) for key, value in paths.items()})

    print(json.dumps({"created": created}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
