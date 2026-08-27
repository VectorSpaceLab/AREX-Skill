#!/usr/bin/env python3
"""Render or execute safe LatentSync training torchrun commands.

This helper wraps the source launch shape used by train_unet.sh and
train_syncnet.sh without hard-coded private paths. It defaults to rendering the
command only. Add --execute to run after optional/automatic preflight checks.
"""

from __future__ import annotations

import argparse
import os
import shlex
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any


UNET_MODULE = "scripts.train_unet"
SYNCNET_MODULE = "scripts.train_syncnet"


class PreflightError(RuntimeError):
    """Raised for a launch-blocking preflight issue."""


def shell_join(parts: list[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def resolve_runtime_path(raw: Any, repo_root: Path) -> Path:
    text = os.path.expandvars(os.path.expanduser(str(raw)))
    path = Path(text)
    if not path.is_absolute():
        path = repo_root / path
    return path


def display_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def infer_mode(config_path: Path, explicit_mode: str) -> str:
    if explicit_mode != "auto":
        return explicit_mode

    lowered_parts = [part.lower() for part in config_path.parts]
    name = config_path.name.lower()
    if "syncnet" in lowered_parts or "syncnet" in name:
        return "syncnet"
    if "unet" in lowered_parts or name.startswith("stage"):
        return "unet"
    raise SystemExit(
        "Could not infer training mode from config path. "
        "Pass --mode unet or --mode syncnet explicitly."
    )


def build_command(args: argparse.Namespace, mode: str, config_arg: str, master_port: int) -> list[str]:
    if args.python_launcher:
        launcher = [sys.executable, "-m", "torch.distributed.run"]
    else:
        launcher = ["torchrun"]

    module = UNET_MODULE if mode == "unet" else SYNCNET_MODULE
    config_flag = "--unet_config_path" if mode == "unet" else "--config_path"

    return [
        *launcher,
        f"--nnodes={args.nnodes}",
        f"--nproc_per_node={args.nproc_per_node}",
        f"--master_port={master_port}",
        "-m",
        module,
        config_flag,
        config_arg,
    ]


def load_config(config_path: Path):
    """Load YAML with OmegaConf when available, otherwise PyYAML.

    Training itself requires OmegaConf, but command preflight should remain useful
    in lighter review environments that only have PyYAML installed.
    """
    try:
        from omegaconf import OmegaConf

        return OmegaConf.load(config_path)
    except Exception:
        pass

    try:
        import yaml
    except Exception as exc:  # pragma: no cover - message is for runtime users
        raise PreflightError(
            "--preflight requires either OmegaConf or PyYAML to read the training YAML config."
        ) from exc

    with config_path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    if not isinstance(loaded, dict):
        raise PreflightError(f"Config did not parse as a YAML mapping: {config_path}")
    return loaded


def cfg_select(config: Any, key: str, default: Any = "") -> Any:
    try:
        from omegaconf import OmegaConf

        if not isinstance(config, dict):
            value = OmegaConf.select(config, key)
            return default if value is None else value
    except Exception:
        pass

    current: Any = config
    for part in key.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default
    return default if current is None else current


def cfg_str(config: Any, key: str) -> str:
    value = cfg_select(config, key, "")
    return "" if value is None else str(value).strip()


def cfg_bool(config: Any, key: str, default: bool = False) -> bool:
    value = cfg_select(config, key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "on"}
    return bool(value)


def cfg_float(config: Any, key: str, default: float = 0.0) -> float:
    value = cfg_select(config, key, default)
    try:
        return float(value)
    except Exception:
        return default


def validate_fileslist(fileslist: str, repo_root: Path, label: str) -> int:
    path = resolve_runtime_path(fileslist, repo_root)
    if not path.is_file():
        raise PreflightError(f"{label}: fileslist does not exist or is not a file: {path}")

    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                raise PreflightError(
                    f"{label}: blank line at {path}:{line_number}. "
                    "Remove empty rows; a final trailing newline is OK."
                )
            if not line.lower().endswith(".mp4"):
                raise PreflightError(
                    f"{label}: malformed entry at {path}:{line_number}: {line!r}. "
                    "LatentSync training file lists should contain one .mp4 path per line."
                )
            video_path = resolve_runtime_path(line, repo_root)
            if not video_path.is_file():
                raise PreflightError(
                    f"{label}: missing video path at {path}:{line_number}: {line!r} "
                    f"(resolved to {video_path})."
                )
            count += 1

    if count == 0:
        raise PreflightError(f"{label}: fileslist is empty: {path}")
    print(f"preflight: {label} OK ({count} .mp4 paths)", file=sys.stderr)
    return count


def count_directory_mp4s(data_dir: str, repo_root: Path, label: str, recursive: bool) -> int:
    path = resolve_runtime_path(data_dir, repo_root)
    if not path.is_dir():
        raise PreflightError(f"{label}: data directory does not exist or is not a directory: {path}")

    iterator = path.rglob("*") if recursive else path.iterdir()
    count = sum(1 for item in iterator if item.is_file() and item.suffix.lower() == ".mp4")
    if count == 0:
        scan = "recursively" if recursive else "non-recursively"
        raise PreflightError(f"{label}: no .mp4 files found {scan} under {path}")
    print(f"preflight: {label} OK ({count} .mp4 files)", file=sys.stderr)
    return count


def validate_dataset_choice(
    config: Any,
    fileslist_key: str,
    data_dir_key: str,
    repo_root: Path,
    label: str,
    directory_recursive: bool,
) -> None:
    fileslist = cfg_str(config, fileslist_key)
    data_dir = cfg_str(config, data_dir_key)
    if fileslist:
        validate_fileslist(fileslist, repo_root, label)
    elif data_dir:
        count_directory_mp4s(data_dir, repo_root, label, recursive=directory_recursive)
    else:
        raise PreflightError(
            f"{label}: both {fileslist_key} and {data_dir_key} are empty. "
            "Set one to a real processed-video source before launch."
        )


def warn_or_block_path(raw_path: str, repo_root: Path, label: str, *, execute: bool) -> None:
    if not raw_path:
        return
    path = resolve_runtime_path(raw_path, repo_root)
    if path.exists():
        return
    message = f"{label}: configured path does not exist: {path}"
    if execute:
        raise PreflightError(message)
    print(f"preflight warning: {message}", file=sys.stderr)


def require_repo_file(repo_root: Path, relative_path: str, label: str) -> None:
    path = repo_root / relative_path
    if not path.exists():
        raise PreflightError(f"{label}: required repo-relative file is missing: {relative_path}")


def preflight_unet(config_path: Path, repo_root: Path, *, execute: bool) -> None:
    config = load_config(config_path)
    require_repo_file(repo_root, "configs/audio.yaml", "audio config")
    require_repo_file(repo_root, "configs/scheduler_config.json", "DDIM scheduler config")

    validate_dataset_choice(
        config,
        "data.train_fileslist",
        "data.train_data_dir",
        repo_root,
        "U-Net train data",
        directory_recursive=False,
    )

    syncnet_config_path = cfg_str(config, "data.syncnet_config_path")
    if syncnet_config_path:
        resolved_syncnet_config = resolve_runtime_path(syncnet_config_path, repo_root)
        if not resolved_syncnet_config.is_file():
            raise PreflightError(f"U-Net data.syncnet_config_path does not exist: {resolved_syncnet_config}")
        if cfg_bool(config, "run.use_syncnet", False):
            syncnet_config = load_config(resolved_syncnet_config)
            inference_ckpt = cfg_str(syncnet_config, "ckpt.inference_ckpt_path")
            if not inference_ckpt:
                raise PreflightError(
                    "U-Net run.use_syncnet is true but the referenced SyncNet config has empty "
                    "ckpt.inference_ckpt_path."
                )
            warn_or_block_path(
                inference_ckpt,
                repo_root,
                "U-Net SyncNet supervision checkpoint",
                execute=execute,
            )

    warn_or_block_path(
        cfg_str(config, "ckpt.resume_ckpt_path"),
        repo_root,
        "U-Net resume/init checkpoint",
        execute=execute,
    )
    warn_or_block_path(
        "checkpoints/auxiliary/syncnet_v2.model",
        repo_root,
        "U-Net validation SyncNet checkpoint",
        execute=execute,
    )

    cross_attention_dim = int(cfg_float(config, "model.cross_attention_dim", 384))
    whisper_path = "checkpoints/whisper/small.pt" if cross_attention_dim == 768 else "checkpoints/whisper/tiny.pt"
    warn_or_block_path(whisper_path, repo_root, "Whisper audio feature checkpoint", execute=execute)

    if cfg_bool(config, "run.pixel_space_supervise", False) and cfg_float(config, "run.trepa_loss_weight", 0.0) != 0:
        trepa_path = "checkpoints/auxiliary/vit_g_hybrid_pt_1200e_ssv2_ft.pth"
        if not resolve_runtime_path(trepa_path, repo_root).exists():
            print(
                "preflight warning: TREPA loss is active and its auxiliary checkpoint is missing; "
                "the source helper may try a Hugging Face download or fail offline: " + trepa_path,
                file=sys.stderr,
            )

    for key, label in (("data.val_video_path", "validation video"), ("data.val_audio_path", "validation audio")):
        value = cfg_str(config, key)
        if value and not resolve_runtime_path(value, repo_root).exists():
            print(f"preflight warning: U-Net {label} path is missing: {value}", file=sys.stderr)


def preflight_syncnet(config_path: Path, repo_root: Path, *, execute: bool) -> None:
    config = load_config(config_path)
    require_repo_file(repo_root, "configs/audio.yaml", "audio config")

    validate_dataset_choice(
        config,
        "data.train_fileslist",
        "data.train_data_dir",
        repo_root,
        "SyncNet train data",
        directory_recursive=True,
    )
    validate_dataset_choice(
        config,
        "data.val_fileslist",
        "data.val_data_dir",
        repo_root,
        "SyncNet validation data",
        directory_recursive=True,
    )

    warn_or_block_path(
        cfg_str(config, "ckpt.resume_ckpt_path"),
        repo_root,
        "SyncNet resume checkpoint",
        execute=execute,
    )

    if cfg_bool(config, "data.latent_space", False):
        print(
            "preflight warning: SyncNet latent_space=true requires VAE loading and has different "
            "visual encoder shape from pixel-space checkpoints.",
            file=sys.stderr,
        )


def run_preflight(mode: str, config_path: Path, repo_root: Path, *, execute: bool) -> None:
    if mode == "unet":
        preflight_unet(config_path, repo_root, execute=execute)
    elif mode == "syncnet":
        preflight_syncnet(config_path, repo_root, execute=execute)
    else:  # pragma: no cover
        raise PreflightError(f"Unsupported mode: {mode}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render or execute LatentSync torchrun training commands safely."
    )
    parser.add_argument("--repo-root", default=".", help="Path to the LatentSync checkout root (default: cwd).")
    parser.add_argument("--config", "--config-path", dest="config_path", required=True, help="Training YAML config path.")
    parser.add_argument("--mode", choices=["auto", "unet", "syncnet"], default="auto", help="Training entry point.")
    parser.add_argument("--nnodes", type=int, default=1, help="torchrun --nnodes value.")
    parser.add_argument("--nproc-per-node", dest="nproc_per_node", type=int, default=1, help="torchrun --nproc_per_node value.")
    parser.add_argument("--master-port", type=int, default=None, help="torchrun --master_port; defaults to an available local port.")
    parser.add_argument("--python-launcher", action="store_true", help="Render/execute python -m torch.distributed.run instead of torchrun.")
    parser.add_argument("--preflight", action="store_true", help="Validate config data/file-list paths before rendering.")
    parser.add_argument("--execute", action="store_true", help="Execute after rendering. Also enables preflight.")
    parser.add_argument("--ack-high-vram", action="store_true", help="Required to execute configs/unet/stage2_512.yaml.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    if args.nnodes < 1 or args.nproc_per_node < 1:
        raise SystemExit("--nnodes and --nproc-per-node must both be >= 1")

    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.is_dir():
        raise SystemExit(f"--repo-root does not exist or is not a directory: {repo_root}")

    config_path = resolve_runtime_path(args.config_path, repo_root).resolve()
    if not config_path.is_file():
        raise SystemExit(f"Config file does not exist: {config_path}")

    mode = infer_mode(config_path, args.mode)
    config_arg = display_path(config_path, repo_root)
    master_port = args.master_port if args.master_port is not None else find_free_port()

    if mode == "unet" and config_path.name == "stage2_512.yaml":
        warning = (
            "WARNING: configs/unet/stage2_512.yaml is documented at about 55 GB VRAM "
            "per GPU process. It is not a smoke target."
        )
        print(warning, file=sys.stderr)
        if args.execute and not args.ack_high_vram:
            raise SystemExit("Refusing to execute stage2_512 without --ack-high-vram.")
    elif mode == "unet" and config_path.name == "stage1_512.yaml":
        print("preflight note: stage1_512 is a 512px config with about 30 GB VRAM demand.", file=sys.stderr)

    if args.preflight or args.execute:
        try:
            run_preflight(mode, config_path, repo_root, execute=args.execute)
        except PreflightError as exc:
            raise SystemExit(f"Preflight failed: {exc}") from exc

    command = build_command(args, mode, config_arg, master_port)
    print(f"# repo-root: {repo_root}")
    print(f"# mode: {mode}")
    print(f"cd {shlex.quote(str(repo_root))} && {shell_join(command)}")

    if not args.execute:
        return 0

    completed = subprocess.run(command, cwd=str(repo_root), check=False)
    return int(completed.returncode)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
