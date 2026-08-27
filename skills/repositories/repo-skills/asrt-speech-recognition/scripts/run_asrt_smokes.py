#!/usr/bin/env python3
"""Run self-contained smoke checks for bundled ASRT repo-skill helpers."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]


def run_case(name: str, command: List[str]) -> Dict[str, Any]:
    proc = subprocess.run(command, cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    return {
        "name": name,
        "command": command,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip()[:1000],
        "stderr": proc.stderr.strip()[:1000],
        "ok": proc.returncode == 0,
    }


def main() -> int:
    py = sys.executable
    cases = [
        [py, "sub-skills/language-model/scripts/decode_pinyin.py", "ni3", "hao3", "ya5"],
        [py, "sub-skills/data-and-features/scripts/inspect_audio_features.py", "--synthesize-zero", "1", "--features", "spectrogram"],
        [py, "sub-skills/data-and-features/scripts/validate_asrt_config.py", "--help"],
        [py, "sub-skills/acoustic-models/scripts/inspect_keras_model.py", "--help"],
        [py, "sub-skills/acoustic-models/scripts/predict_file_template.py", "--help"],
        [py, "sub-skills/serving-clients/scripts/make_http_payload.py", "--endpoint", "/language", "--sequence-pinyin", "ni3", "hao3", "ya5"],
        [py, "sub-skills/serving-clients/scripts/asrt_http_client.py", "--help"],
    ]
    names = [
        "language_decode",
        "feature_spectrogram",
        "config_validator_help",
        "keras_inspector_help",
        "predict_template_help",
        "http_language_payload",
        "http_client_help",
    ]
    results = [run_case(name, command) for name, command in zip(names, cases)]
    print(json.dumps({"root": str(ROOT), "results": results}, ensure_ascii=False, indent=2))
    return 0 if all(item["ok"] for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
