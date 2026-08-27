#!/usr/bin/env python3
"""Classify a GPT Academic media request and name likely backend checks."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def classify(text: str, file_path: str | None):
    low = text.lower()
    workflows = []
    checks = []
    if any(w in low for w in ["image", "图片", "dall", "画", "generate a picture"]):
        workflows.append("image-generation-or-vision")
        checks += ["GPT/OpenAI-compatible image or vision model", "API key/proxy"]
    if any(w in low for w in ["voice", "microphone", "语音", "麦克风"]):
        workflows.append("voice-assistant")
        checks += ["ENABLE_AUDIO", "browser microphone permission", "speech credentials"]
    if any(w in low for w in ["tts", "speak", "朗读", "配音", "edge"]):
        workflows.append("text-to-speech")
        checks += ["TTS_TYPE", "edge-tts or SoVITS service", "ffmpeg"]
    if any(w in low for w in ["audio", "video", "音频", "视频", "bilibili", "youtube"]):
        workflows.append("audio-video-summary-or-resource")
        checks += ["file/server path", "ffmpeg", "network if external site"]
    if any(w in low for w in ["manim", "animation", "动画"]):
        workflows.append("manim-animation")
        checks += ["manim", "short scene prompt", "rendering time"]
    if file_path:
        p = Path(file_path)
        suffix = p.suffix.lower()
        if suffix in {".mp3", ".wav", ".m4a", ".flac", ".mp4", ".mov", ".mkv"}:
            workflows.append("media-file-summary")
            checks += ["file exists on server", "ffmpeg"]
        elif suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
            workflows.append("image-understanding-or-edit")
            checks.append("vision/image-capable model")
    if not workflows:
        workflows.append("conversation-or-domain-subskill")
    return {"request": text, "file": file_path, "recommended_workflows": sorted(set(workflows)), "backend_checks": sorted(set(checks))}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("text", nargs="*", help="user media request")
    parser.add_argument("--file", help="optional server-visible media path")
    args = parser.parse_args()
    print(json.dumps(classify(" ".join(args.text), args.file), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
