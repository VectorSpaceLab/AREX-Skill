#!/usr/bin/env python3
"""No-network FunClip runtime/environment check.

This bundled helper validates the local checkout structure, declared dependency
constraints, import surface, launch policy, and ASR model-selection routing. It
uses a fake AutoModel, so it does not download model weights or contact LLM
providers.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable


def candidate_roots(explicit: Path | None) -> Iterable[Path]:
    if explicit is not None:
        yield explicit
    yield Path.cwd()
    here = Path(__file__).resolve()
    yield from here.parents


def find_repo_root(explicit: Path | None) -> Path:
    for candidate in candidate_roots(explicit):
        root = candidate.expanduser().resolve()
        if (root / "funclip" / "launch.py").is_file() and (root / "requirements.txt").is_file():
            return root
    raise FileNotFoundError(
        "Could not find a FunClip checkout; pass --repo-root pointing to a directory "
        "that contains funclip/launch.py and requirements.txt."
    )


def version_of(module_name: str):
    module = importlib.import_module(module_name)
    return getattr(module, "__version__", None)


def binary_version(binary: str):
    path = shutil.which(binary)
    if not path:
        return None
    try:
        proc = subprocess.run(
            [path, "-version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception as exc:  # pragma: no cover - diagnostic fallback
        return {"path": path, "error": str(exc)}
    first_line = (proc.stdout or proc.stderr).splitlines()[0] if (proc.stdout or proc.stderr) else ""
    return {"path": path, "first_line": first_line, "returncode": proc.returncode}


class RecordingAutoModel:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Check FunClip imports and launch/model-selection contracts without downloads."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Path to a FunClip checkout. Defaults to auto-detection from cwd or this script path.",
    )
    parser.add_argument(
        "--check-binaries",
        action="store_true",
        help="Also report ffmpeg and ImageMagick convert/magick availability.",
    )
    args = parser.parse_args(argv)

    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    os.environ.setdefault("MODELSCOPE_OFFLINE", "1")

    repo_root = find_repo_root(args.repo_root)
    requirements = (repo_root / "requirements.txt").read_text(encoding="utf-8")
    required_markers = [
        "funasr>=1.3.29",
        "gradio>=4.31.3,<5.0",
        "starlette<1.0",
        "moviepy==1.0.3",
        "numpy==1.26.4",
    ]
    missing_markers = [marker for marker in required_markers if marker not in requirements]
    if missing_markers:
        raise AssertionError("requirements.txt is missing expected markers: " + ", ".join(missing_markers))

    sys.path.insert(0, str(repo_root / "funclip"))

    imported = []
    for module_name in [
        "launch_config",
        "utils.trans_utils",
        "utils.subtitle_utils",
        "videoclipper",
        "launch",
        "llm.openai_api",
        "llm.litellm_api",
        "llm.twelvelabs_api",
    ]:
        importlib.import_module(module_name)
        imported.append(module_name)

    from launch import create_asr_model  # type: ignore
    from launch_config import build_launch_kwargs  # type: ignore

    nano = create_asr_model("fun-asr-nano", "en", auto_model_cls=RecordingAutoModel)
    sensevoice = create_asr_model("sensevoice", "en", auto_model_cls=RecordingAutoModel)
    paraformer_en = create_asr_model("paraformer", "en", auto_model_cls=RecordingAutoModel)

    assert nano.kwargs["model"] == "FunAudioLLM/Fun-ASR-Nano-2512"
    assert nano.kwargs["hub"] == "hf"
    assert sensevoice.kwargs["model"] == "iic/SenseVoiceSmall"
    assert paraformer_en.kwargs["model"] == "iic/speech_paraformer_asr-en-16k-vocab4199-pytorch"

    local_launch = build_launch_kwargs(share=False, port=7860, listen=False)
    listen_launch = build_launch_kwargs(share=True, port=7860, listen=True)
    assert local_launch == {
        "share": False,
        "server_port": 7860,
        "server_name": "127.0.0.1",
    }
    assert listen_launch["share"] is True
    assert listen_launch["server_name"] == "0.0.0.0"
    assert listen_launch["inbrowser"] is False
    assert listen_launch["_frontend"] is False

    report = {
        "status": "ok",
        "repo_root": str(repo_root),
        "imported_modules": imported,
        "versions": {
            "funasr": version_of("funasr"),
            "gradio": version_of("gradio"),
            "starlette": version_of("starlette"),
            "openai": version_of("openai"),
            "twelvelabs": version_of("twelvelabs"),
        },
        "requirements_markers": required_markers,
        "launch_kwargs": {"local": local_launch, "listen": listen_launch},
        "model_selection": {
            "fun_asr_nano": nano.kwargs,
            "sensevoice": sensevoice.kwargs,
            "paraformer_en": paraformer_en.kwargs,
        },
    }
    if args.check_binaries:
        report["binaries"] = {
            "ffmpeg": binary_version("ffmpeg"),
            "convert": binary_version("convert"),
            "magick": binary_version("magick"),
        }

    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
