#!/usr/bin/env python3
"""Check PaddleGAN video/audio stack readiness without running inference."""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from typing import Iterable, List, Sequence, Tuple


def check_import(name: str) -> Tuple[bool, str]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - exercised in live envs
        return False, f"{type(exc).__name__}: {exc}"

    version = getattr(module, "__version__", None)
    if version is None:
        return True, "ok"
    return True, f"ok ({version})"


def check_ffmpeg() -> Tuple[bool, str]:
    exe = shutil.which("ffmpeg")
    if exe is None:
        return False, "ffmpeg not found on PATH"

    proc = subprocess.run([exe, "-version"], capture_output=True, text=True)
    line = ""
    if proc.stdout:
        line = proc.stdout.splitlines()[0]
    elif proc.stderr:
        line = proc.stderr.splitlines()[0]
    detail = exe if not line else f"{exe} | {line}"
    return proc.returncode == 0, detail


def check_paddle() -> Tuple[bool, str]:
    try:
        import paddle
    except Exception as exc:  # pragma: no cover - exercised in live envs
        return False, f"{type(exc).__name__}: {exc}"

    cuda = False
    device_count = 0
    try:
        cuda = paddle.is_compiled_with_cuda()
        if cuda:
            device_count = paddle.device.cuda.device_count()
    except Exception:
        pass

    return True, f"ok (cuda_compiled={cuda}, gpu_devices={device_count})"


def check_face_backends() -> List[Tuple[str, bool, str]]:
    backends = ["sfd", "blazeface"]
    results: List[Tuple[str, bool, str]] = []
    for backend in backends:
        spec = importlib.util.find_spec(
            f"ppgan.faceutils.face_detection.detection.{backend}")
        results.append((backend, spec is not None,
                        "available" if spec is not None else "missing"))
    return results


def probe_video(path: str) -> Tuple[bool, str]:
    if not os.path.exists(path):
        return False, f"video file not found: {path}"

    try:
        import cv2
        import imageio
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"

    details: List[str] = []
    try:
        reader = imageio.get_reader(path)
        meta = reader.get_meta_data()
        fps = meta.get("fps", "unknown")
        nframes = meta.get("nframes", "unknown")
        reader.close()
        details.append(f"imageio fps={fps}, nframes={nframes}")
    except Exception as exc:
        details.append(f"imageio probe failed: {type(exc).__name__}: {exc}")

    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return False, "cv2.VideoCapture could not open the clip"

    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    details.append(f"cv2 {int(width)}x{int(height)} @ {fps:.3f} fps")
    return True, "; ".join(details)


def probe_audio(path: str) -> Tuple[bool, str]:
    if not os.path.exists(path):
        return False, f"audio file not found: {path}"

    try:
        import numpy as np
        import librosa
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"

    try:
        wav, sr = librosa.load(path, sr=16000, mono=True, duration=1.0)
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"

    if wav.size == 0:
        return False, "audio decode returned no samples"
    if np.isnan(wav).any():
        return False, "decoded audio contains NaN values"

    return True, f"decoded {wav.size} samples at {sr} Hz"


def print_section(title: str) -> None:
    print(f"\n== {title} ==")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check PaddleGAN video/audio stack readiness without inference")
    parser.add_argument("--video",
                        action="append",
                        default=[],
                        help="Optional video file to probe")
    parser.add_argument("--audio",
                        action="append",
                        default=[],
                        help="Optional audio file to probe")
    parser.add_argument("--json",
                        action="store_true",
                        help="Emit machine-readable JSON output")
    args = parser.parse_args(argv)

    results = []

    core_checks = [
        ("paddle",) + check_paddle(),
        ("ffmpeg",) + check_ffmpeg(),
        ("imageio",) + check_import("imageio"),
        ("librosa",) + check_import("librosa"),
        ("cv2",) + check_import("cv2"),
        ("ppgan.utils.video",) + check_import("ppgan.utils.video"),
        ("ppgan.utils.audio",) + check_import("ppgan.utils.audio"),
        ("ppgan.faceutils.face_detection.api",) + check_import(
            "ppgan.faceutils.face_detection.api"),
    ]

    predictor_modules = [
        "ppgan.apps.first_order_predictor",
        "ppgan.apps.wav2lip_predictor",
        "ppgan.apps.dain_predictor",
        "ppgan.apps.deepremaster_predictor",
        "ppgan.apps.deoldify_predictor",
        "ppgan.apps.realsr_predictor",
        "ppgan.apps.edvr_predictor",
        "ppgan.apps.recurrent_vsr_predictor",
    ]
    predictor_checks = [(name, *check_import(name)) for name in predictor_modules]

    face_backend_checks = check_face_backends()

    media_checks: List[Tuple[str, bool, str]] = []
    for video_path in args.video:
        media_checks.append((f"video:{video_path}",) + probe_video(video_path))
    for audio_path in args.audio:
        media_checks.append((f"audio:{audio_path}",) + probe_audio(audio_path))

    results.extend(core_checks)
    results.extend(predictor_checks)
    results.extend([(f"face-backend:{backend}", ok, detail)
                    for backend, ok, detail in face_backend_checks])
    results.extend(media_checks)

    if args.json:
        print(
            json.dumps([
                {
                    "name": name,
                    "ok": ok,
                    "detail": detail,
                } for name, ok, detail in results
            ], indent=2, sort_keys=True))
    else:
        print_section("Core stack")
        for name, ok, detail in core_checks:
            status = "OK" if ok else "FAIL"
            print(f"[{status}] {name}: {detail}")

        print_section("Predictor imports")
        for name, ok, detail in predictor_checks:
            status = "OK" if ok else "FAIL"
            print(f"[{status}] {name}: {detail}")

        print_section("Face detector backends")
        for backend, ok, detail in face_backend_checks:
            status = "OK" if ok else "WARN"
            print(f"[{status}] {backend}: {detail}")
        if not any(ok for _, ok, _ in face_backend_checks):
            print("[FAIL] no face detector backend is available")

        if media_checks:
            print_section("Media probes")
            for name, ok, detail in media_checks:
                status = "OK" if ok else "FAIL"
                print(f"[{status}] {name}: {detail}")
        else:
            print_section("Media probes")
            print("[INFO] no media files supplied")

    core_failed = any(not ok for _, ok, _ in core_checks)
    predictor_failed = any(not ok for _, ok, _ in predictor_checks)
    face_backend_failed = not any(ok for _, ok, _ in face_backend_checks)
    media_failed = any(not ok for _, ok, _ in media_checks)

    return 1 if (core_failed or predictor_failed or face_backend_failed or media_failed) else 0


if __name__ == "__main__":
    raise SystemExit(main())
