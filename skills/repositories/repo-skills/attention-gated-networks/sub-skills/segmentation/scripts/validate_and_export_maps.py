#!/usr/bin/env python3
"""Validate a segmentation model or export 3D feature/attention maps.

This helper replaces the unsafe, hard-coded validation and visualization
scripts from the source repo. It supports two modes:

- validate: run a synthetic or fixture volume through a segmentation model,
  compute lightweight metrics, and write NIfTI outputs.
- maps: hook one or more internal layers, export their feature/attention maps
  as NIfTI volumes, and save a preview PNG for the middle slice.

Examples:
  python validate_and_export_maps.py \
    --repo-root /path/to/repo \
    --output-dir /tmp/ag-net-segmentation \
    --mode validate \
    --synthetic

  python validate_and_export_maps.py \
    --repo-root /path/to/repo \
    --config configs/config_unet_ct_multi_att_dsv.json \
    --output-dir /tmp/ag-net-maps \
    --mode maps \
    --synthetic
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
import torch
from skimage.transform import resize


def add_repo_root(repo_root: str | None) -> Path | None:
    if not repo_root:
        return None
    root = Path(repo_root).resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root


def resolve_config_path(path: str, repo_root: Path | None = None) -> Path:
    resolved = Path(path).expanduser()
    if resolved.is_absolute():
        return resolved.resolve()
    if repo_root is None:
        raise SystemExit("relative --config requires an explicit --repo-root")
    return (repo_root / resolved).resolve()


def to_namespace(value):
    if isinstance(value, dict):
        return SimpleNamespace(**{key: to_namespace(val) for key, val in value.items()})
    if isinstance(value, list):
        return [to_namespace(item) for item in value]
    return value


def load_model_config(repo_root: Path | None, config_path: str):
    resolved = resolve_config_path(config_path, repo_root)
    try:
        data = json.loads(resolved.read_text())
    except FileNotFoundError as exc:
        raise SystemExit(f"config not found: {resolved}") from exc
    model_cfg = to_namespace(data["model"])
    return model_cfg, data


def normalize01(array: np.ndarray) -> np.ndarray:
    array = array.astype(np.float32)
    lo = float(array.min())
    hi = float(array.max())
    if np.isclose(lo, hi):
        return np.zeros_like(array, dtype=np.float32)
    return (array - lo) / (hi - lo)


def load_volume(path: str | None, synthetic_shape: tuple[int, int, int], seed: int) -> np.ndarray:
    if path:
        volume = np.load(path).astype(np.float32)
        volume = np.squeeze(volume)
    else:
        rng = np.random.default_rng(seed)
        volume = rng.normal(size=synthetic_shape).astype(np.float32)
    if volume.ndim != 3:
        raise SystemExit(f"expected a 3D volume, got shape {volume.shape}")
    return volume


def quantized_labels(volume: np.ndarray, n_class: int) -> np.ndarray:
    if n_class <= 1:
        return np.zeros_like(volume, dtype=np.int16)
    lo = float(volume.min())
    hi = float(volume.max())
    if np.isclose(lo, hi):
        return np.zeros_like(volume, dtype=np.int16)
    bins = np.linspace(lo, hi, n_class + 1)[1:-1]
    return np.digitize(volume, bins, right=False).astype(np.int16)


def save_nifti(array: np.ndarray, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = nib.Nifti1Image(array.astype(np.float32), affine=np.eye(4, dtype=np.float32))
    nib.save(image, str(path))
    return path


def save_middle_slice_png(array: np.ndarray, path: Path, title: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    slice_index = array.shape[2] // 2
    preview = array[:, :, slice_index]
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(1, 1, 1)
    ax.imshow(normalize01(preview), cmap="magma")
    ax.set_axis_off()
    ax.set_title(title)
    fig.tight_layout(pad=0)
    fig.savefig(path, bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    return path


def prepare_segmentation_cfg(tmpdir: Path, model_cfg, args):
    model_cfg.checkpoints_dir = str(tmpdir)
    model_cfg.experiment_name = "segmentation-smoke"
    if args.checkpoint:
        model_cfg.isTrain = False
        model_cfg.path_pre_trained_model = str(Path(args.checkpoint).resolve())
        model_cfg.continue_train = False
    else:
        model_cfg.isTrain = True
        model_cfg.path_pre_trained_model = None
        model_cfg.continue_train = False
    return model_cfg


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", help="Repository root; relative --config paths are resolved from here")
    parser.add_argument(
        "--config",
        default="configs/config_unet_ct_multi_att_dsv.json",
        help="Segmentation config JSON relative to --repo-root unless absolute",
    )
    parser.add_argument("--checkpoint", help="Optional checkpoint path to load before running")
    parser.add_argument("--input-npy", help="Optional 3D NumPy volume for validation or map export")
    parser.add_argument("--synthetic", action="store_true", help="Use a generated synthetic volume when --input-npy is omitted")
    parser.add_argument("--label-npy", help="Optional 3D NumPy label volume for validation mode")
    parser.add_argument("--output-dir", required=True, help="Directory for metrics, NIfTI files, and previews")
    parser.add_argument(
        "--mode",
        choices=("validate", "maps", "both"),
        default="both",
        help="Run validation, map export, or both",
    )
    parser.add_argument(
        "--layers",
        nargs="+",
        default=["attentionblock2", "attentionblock3", "attentionblock4", "center"],
        help="Layers to export when --mode includes maps",
    )
    parser.add_argument(
        "--synthetic-shape",
        nargs=3,
        type=int,
        metavar=("D", "H", "W"),
        default=[16, 16, 16],
        help="Synthetic volume size used when --input-npy is omitted",
    )
    parser.add_argument("--seed", type=int, default=13, help="Random seed for synthetic input")
    return parser.parse_args()


def run_validate(model, volume: np.ndarray, output_dir: Path, output_nc: int, label_path: str | None) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    if label_path:
        label = np.load(label_path).astype(np.int16)
        label = np.squeeze(label)
    else:
        label = quantized_labels(volume, output_nc)

    if label.shape != volume.shape:
        raise SystemExit(f"label shape {label.shape} does not match input volume shape {volume.shape}")

    tensor = torch.from_numpy(volume).float().unsqueeze(0).unsqueeze(0).cuda()
    with torch.no_grad():
        logits = model.net(tensor)
        pred = logits.argmax(dim=1).squeeze(0).detach().cpu().numpy().astype(np.int16)

    from utils.metrics import dice_score, distance_metric, precision_and_recall, segmentation_scores

    scores = segmentation_scores([label], [pred], n_class=output_nc)
    dice = dice_score(label, pred, n_class=output_nc)
    precision, recall = precision_and_recall(label, pred, n_class=output_nc)
    md = hd = None
    if output_nc > 1:
        try:
            md, hd = distance_metric(label, pred, dx=1.0, k=min(1, output_nc - 1))
        except Exception as exc:  # pragma: no cover - the helper should keep going on sparse volumes
            md = hd = f"distance-metric-skipped: {exc}"

    save_nifti(volume, output_dir / "input.nii.gz")
    save_nifti(label, output_dir / "label.nii.gz")
    save_nifti(pred, output_dir / "prediction.nii.gz")

    metrics = {
        "overall_acc": float(scores["overall_acc"]),
        "mean_acc": float(scores["mean_acc"]),
        "mean_iou": float(scores["mean_iou"]),
        "fwavacc": float(scores["freq_w_acc"]),
        "dice": [float(x) for x in np.asarray(dice).ravel()],
        "precision": [float(x) for x in np.asarray(precision).ravel()],
        "recall": [float(x) for x in np.asarray(recall).ravel()],
        "mean_distance": md,
        "hausdorff": hd,
    }
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))


def extract_feature_map(model, layer_name: str, volume: np.ndarray) -> np.ndarray:
    if not hasattr(model.net, layer_name):
        raise AttributeError(layer_name)
    _, output = model.get_feature_maps(layer_name, upscale=False)
    if isinstance(output, (list, tuple)) and len(output) > 1:
        feature = output[1]
    else:
        feature = output

    if torch.is_tensor(feature):
        feature = feature.detach().float().cpu().numpy()
    feature = np.asarray(feature)
    feature = np.squeeze(feature)
    if feature.ndim == 4:
        feature = feature.mean(axis=0)
    elif feature.ndim == 3:
        pass
    else:
        raise ValueError(f"unsupported feature shape {feature.shape} for layer {layer_name}")

    if feature.shape != volume.shape:
        feature = resize(
            feature,
            volume.shape,
            mode="constant",
            preserve_range=True,
            anti_aliasing=True,
        ).astype(np.float32)
    return feature.astype(np.float32)


def run_maps(model, volume: np.ndarray, output_dir: Path, layers: list[str]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    tensor = torch.from_numpy(volume).float().unsqueeze(0).unsqueeze(0).cuda()
    model.net.eval()
    model.set_input(tensor)
    with torch.no_grad():
        _ = model.net(tensor)

    exported = []
    for layer_name in layers:
        if not hasattr(model.net, layer_name):
            print(f"skip-missing-layer={layer_name}")
            continue
        try:
            feature = extract_feature_map(model, layer_name, volume)
        except ValueError as exc:
            print(f"skip-unsupported-layer={layer_name}: {exc}")
            continue
        exported.append(feature)
        save_nifti(feature, output_dir / f"{layer_name}.nii.gz")
        save_middle_slice_png(feature, output_dir / f"{layer_name}.png", title=layer_name)
        print(f"exported-layer={layer_name} shape={feature.shape}")

    if not exported:
        raise SystemExit("none of the requested layers were found on the model")

    merged = np.mean(np.stack(exported, axis=0), axis=0)
    save_nifti(merged, output_dir / "merged.nii.gz")
    save_middle_slice_png(merged, output_dir / "merged.png", title="merged")
    print(f"merged_shape={merged.shape}")


def main() -> int:
    args = parse_args()
    repo_root = add_repo_root(args.repo_root)
    from models import get_model

    model_cfg, _ = load_model_config(repo_root, args.config)
    volume = load_volume(args.input_npy, tuple(args.synthetic_shape), args.seed)
    output_dir = Path(args.output_dir).resolve()

    with tempfile.TemporaryDirectory(prefix="ag-net-segmentation-") as tmp:
        tmpdir = Path(tmp)
        model = get_model(prepare_segmentation_cfg(tmpdir, model_cfg, args))
        model.net.eval()

        if args.mode in ("validate", "both"):
            run_validate(model, volume, output_dir / "validate", int(model_cfg.output_nc), args.label_npy)
        if args.mode in ("maps", "both"):
            run_maps(model, volume, output_dir / "maps", list(args.layers))

    print("segmentation-helper-ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
