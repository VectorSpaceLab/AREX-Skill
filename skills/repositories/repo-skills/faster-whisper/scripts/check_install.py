#!/usr/bin/env python3
"""Inspect a faster-whisper installation from the active environment.

This helper prints the installed package version, public exports, model aliases,
CTranslate2 compute support, and basic VAD import health. It is safe to run with
--help and does not depend on the original repository checkout.
"""

from __future__ import annotations

import argparse
from importlib.metadata import PackageNotFoundError, version


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check a faster-whisper installation."
    )
    parser.add_argument(
        "--show-models",
        action="store_true",
        help="Print the available model aliases.",
    )
    parser.add_argument(
        "--show-compute-types",
        action="store_true",
        help="Print CTranslate2 CPU/CUDA compute-type support.",
    )
    args = parser.parse_args(argv)

    try:
        import faster_whisper
        from faster_whisper import available_models
        from faster_whisper.vad import VadOptions, get_speech_timestamps
    except Exception as exc:  # noqa: BLE001 - helper should show a concise failure
        raise SystemExit(f"failed to import faster-whisper: {exc}") from exc

    print(f"faster-whisper: {version('faster-whisper')}")
    print(f"module: {faster_whisper.__name__}")
    print(f"exports: {', '.join(faster_whisper.__all__)}")
    print(f"model-count: {len(available_models())}")

    if args.show_models:
        print("models:")
        for name in available_models():
            print(f"  - {name}")

    if args.show_compute_types:
        try:
            import ctranslate2
        except Exception as exc:  # noqa: BLE001
            print(f"ctranslate2: import failed: {exc}")
        else:
            for device in ("cpu", "cuda"):
                try:
                    supported = sorted(ctranslate2.get_supported_compute_types(device))
                    print(f"{device}: {supported}")
                except Exception as exc:  # noqa: BLE001
                    print(f"{device}: unavailable: {exc}")

    try:
        import numpy as np

        silent = np.zeros(16000, dtype=np.float32)
        vad = get_speech_timestamps(silent, VadOptions(min_silence_duration_ms=100))
        print(f"vad-empty-audio: {vad}")
    except Exception as exc:  # noqa: BLE001
        print(f"vad-empty-audio: failed: {exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
