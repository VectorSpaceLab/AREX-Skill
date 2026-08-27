#!/usr/bin/env python3
"""Export a tiny ultrasound attention overlay from a Sononet-style model.

This helper is safe by default: if no input array is provided, it generates a
small synthetic 2D fixture, builds the classification model, captures one or
more attention layers, and writes an overlay PNG plus NumPy dumps to the output
folder.

Examples:
  python export_attention_overlay.py \
    --repo-root /path/to/repo \
    --output-dir /tmp/ag-net-attention \
    --synthetic

  python export_attention_overlay.py \
    --repo-root /path/to/repo \
    --config configs/config_sononet_grid_att_8.json \
    --input-npy sample.npy \
    --output-dir /tmp/ag-net-attention
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch


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
    # Legacy compatibility: AggregatedClassifier reads aggregation_param even
    # when the selected aggregation mode does not use it.
    if getattr(model_cfg, "type", None) == "aggregated_classifier" and not hasattr(model_cfg, "aggregation_param"):
        model_cfg.aggregation_param = 0
    return model_cfg, data


def normalize01(array: np.ndarray) -> np.ndarray:
    array = array.astype(np.float32)
    lo = float(array.min())
    hi = float(array.max())
    if np.isclose(lo, hi):
        return np.zeros_like(array, dtype=np.float32)
    return (array - lo) / (hi - lo)


def prepare_input(args) -> np.ndarray:
    if args.input_npy:
        image = np.load(args.input_npy).astype(np.float32)
        image = np.squeeze(image)
    else:
        h, w = args.synthetic_shape
        rng = np.random.default_rng(args.seed)
        image = rng.normal(size=(h, w)).astype(np.float32)

    if image.ndim != 2:
        raise SystemExit(f"expected a 2D array, got shape {image.shape}")
    return image


def attention_from_output(output) -> np.ndarray:
    if isinstance(output, (list, tuple)) and len(output) > 1:
        attention = output[1]
    else:
        attention = output

    if torch.is_tensor(attention):
        attention = attention.detach().float().cpu().numpy()

    attention = np.asarray(attention)
    attention = np.squeeze(attention)
    if attention.ndim == 3:
        attention = attention.mean(axis=0)
    if attention.ndim != 2:
        raise SystemExit(f"unsupported attention shape {attention.shape}")
    return attention.astype(np.float32)


def overlay_and_save(image: np.ndarray, attention: np.ndarray, out_dir: Path, name: str) -> Path:
    import matplotlib.pyplot as plt
    out_dir.mkdir(parents=True, exist_ok=True)
    image = normalize01(image)
    attention = normalize01(attention)
    overlay_path = out_dir / f"{name}.png"

    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(1, 1, 1)
    ax.imshow(image, cmap="gray")
    ax.imshow(attention, cmap="magma", alpha=0.45)
    ax.set_axis_off()
    ax.set_title(name)
    fig.tight_layout(pad=0)
    fig.savefig(overlay_path, bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    np.save(out_dir / f"{name}.attention.npy", attention)
    np.save(out_dir / f"{name}.image.npy", image)
    return overlay_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", help="Repository root; relative --config paths are resolved from here")
    parser.add_argument(
        "--config",
        default="configs/config_sononet_grid_att_8.json",
        help="Classification config JSON relative to --repo-root unless absolute",
    )
    parser.add_argument("--checkpoint", help="Optional checkpoint path to load before exporting")
    parser.add_argument("--input-npy", help="Optional 2D NumPy array for a real or tiny fixture input")
    parser.add_argument("--synthetic", action="store_true", help="Use a generated synthetic image when --input-npy is omitted")
    parser.add_argument("--output-dir", required=True, help="Directory for exported overlays and arrays")
    parser.add_argument(
        "--layers",
        nargs="+",
        default=["compatibility_score1", "compatibility_score2"],
        help="Attention layers to inspect and average when more than one exists",
    )
    parser.add_argument(
        "--synthetic-shape",
        nargs=2,
        type=int,
        metavar=("H", "W"),
        default=[32, 32],
        help="Synthetic image size used when --input-npy is omitted",
    )
    parser.add_argument("--seed", type=int, default=7, help="Random seed for synthetic input")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = add_repo_root(args.repo_root)
    # Legacy compatibility for code paths that still use collections.Sequence.
    import collections
    import collections.abc

    if not hasattr(collections, "Sequence"):
        collections.Sequence = collections.abc.Sequence

    from models import get_model

    from skimage.transform import resize
    model_cfg, _ = load_model_config(repo_root, args.config)
    output_dir = Path(args.output_dir).resolve()
    image = prepare_input(args)

    with tempfile.TemporaryDirectory(prefix="ag-net-classification-") as tmp:
        tmpdir = Path(tmp)
        model_cfg.checkpoints_dir = str(tmpdir)
        model_cfg.experiment_name = "attention-overlay"
        if args.checkpoint:
            model_cfg.isTrain = False
            model_cfg.path_pre_trained_model = str(Path(args.checkpoint).resolve())
            model_cfg.continue_train = False
        else:
            model_cfg.isTrain = True
            model_cfg.path_pre_trained_model = None
            model_cfg.continue_train = False

        model = get_model(model_cfg)
        model.net.eval()

        tensor = torch.from_numpy(image).float().unsqueeze(0).unsqueeze(0).cuda()
        model.set_input(tensor, torch.zeros((1,), dtype=torch.long).cuda())
        with torch.no_grad():
            prediction = model.net(tensor)
        if isinstance(prediction, (list, tuple)):
            primary_prediction = prediction[0]
        else:
            primary_prediction = prediction
        predicted_class = int(primary_prediction.argmax(dim=1).item())

        attention_maps = []
        used_layers = []
        for layer_name in args.layers:
            if not hasattr(model.net, layer_name):
                print(f"skip-missing-layer={layer_name}")
                continue
            _, output = model.get_feature_maps(layer_name, upscale=False)
            attention = attention_from_output(output)
            attention = resize(
                attention,
                image.shape,
                mode="constant",
                preserve_range=True,
                anti_aliasing=True,
            ).astype(np.float32)
            attention_maps.append(attention)
            used_layers.append(layer_name)
            overlay_and_save(image, attention, output_dir, f"overlay_{layer_name}")

        if not attention_maps:
            raise SystemExit("none of the requested attention layers were found on the model")

        merged = np.mean(np.stack(attention_maps, axis=0), axis=0)
        merged_path = overlay_and_save(image, merged, output_dir, "overlay_mean")
        print(f"predicted_class={predicted_class}")
        print(f"layers_used={used_layers}")
        print(f"merged_overlay={merged_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
