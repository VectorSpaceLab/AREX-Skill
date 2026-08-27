#!/usr/bin/env python3
"""Deterministic smoke checks for FunClip LLM provider routing.

This script does not contact external services. It installs tiny in-process
provider stand-ins, imports the FunClip source from the supplied repository
root, and verifies the model-prefix routing and Pegasus timestamp
normalization that AI Clip depends on.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import os
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch


class FakeOpenAI:
    instances = []

    def __init__(self, api_key=None, base_url=None):
        self.api_key = api_key
        self.base_url = base_url
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))
        FakeOpenAI.instances.append(self)

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))]
        )


class FakeTwelveLabs:
    instances = []

    def __init__(self, api_key=None):
        self.api_key = api_key
        self.analyze_calls = []
        FakeTwelveLabs.instances.append(self)

    def analyze(self, **kwargs):
        self.analyze_calls.append(kwargs)
        return SimpleNamespace(
            data=(
                "1. [12.5-15.0] first highlight\n"
                "2. [120-135] second highlight"
            )
        )


def _install_fake_module(name, **attrs):
    module = ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _prepare_imports(repo_root: Path):
    funclip_root = repo_root / "funclip"
    if not funclip_root.is_dir():
        raise FileNotFoundError(f"Missing FunClip source directory: {funclip_root}")

    sys.path.insert(0, str(funclip_root))

    # Install tiny provider stand-ins before importing the FunClip helpers.
    _install_fake_module("openai", OpenAI=FakeOpenAI)
    _install_fake_module("twelvelabs", TwelveLabs=FakeTwelveLabs)

    from llm.openai_api import (  # type: ignore
        ATLASCLOUD_API_BASE,
        MINIMAX_API_BASE,
        MINIMAX_API_BASE_CN,
        openai_call,
    )
    from llm.twelvelabs_api import (  # type: ignore
        PEGASUS_SYSTEM_PROMPT,
        call_twelvelabs_pegasus,
    )
    from utils.trans_utils import extract_timestamps  # type: ignore

    return {
        "ATLASCLOUD_API_BASE": ATLASCLOUD_API_BASE,
        "MINIMAX_API_BASE": MINIMAX_API_BASE,
        "MINIMAX_API_BASE_CN": MINIMAX_API_BASE_CN,
        "PEGASUS_SYSTEM_PROMPT": PEGASUS_SYSTEM_PROMPT,
        "call_twelvelabs_pegasus": call_twelvelabs_pegasus,
        "extract_timestamps": extract_timestamps,
        "openai_call": openai_call,
        "llm_twelvelabs_api": sys.modules["llm.twelvelabs_api"],
    }


def _reset_fakes():
    FakeOpenAI.instances.clear()
    FakeTwelveLabs.instances.clear()


def _last_openai_instance():
    if not FakeOpenAI.instances:
        raise AssertionError("OpenAI fake was not constructed")
    return FakeOpenAI.instances[-1]


def _last_twelvelabs_instance():
    if not FakeTwelveLabs.instances:
        raise AssertionError("TwelveLabs fake was not constructed")
    return FakeTwelveLabs.instances[-1]


def _check_atlascloud_routing(openai_call, atlas_base):
    _reset_fakes()
    with patch.dict(os.environ, {"ATLASCLOUD_API_KEY": "env-atlas-key"}, clear=False):
        result = openai_call(
            "",
            "atlascloud/qwen/qwen3.5-flash",
            "subtitle text",
            "find highlights",
        )

    client = _last_openai_instance()
    assert result == "ok"
    assert client.api_key == "env-atlas-key"
    assert client.base_url == atlas_base
    assert client.calls[-1]["model"] == "qwen/qwen3.5-flash"


def _check_minimax_routing(openai_call, minimax_base_cn):
    _reset_fakes()
    with patch.dict(
        os.environ,
        {"MINIMAX_API_KEY": "env-minimax-key", "MINIMAX_API_BASE": minimax_base_cn},
        clear=False,
    ):
        result = openai_call(
            "",
            "minimax/MiniMax-M2.7",
            "subtitle text",
            "find highlights",
        )

    client = _last_openai_instance()
    assert result == "ok"
    assert client.api_key == "env-minimax-key"
    assert client.base_url == minimax_base_cn
    assert client.calls[-1]["model"] == "MiniMax-M2.7"


def _check_pegasus_normalization(call_twelvelabs_pegasus, extract_timestamps, pegasus_module):
    _reset_fakes()
    with patch.dict(os.environ, {"TWELVELABS_API_KEY": "env-pegasus-key"}, clear=False):
        with patch.object(pegasus_module, "_resolve_video_context", return_value="video-context"):
            result = call_twelvelabs_pegasus(
                "",
                "dummy-video.mp4",
                prompt="focus on the visual hook",
            )

    client = _last_twelvelabs_instance()
    assert client.api_key == "env-pegasus-key"
    assert client.analyze_calls[-1]["model_name"] == "pegasus1.5"
    assert client.analyze_calls[-1]["video"] == "video-context"
    assert "focus on the visual hook" in client.analyze_calls[-1]["prompt"]
    assert pegasus_module.PEGASUS_SYSTEM_PROMPT in client.analyze_calls[-1]["prompt"]
    assert result == (
        "1. [00:00:12,500-00:00:15,000] first highlight\n"
        "2. [00:02:00,000-00:02:15,000] second highlight"
    )

    with contextlib.redirect_stdout(io.StringIO()):
        timestamps = extract_timestamps(result)
    assert timestamps == [[12500, 15000], [120000, 135000]]


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Smoke-test FunClip LLM provider routing without API calls."
    )
    parser.add_argument(
        "--repo-root",
        required=True,
        type=Path,
        help="Path to the FunClip repository root that contains the funclip/ directory.",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.expanduser().resolve()
    modules = _prepare_imports(repo_root)

    _check_atlascloud_routing(modules["openai_call"], modules["ATLASCLOUD_API_BASE"])
    _check_minimax_routing(modules["openai_call"], modules["MINIMAX_API_BASE_CN"])
    _check_pegasus_normalization(
        modules["call_twelvelabs_pegasus"],
        modules["extract_timestamps"],
        modules["llm_twelvelabs_api"],
    )

    print("provider_route_smoke: all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
