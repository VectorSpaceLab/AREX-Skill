#!/usr/bin/env python3
"""Read-only KAIR training option checker.

This helper validates the JSON-with-//comments option files used by KAIR
training scripts. It does not import KAIR, does not launch training, and does
not modify files.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

IMAGE_DATASET_TYPES = {
    "l", "low-quality", "input-only",
    "dncnn", "denoising", "dnpatch",
    "ffdnet", "denoising-noiselevel",
    "fdncnn", "denoising-noiselevelmap",
    "sr", "super-resolution", "srmd", "dpsr", "dnsr",
    "usrnet", "usrgan", "bsrnet", "bsrgan", "blindsr",
    "jpeg", "plain", "plainpatch",
}
VIDEO_DATASET_TYPES = {
    "videorecurrenttraindataset",
    "videorecurrenttrainnonblinddenoisingdataset",
    "videorecurrenttrainvimeodataset",
    "videorecurrenttrainvimeovfidataset",
    "videorecurrenttestdataset",
    "singlevideorecurrenttestdataset",
    "videotestvimeo90kdataset",
    "vfi_davis", "vfi_ucf101", "vfi_vid4",
}
MODEL_TYPES = {"plain", "plain2", "plain4", "gan", "vrt"}
NET_TYPES = {
    "dncnn", "fdncnn", "ffdnet", "srmd", "dpsr", "msrresnet0", "msrresnet1",
    "rrdb", "rrdbnet", "imdn", "usrnet", "drunet", "swinir", "vrt", "rvrt",
}
DDP_SCRIPTS = {"main_train_psnr.py", "main_train_gan.py", "main_train_drunet.py", "main_train_vrt.py"}


def strip_json_line_comments(text: str) -> str:
    """Strip // comments outside quoted strings."""
    out: List[str] = []
    in_string = False
    escape = False
    i = 0
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if in_string:
            out.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
            continue
        if ch == "/" and nxt == "/":
            while i < len(text) and text[i] not in "\r\n":
                i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def load_config(path: Path) -> Dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    return json.loads(strip_json_line_comments(raw))


def boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"true", "1", "yes", "y"}
    return bool(value)


def choose_script(opt: Dict[str, Any], config_name: str) -> str:
    model = str(opt.get("model", "")).lower()
    net_type = str(opt.get("netG", {}).get("net_type", "")).lower()
    if net_type in {"vrt", "rvrt"} or model == "vrt" or "/vrt/" in config_name or "/rvrt/" in config_name:
        return "main_train_vrt.py"
    if model == "gan":
        return "main_train_gan.py"
    if net_type == "drunet":
        return "main_train_drunet.py"
    if model == "plain4" or net_type == "usrnet":
        return "main_train_usrnet.py"
    if net_type in {"dncnn", "fdncnn", "ffdnet"} and "swinir" not in config_name:
        return "main_train_dncnn.py"
    return "main_train_psnr.py"


def command_for(script: str, config: Path, dist: bool, gpu_count: int, port: int) -> str:
    opt_flag = "-opt" if script in {"main_train_dncnn.py", "main_train_usrnet.py"} else "--opt"
    base = f"python {script} {opt_flag} {config}"
    if dist and script in DDP_SCRIPTS:
        return (
            f"python -m torch.distributed.launch --nproc_per_node={gpu_count} "
            f"--master_port={port} {script} {opt_flag} {config} --dist True"
        )
    return base


def exists_under(root: Path, value: Any) -> bool | None:
    if value in (None, ""):
        return None
    try:
        return (root / os.path.expanduser(str(value))).exists()
    except OSError:
        return False


def require(mapping: Dict[str, Any], key: str, where: str, errors: List[str]) -> Any:
    if key not in mapping:
        errors.append(f"Missing `{where}.{key}`")
        return None
    return mapping[key]


