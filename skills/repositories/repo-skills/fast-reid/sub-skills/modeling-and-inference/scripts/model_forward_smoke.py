#!/usr/bin/env python3
"""CPU-only FastReID model construction and forward smoke.

This script is safe by default: it uses CPU, disables backbone pretraining, does
not load model weights, and runs one random tensor through the model in eval mode.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Iterable


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build a FastReID model on CPU, disable backbone pretraining, "
            "run one random BCHW tensor forward, and print output shape."
        )
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help=(
            "Optional path to a FastReID source checkout. Use this when the "
            "fastreid package is not otherwise importable."
        ),
    )
    parser.add_argument(
        "--config-file",
        default=None,
        help=(
            "Optional FastReID YAML config path. Relative paths are resolved "
            "first from the current directory, then from --repo-root if set."
        ),
    )
    parser.add_argument("--height", type=positive_int, default=256, help="Input tensor height. Default: 256.")
    parser.add_argument("--width", type=positive_int, default=128, help="Input tensor width. Default: 128.")
    parser.add_argument(
        "--num-classes",
        type=positive_int,
        default=1,
        help="NUM_CLASSES placeholder for head construction. Default: 1.",
    )
    parser.add_argument("--batch-size", type=positive_int, default=1, help="Random batch size. Default: 1.")
    parser.add_argument("--seed", type=int, default=7, help="Torch RNG seed for the random tensor. Default: 7.")
    parser.add_argument(
        "--opts",
        nargs=argparse.REMAINDER,
        default=[],
        help="Optional KEY VALUE config overrides applied before safe CPU/no-pretrain overrides.",
    )
    return parser


def add_repo_root(repo_root: str | None) -> Path | None:
    if not repo_root:
        return None
    root = Path(repo_root).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"ERROR: --repo-root does not exist: {root}")
    if not (root / "fastreid").is_dir():
        raise SystemExit(f"ERROR: --repo-root must contain a fastreid/ package directory: {root}")
    sys.path.insert(0, str(root))
    return root


def resolve_optional_file(path_text: str | None, repo_root: Path | None, label: str) -> Path | None:
    if not path_text:
        return None
    raw = Path(path_text).expanduser()
    candidates = [raw]
    if not raw.is_absolute() and repo_root is not None:
        candidates.append(repo_root / raw)
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    tried = ", ".join(str(c) for c in candidates)
    raise SystemExit(f"ERROR: {label} not found. Tried: {tried}")


def import_runtime() -> tuple[Any, Any]:
    try:
        import torch
        from fastreid.config import get_cfg
        from fastreid.modeling import build_model
    except Exception as exc:  # pragma: no cover - error path is environment-specific.
        raise SystemExit(
            "ERROR: failed to import FastReID runtime. Provide --repo-root for a "
            "source checkout and ensure torch/yacs/PyYAML dependencies are installed. "
            f"Original error: {type(exc).__name__}: {exc}"
        ) from exc
    return torch, (get_cfg, build_model)


def describe_output(value: Any) -> Any:
    if hasattr(value, "shape"):
        return tuple(int(x) for x in value.shape)
    if isinstance(value, dict):
        return {str(k): describe_output(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [describe_output(v) for v in value]
    return type(value).__name__


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = add_repo_root(args.repo_root)
    config_path = resolve_optional_file(args.config_file, repo_root, "--config-file")

    torch, runtime = import_runtime()
    get_cfg, build_model = runtime

    torch.manual_seed(args.seed)

    cfg = get_cfg()
    if config_path is not None:
        cfg.merge_from_file(str(config_path))
    if args.opts:
        if len(args.opts) % 2 != 0:
            raise SystemExit("ERROR: --opts expects KEY VALUE pairs.")
        cfg.merge_from_list(args.opts)

    cfg.defrost()
    cfg.MODEL.DEVICE = "cpu"
    cfg.MODEL.BACKBONE.PRETRAIN = False
    cfg.MODEL.HEADS.NUM_CLASSES = args.num_classes
    cfg.freeze()

    try:
        model = build_model(cfg)
        model.eval()
        images = torch.rand(args.batch_size, 3, args.height, args.width, dtype=torch.float32)
        with torch.no_grad():
            output = model(images)
    except Exception as exc:  # pragma: no cover - depends on user configs.
        raise SystemExit(
            "ERROR: FastReID CPU model forward smoke failed. Check model family, "
            "input size, head config, optional dependencies, and device settings. "
            f"Original error: {type(exc).__name__}: {exc}"
        ) from exc

    print("FastReID model forward smoke passed")
    print(f"repo_root={repo_root if repo_root is not None else '<importable-package>'}")
    print(f"config_file={config_path if config_path is not None else '<default-config>'}")
    print(f"device={cfg.MODEL.DEVICE}")
    print(f"meta_architecture={cfg.MODEL.META_ARCHITECTURE}")
    print(f"backbone={cfg.MODEL.BACKBONE.NAME}")
    print(f"head={cfg.MODEL.HEADS.NAME}")
    print(f"pretrain={cfg.MODEL.BACKBONE.PRETRAIN}")
    print(f"input_shape={(args.batch_size, 3, args.height, args.width)}")
    print(f"output_shape={describe_output(output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
