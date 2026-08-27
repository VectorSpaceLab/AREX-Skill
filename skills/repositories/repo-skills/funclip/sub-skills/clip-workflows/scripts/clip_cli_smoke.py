#!/usr/bin/env python3
"""No-network FunClip clip-workflow smoke test.

This script is deterministic, uses in-memory numpy arrays only, and avoids model
downloads or real media files. It exercises the matching helpers plus the
VideoClipper clipping path.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import os
import sys
import types
from pathlib import Path

import numpy as np


for key, value in {
    "HF_HUB_OFFLINE": "1",
    "TRANSFORMERS_OFFLINE": "1",
    "MODELSCOPE_OFFLINE": "1",
}.items():
    os.environ.setdefault(key, value)


logging.basicConfig(level=logging.ERROR)


class _DummyMediaObject:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.audio = None

    def subclip(self, *args, **kwargs):
        return self

    def set_pos(self, *args, **kwargs):
        return self

    def write_videofile(self, *args, **kwargs):
        return None


def _stub_module(name: str, attrs: dict | None = None) -> types.ModuleType:
    module = types.ModuleType(name)
    if attrs:
        for key, value in attrs.items():
            setattr(module, key, value)
    sys.modules[name] = module
    return module


def ensure_optional_media_deps() -> None:
    if importlib.util.find_spec("librosa") is None:
        _stub_module(
            "librosa",
            {
                "resample": lambda data, orig_sr, target_sr: data,
                "load": lambda path, sr=16000: (np.zeros(1, dtype=np.float32), sr),
            },
        )
    if importlib.util.find_spec("soundfile") is None:
        _stub_module("soundfile", {"write": lambda *args, **kwargs: None})
    if importlib.util.find_spec("moviepy") is None:
        moviepy = _stub_module("moviepy")
        editor = _stub_module(
            "moviepy.editor",
            {
                "VideoFileClip": _DummyMediaObject,
                "concatenate_videoclips": lambda clips: clips[-1] if clips else _DummyMediaObject(),
            },
        )
        video = _stub_module("moviepy.video")
        tools = _stub_module("moviepy.video.tools")
        subtitles = _stub_module(
            "moviepy.video.tools.subtitles",
            {
                "SubtitlesClip": _DummyMediaObject,
                "TextClip": _DummyMediaObject,
            },
        )
        compositing = _stub_module("moviepy.video.compositing")
        composite = _stub_module(
            "moviepy.video.compositing.CompositeVideoClip",
            {"CompositeVideoClip": _DummyMediaObject},
        )
        moviepy.editor = editor
        moviepy.video = video
        video.tools = tools
        tools.subtitles = subtitles
        video.compositing = compositing
        compositing.CompositeVideoClip = composite


def detect_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "funclip" / "videoclipper.py").is_file():
            return parent
    raise RuntimeError(
        "Could not auto-detect the FunClip repository root; pass --repo-root."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a no-network FunClip text-matching smoke test."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Path to the FunClip repository root. Defaults to auto-detection.",
    )
    return parser.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve() if args.repo_root else detect_repo_root()
    funclip_dir = repo_root / "funclip"
    videoclipper_path = funclip_dir / "videoclipper.py"

    require(
        videoclipper_path.is_file(),
        f"Expected {videoclipper_path} to exist. Pass the FunClip repo root with --repo-root.",
    )

    ensure_optional_media_deps()
    sys.path.insert(0, str(funclip_dir))

    from videoclipper import VideoClipper
    from utils.trans_utils import convert_pcm_to_float, pre_proc, proc, proc_spk

    audio = np.arange(4000, dtype=np.float32)
    timestamps = [[0, 100], [100, 200]]
    sentences = [{"text": "HELLO WORLD", "timestamp": timestamps}]
    state = {
        "audio_input": (16000, audio),
        "recog_res_raw": "HELLO WORLD",
        "timestamp": timestamps,
        "sentences": sentences,
    }

    normalized = pre_proc("hello world")
    direct_matches = proc("HELLO WORLD", timestamps, normalized)
    require(direct_matches == [[0, 3200]], f"Unexpected direct match result: {direct_matches!r}")

    no_direct_matches = proc("HELLO WORLD", timestamps, pre_proc("missing text"))
    require(no_direct_matches == [], f"Unexpected no-match result: {no_direct_matches!r}")

    clipper = VideoClipper(None)
    clipper.lang = "en"

    (sample_rate, clipped_audio), match_message, match_srt = clipper.clip(
        "hello world", 0, 0, state
    )
    require(sample_rate == 16000, f"Unexpected sample rate: {sample_rate!r}")
    require(len(clipped_audio) == 3200, f"Unexpected clipped length: {len(clipped_audio)!r}")
    require("1 periods found" in match_message, f"Unexpected match message: {match_message!r}")
    require(
        "00:00:00,000 --> 00:00:00,200" in match_srt,
        f"Unexpected subtitle output: {match_srt!r}",
    )

    (_, raw_audio), no_match_message, no_match_srt = clipper.clip(
        "missing", 0, 0, state
    )
    require(len(raw_audio) == len(audio), "No-match clip should return the original audio.")
    require(
        "No period found" in no_match_message,
        f"Unexpected no-match message: {no_match_message!r}",
    )
    require(no_match_srt == "", f"Unexpected no-match SRT: {no_match_srt!r}")

    speaker_state = [{"spk": 0, "timestamp": [[0, 1200]], "ts_list": [[0, 1200]]}]
    speaker_matches = proc_spk("spk0", speaker_state)
    require(
        speaker_matches == [[0, 19200]],
        f"Unexpected speaker match result: {speaker_matches!r}",
    )

    converted = convert_pcm_to_float(np.array([0, -32768], dtype=np.int16))
    require(converted.dtype == np.float64, f"Unexpected PCM dtype: {converted.dtype!r}")
    require(np.isclose(converted[1], -1.0), f"Unexpected PCM conversion: {converted!r}")

    report = {
        "repo_root": str(repo_root),
        "direct_match_samples": direct_matches,
        "clip_message": match_message,
        "no_match_message": no_match_message,
        "speaker_match_samples": speaker_matches,
        "pcm_dtype": str(converted.dtype),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