def validate(opt: Dict[str, Any], config: Path, repo_root: Path, check_paths: bool, port: int) -> Tuple[List[str], List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    notes: List[str] = []

    require(opt, "task", "root", errors)
    model = require(opt, "model", "root", errors)
    gpu_ids = require(opt, "gpu_ids", "root", errors)
    datasets = require(opt, "datasets", "root", errors)
    path_cfg = require(opt, "path", "root", errors)
    netg = require(opt, "netG", "root", errors)
    train = require(opt, "train", "root", errors)

    if model is not None and str(model).lower() not in MODEL_TYPES:
        errors.append(f"Unsupported `model`: {model!r}; expected one of {sorted(MODEL_TYPES)}")

    if not isinstance(gpu_ids, list):
        errors.append("`gpu_ids` should be a list such as [0] or [0, 1, 2, 3]")
        gpu_count = 1
    else:
        gpu_count = len(gpu_ids)
        if not gpu_ids:
            warnings.append("`gpu_ids` is empty; KAIR generally expects at least one GPU id for training.")

    if isinstance(path_cfg, dict):
        require(path_cfg, "root", "path", errors)
    if isinstance(netg, dict):
        net_type = require(netg, "net_type", "netG", errors)
        if net_type is not None and str(net_type).lower() not in NET_TYPES:
            errors.append(f"Unsupported `netG.net_type`: {net_type!r}; expected one of {sorted(NET_TYPES)}")
    if isinstance(train, dict):
        for key in ["G_lossfn_type", "G_optimizer_type", "G_optimizer_lr", "checkpoint_print", "checkpoint_save"]:
            if key not in train:
                warnings.append(f"Training key `{key}` is absent; KAIR may fill some defaults, but confirm this is intentional.")
    if isinstance(datasets, dict):
        if "train" not in datasets:
            errors.append("Missing `datasets.train`")
        for phase, ds in datasets.items():
            if not isinstance(ds, dict):
                errors.append(f"`datasets.{phase}` should be an object")
                continue
            dtype = ds.get("dataset_type")
            if dtype is None:
                errors.append(f"Missing `datasets.{phase}.dataset_type`")
                continue
            dtype_l = str(dtype).lower()
            if dtype_l in VIDEO_DATASET_TYPES:
                warnings.append(f"`datasets.{phase}.dataset_type` is video-oriented; route VRT/RVRT configs to the video-restoration sub-skill.")
            elif dtype_l not in IMAGE_DATASET_TYPES:
                errors.append(f"Unknown `datasets.{phase}.dataset_type`: {dtype!r}")
            if check_paths:
                for root_key in ["dataroot_H", "dataroot_L", "dataroot_gt", "dataroot_lq", "meta_info_file"]:
                    if root_key in ds and ds[root_key] not in (None, ""):
                        ok = exists_under(repo_root, ds[root_key])
                        if ok is False:
                            warnings.append(f"Path for `datasets.{phase}.{root_key}` does not exist under repo root: {ds[root_key]}")

    script = choose_script(opt, config.as_posix().lower())
    dist = boolish(opt.get("dist", False))
    if dist and script not in DDP_SCRIPTS:
        warnings.append(f"Config requests distributed training, but `{script}` does not parse `--dist`; use DataParallel or choose a DDP-capable entry point.")
    if dist and gpu_count <= 1:
        warnings.append("Distributed training requested with one or zero `gpu_ids`; check `gpu_ids` and launcher `--nproc_per_node`.")
    if script in {"main_train_dncnn.py", "main_train_usrnet.py"}:
        notes.append(f"`{script}` uses one-dash `-opt`, not `--opt`.")

    notes.append(f"Suggested entry script: {script}")
    notes.append(f"Suggested launch template: {command_for(script, config, dist, max(gpu_count, 1), port)}")
    if isinstance(path_cfg, dict) and opt.get("task"):
        exp_root = path_cfg.get("root", "<path.root>")
        notes.append(f"Derived experiment folder: {exp_root}/{opt.get('task')}/")
        notes.append("Resume detection scans the derived `models/` folder for numbered *_G.pth, *_E.pth, and optimizer checkpoints.")

    return errors, warnings, notes


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a KAIR training option JSON without importing KAIR or launching training.")
    parser.add_argument("--config", required=True, type=Path, help="Path to a KAIR option JSON file, including JSON files with // comments.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="KAIR checkout root used only for optional path-existence checks. Default: current directory.")
    parser.add_argument("--no-path-check", action="store_true", help="Skip existence checks for dataroot/meta-info paths.")
    parser.add_argument("--master-port", type=int, default=1234, help="Port to show in suggested DDP launch templates.")
    args = parser.parse_args()

    try:
        opt = load_config(args.config)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: failed to parse {args.config}: {exc}")
        return 2

    errors, warnings, notes = validate(opt, args.config, args.repo_root, not args.no_path_check, args.master_port)
    print(f"Config: {args.config}")
    print(f"Task: {opt.get('task', '<missing>')}")
    print(f"Model/netG: {opt.get('model', '<missing>')} / {opt.get('netG', {}).get('net_type', '<missing>') if isinstance(opt.get('netG'), dict) else '<missing>'}")
    print()
    for label, items in [("ERROR", errors), ("WARN", warnings), ("NOTE", notes)]:
        for item in items:
            print(f"{label}: {item}")
    if errors:
        print("\nResult: invalid for KAIR image-training guidance.")
        return 1
    print("\nResult: no structural errors found. Review warnings before launching expensive training.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
