#!/usr/bin/env python3
"""Validate MMSpeech manifest and fbank-config inputs.

This helper checks the three-column TSV layout used by the MMSpeech workflow,
verifies that referenced audio paths exist, and optionally inspects the fbank
configuration for a matching sample rate field.

Example:
  python validate_mmspeech_manifest.py --manifest aishell_train.tsv \
    --audio-col 1 --text-col 2 --speech-id-col 0 --fbank-config fbank_config.yaml
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

try:
    import yaml
except Exception as exc:  # pragma: no cover - helper diagnostics
    yaml = None
    _YAML_IMPORT_ERROR = exc


def _load_yaml(path: Path) -> dict:
    if yaml is None:
        raise RuntimeError(
            "missing optional dependency: PyYAML is required to inspect the fbank config"
        ) from _YAML_IMPORT_ERROR
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a mapping at the top level")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path, help="MMSpeech TSV manifest to validate.")
    parser.add_argument("--speech-id-col", type=int, default=0)
    parser.add_argument("--audio-col", type=int, default=1)
    parser.add_argument("--text-col", type=int, default=2)
    parser.add_argument("--separator", default="\t")
    parser.add_argument("--fbank-config", default=None, type=Path, help="Optional fbank YAML config to inspect.")
    parser.add_argument("--expected-sample-rate", type=int, default=16000)
    parser.add_argument("--max-rows", type=int, default=None)
    args = parser.parse_args()

    try:
        row_count = 0
        with args.manifest.open("r", encoding="utf-8") as handle:
            for row_num, raw_line in enumerate(handle, start=1):
                line = raw_line.rstrip("\n")
                if not line:
                    raise ValueError(f"row {row_num}: blank line encountered")
                cols = line.split(args.separator)
                max_col = max(args.speech_id_col, args.audio_col, args.text_col)
                if len(cols) <= max_col:
                    raise ValueError(f"row {row_num}: expected at least {max_col + 1} columns, found {len(cols)}")
                audio_path = Path(cols[args.audio_col]).expanduser()
                if not audio_path.exists():
                    raise ValueError(f"row {row_num}: audio path does not exist: {audio_path}")
                row_count += 1
                if args.max_rows is not None and row_count >= args.max_rows:
                    break
        if row_count == 0:
            raise ValueError(f"{args.manifest}: file is empty")

        if args.fbank_config is not None:
            cfg = _load_yaml(args.fbank_config)
            sample_rate = cfg.get("sample_rate") or cfg.get("audio_sample_rate")
            if sample_rate is not None and int(sample_rate) != args.expected_sample_rate:
                raise ValueError(
                    f"{args.fbank_config}: sample rate {sample_rate} does not match expected {args.expected_sample_rate}"
                )
        print(f"validated {row_count} rows in {args.manifest}")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
