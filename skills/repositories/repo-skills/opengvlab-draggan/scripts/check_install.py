#!/usr/bin/env python3
"""Check whether the installed DragGAN stack is usable.

This helper imports the packaged DragGAN modules, confirms the web or API
compatibility surface, and reports the CUDA backend status without touching the
original repository checkout.

Example:
  python scripts/check_install.py --mode web
  python scripts/check_install.py --mode api
"""
from __future__ import annotations

import argparse
import inspect
import sys
from importlib import import_module, metadata


def _label(ok: bool) -> str:
    return "OK" if ok else "FAIL"


def _print(ok: bool, message: str) -> None:
    print(f"[{_label(ok)}] {message}")


def _require_import(name: str):
    try:
        return import_module(name), None
    except Exception as exc:  # pragma: no cover - surfaced to the user
        return None, exc


def _version(name: str) -> str:
    try:
        return metadata.version(name)
    except Exception:
        return "unknown"


def _sig(obj) -> str:
    try:
        return str(inspect.signature(obj))
    except Exception:
        return "(signature unavailable)"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("web", "api"), default="web")
    parser.add_argument(
        "--allow-cpu",
        action="store_true",
        help="Do not fail when CUDA is unavailable.",
    )
    args = parser.parse_args()

    errors = 0
    warnings = 0

    draggan, err = _require_import("draggan")
    if err:
        _print(False, f"import draggan -> {err}")
        return 1
    _print(True, f"draggan {_version('draggan')} imported from {draggan.__file__}")

    dg, err = _require_import("draggan.draggan")
    if err:
        _print(False, f"import draggan.draggan -> {err}")
        return 1

    utils, err = _require_import("draggan.utils")
    if err:
        _print(False, f"import draggan.utils -> {err}")
        return 1

    torch, err = _require_import("torch")
    if err:
        _print(False, f"import torch -> {err}")
        return 1

    cuda_ok = bool(getattr(torch, "cuda", None) and torch.cuda.is_available())
    _print(cuda_ok, f"torch {_version('torch')} cuda_available={cuda_ok} device_count={torch.cuda.device_count() if cuda_ok else 0}")
    if not cuda_ok and not args.allow_cpu:
        errors += 1
        _print(False, "CUDA is required for the verified drag workflow")

    tv, err = _require_import("torchvision")
    if err:
        _print(False, f"import torchvision -> {err}")
        errors += 1
    else:
        _print(True, f"torchvision {_version('torchvision')} imported from {tv.__file__}")

    if args.mode == "web":
        gradio, err = _require_import("gradio")
        if err:
            _print(False, f"import gradio -> {err}")
            return 1
        _print(True, f"gradio {_version('gradio')} imported from {gradio.__file__}")

        gradio_client, err = _require_import("gradio_client")
        if err:
            _print(False, f"import gradio_client -> {err}")
            return 1
        _print(True, f"gradio-client {_version('gradio-client')} imported from {gradio_client.__file__}")
        if not hasattr(gradio_client, "media_data"):
            _print(False, "gradio_client.media_data is missing; pin gradio-client==0.2.6")
            errors += 1
        else:
            _print(True, "gradio_client.media_data is available")

        pkg_resources, err = _require_import("pkg_resources")
        if err:
            _print(False, f"import pkg_resources -> {err}")
            errors += 1
        else:
            _print(True, f"pkg_resources imported from {pkg_resources.__file__}")

        audioop, err = _require_import("audioop")
        if err:
            _print(False, f"import audioop -> {err}")
            errors += 1
        else:
            _print(True, f"audioop imported from {audioop.__file__}")

        web_mod, err = _require_import("draggan.web")
        if err:
            _print(False, f"import draggan.web -> {err}")
            return 1
        _print(True, f"draggan.web imported from {web_mod.__file__}")
        _print(True, f"draggan.web.main{_sig(web_mod.main)}")

    _print(True, f"load_model{_sig(dg.load_model)}")
    _print(True, f"generate_W{_sig(dg.generate_W)}")
    _print(True, f"generate_image{_sig(dg.generate_image)}")
    _print(True, f"drag_gan{_sig(dg.drag_gan)}")
    _print(True, f"utils.get_path{_sig(utils.get_path)}")
    _print(True, f"utils.BASE_DIR={utils.BASE_DIR}")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
