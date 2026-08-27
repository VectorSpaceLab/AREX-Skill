#!/usr/bin/env python3
"""CPU-only diagnostics for DRL-Pytorch Atari and ASL workflows.

This helper imports modules from a user-supplied DRL-Pytorch checkout, runs tiny
CNN forward passes on dummy tensors, and optionally probes import-only gates for
Atari wrappers and EnvPool. It does not create Atari environments, download ROMs,
start EnvPool workers, render, write checkpoints, or train.

Examples:
  python smoke_atari_asl.py --repo-root <repo-root>
  python smoke_atari_asl.py --repo-root <repo-root> --probe-atari-wrappers
  python smoke_atari_asl.py --repo-root <repo-root> --probe-envpool
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import importlib.util
import sys
import traceback
from pathlib import Path
from types import SimpleNamespace
from typing import Iterable

_SENTINEL = object()


@contextlib.contextmanager
def isolated_import_path(directory: Path, purge_names: Iterable[str]):
    """Temporarily import modules from a workflow directory.

    DRL-Pytorch has separate workflow directories that reuse module names such as
    ``utils`` and ``AtariNames``. This context avoids accidentally importing the
    sibling workflow's module during diagnostics.
    """

    old_path = list(sys.path)
    saved_modules = {}
    for name in purge_names:
        saved_modules[name] = sys.modules.pop(name, _SENTINEL)
    sys.path.insert(0, str(directory))
    importlib.invalidate_caches()
    try:
        yield
    finally:
        sys.path[:] = old_path
        for name, module in saved_modules.items():
            if module is _SENTINEL:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
        importlib.invalidate_caches()


def load_module_from_file(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not build an import spec for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def require_repo_subdir(repo_root: Path, relative: str) -> Path:
    path = repo_root / relative
    if not path.is_dir():
        raise FileNotFoundError(
            f"Expected DRL-Pytorch workflow directory is missing: {relative}"
        )
    return path


def require_torch():
    try:
        import torch
    except ImportError as exc:  # pragma: no cover - depends on user env
        raise RuntimeError(
            "PyTorch is required for the dummy CNN smoke. Install torch before "
            "using this diagnostic."
        ) from exc
    return torch


def run_atari_agent_smoke(repo_root: Path, action_dim: int, fc_width: int, noisy: bool):
    torch = require_torch()
    atari_dir = require_repo_subdir(repo_root, "2.2_Noisy-Duel-DDQN-Atari")

    with isolated_import_path(atari_dir, ["Agent", "utils", "AtariNames"]):
        agent_mod = importlib.import_module("Agent")

    opt = SimpleNamespace(Noisy=noisy, fc_width=fc_width, action_dim=action_dim)
    model = agent_mod.Duel_Q_Net(opt).cpu().eval()
    dummy = torch.zeros((1, 4, 84, 84), dtype=torch.uint8)
    with torch.no_grad():
        q_values = model(dummy)
    expected = (1, action_dim)
    actual = tuple(q_values.shape)
    if actual != expected:
        raise AssertionError(f"Duel_Q_Net output shape {actual}, expected {expected}")
    print(
        "OK atari-agent: imported Agent.Duel_Q_Net and ran CPU dummy forward "
        f"with output shape {actual}"
    )


def run_asl_utils_smoke(repo_root: Path, action_dim: int, fc_width: int):
    torch = require_torch()
    asl_dir = require_repo_subdir(repo_root, "6. Actor-Sharer-Learner")
    asl_utils = load_module_from_file("_drl_pytorch_asl_utils", asl_dir / "utils.py")

    model = asl_utils.Q_Net(action_dim=action_dim, hidden=fc_width).cpu().eval()
    dummy = torch.zeros((1, 4, 84, 84), dtype=torch.uint8)
    with torch.no_grad():
        q_values = model(dummy)
    expected = (1, action_dim)
    actual = tuple(q_values.shape)
    if actual != expected:
        raise AssertionError(f"ASL Q_Net output shape {actual}, expected {expected}")
    print(
        "OK asl-utils: imported ASL utils.Q_Net and ran CPU dummy forward "
        f"with output shape {actual}"
    )


def probe_atari_wrappers(repo_root: Path) -> bool:
    atari_dir = require_repo_subdir(repo_root, "2.2_Noisy-Duel-DDQN-Atari")
    try:
        with isolated_import_path(atari_dir, ["tianshou_wrappers"]):
            wrappers = importlib.import_module("tianshou_wrappers")
        assert hasattr(wrappers, "make_env_tianshou")
    except Exception as exc:  # optional dependency probe
        print(
            "SKIP/FAIL optional atari-wrappers: import-only probe failed. "
            "Common causes are missing cv2/opencv-python or Gymnasium Atari "
            f"extras. Detail: {type(exc).__name__}: {exc}"
        )
        return False
    print(
        "OK optional atari-wrappers: imported make_env_tianshou without creating "
        "an Atari environment"
    )
    return True


def probe_envpool_import() -> bool:
    try:
        envpool = importlib.import_module("envpool")
    except Exception as exc:  # optional dependency probe
        print(
            "SKIP/FAIL optional envpool: import-only probe failed. ASL requires "
            f"EnvPool on a supported platform. Detail: {type(exc).__name__}: {exc}"
        )
        return False
    version = getattr(envpool, "__version__", "unknown")
    print(f"OK optional envpool: imported envpool version {version}; no env was created")
    return True


def probe_asl_sharer(repo_root: Path) -> bool:
    try:
        import numpy as np
    except ImportError as exc:  # pragma: no cover - depends on user env
        print(f"SKIP/FAIL optional asl-sharer: numpy missing: {exc}")
        return False
    torch = require_torch()
    asl_dir = require_repo_subdir(repo_root, "6. Actor-Sharer-Learner")
    sharer_mod = load_module_from_file("_drl_pytorch_asl_sharer", asl_dir / "sharer.py")

    opt = SimpleNamespace(
        B_dvc="cpu",
        L_dvc="cpu",
        buffersize=4,
        train_envs=2,
        batch_size=1,
    )
    shared = sharer_mod.shared_data_cpu(opt)
    for step in range(2):
        obs = np.full((2, 4, 84, 84), step, dtype=np.uint8)
        actions = np.zeros((2,), dtype=np.int64)
        rewards = np.zeros((2,), dtype=np.float32)
        done = np.zeros((2,), dtype=np.bool_)
        consistent = np.ones((2,), dtype=np.bool_)
        shared.add_core((obs, actions, rewards, done, consistent))
    batch = shared.sample_core()
    shapes = [tuple(item.shape) for item in batch]
    if shapes[0][-3:] != (4, 84, 84):
        raise AssertionError(f"Unexpected shared_data_cpu sample shapes: {shapes}")
    # Use torch in a visible way so an accidental non-tensor return is caught.
    assert isinstance(batch[0], torch.Tensor)
    print(f"OK optional asl-sharer: tiny shared_data_cpu add/sample shapes {shapes}")
    return True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run safe DRL-Pytorch Atari/ASL diagnostics: dummy CPU CNN forwards "
            "plus optional import-only probes."
        )
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        required=True,
        help="Path to a DRL-Pytorch checkout containing the Atari and ASL workflow directories.",
    )
    parser.add_argument(
        "--action-dim",
        type=int,
        default=6,
        help="Dummy action dimension for CNN output shape checks. Default: 6.",
    )
    parser.add_argument(
        "--fc-width",
        type=int,
        default=32,
        help="Small hidden width for dummy networks. Default: 32.",
    )
    parser.add_argument(
        "--noisy",
        action="store_true",
        help="Use NoisyLinear layers in the Atari Duel_Q_Net dummy forward.",
    )
    parser.add_argument(
        "--probe-atari-wrappers",
        action="store_true",
        help="Optionally import tianshou_wrappers to diagnose cv2/Gymnasium wrapper gates; no env is created.",
    )
    parser.add_argument(
        "--probe-envpool",
        action="store_true",
        help="Optionally import envpool to diagnose ASL dependency gates; no env is created.",
    )
    parser.add_argument(
        "--probe-asl-sharer",
        action="store_true",
        help="Optionally instantiate a tiny CPU shared_data buffer and sample once.",
    )
    parser.add_argument(
        "--strict-optional",
        action="store_true",
        help="Return non-zero if an optional probe fails. Required dummy smokes are always strict.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print a traceback for required-smoke failures.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = args.repo_root.expanduser().resolve()

    try:
        if not repo_root.is_dir():
            raise FileNotFoundError(f"--repo-root is not a directory: {args.repo_root}")
        if args.action_dim < 1:
            raise ValueError("--action-dim must be >= 1")
        if args.fc_width < 1:
            raise ValueError("--fc-width must be >= 1")

        run_atari_agent_smoke(repo_root, args.action_dim, args.fc_width, args.noisy)
        run_asl_utils_smoke(repo_root, args.action_dim, args.fc_width)
    except Exception as exc:
        print(f"FAIL required smoke: {type(exc).__name__}: {exc}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        return 1

    optional_ok = True
    if args.probe_atari_wrappers:
        optional_ok = probe_atari_wrappers(repo_root) and optional_ok
    if args.probe_envpool:
        optional_ok = probe_envpool_import() and optional_ok
    if args.probe_asl_sharer:
        try:
            optional_ok = probe_asl_sharer(repo_root) and optional_ok
        except Exception as exc:
            print(f"SKIP/FAIL optional asl-sharer: {type(exc).__name__}: {exc}")
            optional_ok = False

    if args.strict_optional and not optional_ok:
        return 1
    print("OK summary: required Atari Agent and ASL utils diagnostics completed")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
