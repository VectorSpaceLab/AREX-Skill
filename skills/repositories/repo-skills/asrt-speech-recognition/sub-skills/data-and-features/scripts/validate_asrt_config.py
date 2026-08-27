#!/usr/bin/env python3
"""Validate ASRT config, dictionary, wav-list, and syllable-label files.

This script is self-contained and does not import ASRT. It mirrors the data
contract used by ASRT's config utilities and DataLoader while adding explicit
checks for common custom-dataset mistakes.
"""

from __future__ import annotations

import argparse
import json
import sys
import wave
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


REQUIRED_DATASET_KEYS = ("name", "data_list", "data_path", "label_list")


def resolve_path(path_text: str, base_dir: Path) -> Path:
    path = Path(path_text).expanduser()
    return path if path.is_absolute() else base_dir / path


def add_issue(issues: List[Dict[str, Any]], level: str, where: str, message: str) -> None:
    issues.append({"level": level, "where": where, "message": message})


def load_json_config(path: Path, issues: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not path.exists():
        add_issue(issues, "error", str(path), "config file does not exist")
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception as exc:  # noqa: BLE001 - report config parse failures clearly
        add_issue(issues, "error", str(path), f"could not read JSON config: {exc}")
        return None
    if not isinstance(data, dict):
        add_issue(issues, "error", str(path), "config root must be a JSON object")
        return None
    return data


def load_pinyin_dict(path: Path, issues: List[Dict[str, Any]]) -> Tuple[List[str], Dict[str, int]]:
    pinyin_list: List[str] = []
    pinyin_dict: Dict[str, int] = {}
    if not path.exists():
        add_issue(issues, "error", str(path), "dictionary file does not exist")
        return pinyin_list, pinyin_dict
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception as exc:  # noqa: BLE001
        add_issue(issues, "error", str(path), f"could not read dictionary: {exc}")
        return pinyin_list, pinyin_dict

    for line_no, line in enumerate(lines, 1):
        if not line:
            continue
        if "\t" not in line:
            add_issue(issues, "error", f"{path}:{line_no}", "dictionary row must contain a tab separator")
            continue
        pinyin, chars = line.split("\t", 1)
        if not pinyin:
            add_issue(issues, "error", f"{path}:{line_no}", "dictionary pinyin token is empty")
            continue
        if not chars:
            add_issue(issues, "warning", f"{path}:{line_no}", "dictionary character column is empty")
        if pinyin in pinyin_dict:
            add_issue(
                issues,
                "warning",
                f"{path}:{line_no}",
                f"duplicate pinyin token {pinyin!r}; ASRT keeps the row in pinyin_list and maps the token to the last occurrence",
            )
        pinyin_dict[pinyin] = len(pinyin_list)
        pinyin_list.append(pinyin)
    return pinyin_list, pinyin_dict


def duplicate_values(values: Iterable[str]) -> List[str]:
    counts = Counter(values)
    return sorted([value for value, count in counts.items() if count > 1])


def parse_wav_list(path: Path, issues: List[Dict[str, Any]]) -> Dict[str, str]:
    rows: Dict[str, str] = {}
    ids: List[str] = []
    if not path.exists():
        add_issue(issues, "error", str(path), "wav list file does not exist")
        return rows
    try:
        lines = path.read_text(encoding="utf-8").split("\n")
    except Exception as exc:  # noqa: BLE001
        add_issue(issues, "error", str(path), f"could not read wav list: {exc}")
        return rows

    for line_no, line in enumerate(lines, 1):
        if len(line) == 0:
            continue
        parts = line.split(" ")
        if len(parts) != 2 or not parts[0] or not parts[1]:
            add_issue(
                issues,
                "error",
                f"{path}:{line_no}",
                "wav-list row must be exactly '<sample_id> <relative_wav_path>' with one space separator",
            )
            continue
        sample_id, rel_wav = parts
        ids.append(sample_id)
        rows[sample_id] = rel_wav

    for dup in duplicate_values(ids)[:20]:
        add_issue(issues, "error", str(path), f"duplicate wav-list sample id {dup!r}")
    return rows


def parse_label_list(path: Path, issues: List[Dict[str, Any]], pinyin_dict: Dict[str, int]) -> Dict[str, List[str]]:
    rows: Dict[str, List[str]] = {}
    ids: List[str] = []
    if not path.exists():
        add_issue(issues, "error", str(path), "label list file does not exist")
        return rows
    try:
        lines = path.read_text(encoding="utf-8").split("\n")
    except Exception as exc:  # noqa: BLE001
        add_issue(issues, "error", str(path), f"could not read label list: {exc}")
        return rows

    missing_tokens: Dict[str, List[int]] = {}
    for line_no, line in enumerate(lines, 1):
        if len(line) == 0:
            continue
        parts = line.split(" ")
        if not parts[0]:
            add_issue(issues, "error", f"{path}:{line_no}", "label-list sample id is empty")
            continue
        sample_id = parts[0]
        labels = [token for token in parts[1:] if token]
        if not labels:
            add_issue(issues, "warning", f"{path}:{line_no}", f"sample id {sample_id!r} has no pinyin labels")
        ids.append(sample_id)
        rows[sample_id] = labels
        for token in labels:
            if token not in pinyin_dict:
                missing_tokens.setdefault(token, []).append(line_no)

    for dup in duplicate_values(ids)[:20]:
        add_issue(issues, "error", str(path), f"duplicate label-list sample id {dup!r}")
    for token, line_numbers in sorted(missing_tokens.items())[:50]:
        preview = ",".join(str(n) for n in line_numbers[:5])
        add_issue(issues, "error", str(path), f"pinyin token {token!r} not found in dictionary; example line(s): {preview}")
    return rows


def inspect_wav(path: Path) -> Dict[str, Any]:
    with wave.open(str(path), "rb") as wav:
        frames = wav.getnframes()
        rate = wav.getframerate()
        channels = wav.getnchannels()
        width = wav.getsampwidth()
    return {
        "path": str(path),
        "frames": frames,
        "sample_rate": rate,
        "channels": channels,
        "byte_width": width,
        "duration_seconds": frames / rate if rate else None,
    }


def validate_descriptor(
    descriptor: Any,
    split: str,
    index: int,
    base_dir: Path,
    pinyin_dict: Dict[str, int],
    args: argparse.Namespace,
    issues: List[Dict[str, Any]],
) -> Dict[str, Any]:
    where = f"dataset.{split}[{index}]"
    summary: Dict[str, Any] = {"split": split, "index": index, "ok": False}
    if not isinstance(descriptor, dict):
        add_issue(issues, "error", where, "dataset descriptor must be an object")
        return summary
    for key in REQUIRED_DATASET_KEYS:
        if key not in descriptor:
            add_issue(issues, "error", where, f"missing required key {key!r}")
    if any(key not in descriptor for key in REQUIRED_DATASET_KEYS):
        return summary

    name = str(descriptor["name"])
    data_path = resolve_path(str(descriptor["data_path"]), base_dir)
    wav_list_path = resolve_path(str(descriptor["data_list"]), base_dir)
    label_list_path = resolve_path(str(descriptor["label_list"]), base_dir)
    wav_rows = parse_wav_list(wav_list_path, issues)
    label_rows = parse_label_list(label_list_path, issues, pinyin_dict)

    wav_ids = set(wav_rows)
    label_ids = set(label_rows)
    for missing in sorted(wav_ids - label_ids)[:50]:
        add_issue(issues, "error", name, f"wav-list id {missing!r} is missing from label list")
    for extra in sorted(label_ids - wav_ids)[:50]:
        add_issue(issues, "error", name, f"label-list id {extra!r} is missing from wav list")

    audio_missing = 0
    audio_probed = 0
    audio_metadata: List[Dict[str, Any]] = []
    probe_limit = max(args.max_audio_probe, 0)
    for sample_id, rel_wav in wav_rows.items():
        wav_path = data_path / rel_wav
        exists = wav_path.exists()
        if args.check_audio_exists and not exists:
            audio_missing += 1
            if audio_missing <= 50:
                add_issue(issues, "error", name, f"audio file for id {sample_id!r} does not exist: {wav_path}")
        if probe_limit and exists and audio_probed < probe_limit:
            try:
                meta = inspect_wav(wav_path)
                meta["sample_id"] = sample_id
                audio_metadata.append(meta)
                audio_probed += 1
                if args.expect_sample_rate and meta["sample_rate"] != args.expect_sample_rate:
                    add_issue(
                        issues,
                        "error",
                        str(wav_path),
                        f"sample rate {meta['sample_rate']} != expected {args.expect_sample_rate}",
                    )
            except Exception as exc:  # noqa: BLE001
                add_issue(issues, "error", str(wav_path), f"could not inspect wav metadata: {exc}")

    summary.update(
        {
            "ok": True,
            "name": name,
            "data_path": str(data_path),
            "data_list": str(wav_list_path),
            "label_list": str(label_list_path),
            "wav_rows": len(wav_rows),
            "label_rows": len(label_rows),
            "matched_ids": len(wav_ids & label_ids),
            "audio_missing": audio_missing if args.check_audio_exists else None,
            "audio_probed": audio_probed,
            "audio_metadata": audio_metadata,
        }
    )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate ASRT asrt_config.json, dict.txt, datalist, label-list, and optional WAV metadata.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--config", default="asrt_config.json", help="ASRT JSON config path")
    parser.add_argument("--base-dir", default=None, help="Base directory for relative config/list/dict paths; defaults to config parent")
    parser.add_argument("--dict", dest="dict_path", default=None, help="Override dictionary path instead of config['dict_filename']")
    parser.add_argument("--split", action="append", default=None, help="Dataset split key to validate; repeatable; defaults to all splits in config")
    parser.add_argument("--check-audio-exists", action="store_true", help="Check that resolved WAV files exist")
    parser.add_argument("--max-audio-probe", type=int, default=0, help="Inspect metadata for up to N existing WAV files per descriptor")
    parser.add_argument("--expect-sample-rate", type=int, default=None, help="Expected WAV sample rate when probing metadata, e.g. 16000")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    issues: List[Dict[str, Any]] = []
    config_path = Path(args.config).expanduser().resolve()
    base_dir = Path(args.base_dir).expanduser().resolve() if args.base_dir else config_path.parent

    config = load_json_config(config_path, issues)
    result: Dict[str, Any] = {
        "config": str(config_path),
        "base_dir": str(base_dir),
        "dictionary": None,
        "dictionary_entries": 0,
        "splits": [],
        "issues": issues,
    }
    if config is None:
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print_issues(issues)
        return 1

    if "dict_filename" not in config and not args.dict_path:
        add_issue(issues, "error", str(config_path), "missing top-level 'dict_filename'")
        dict_path = base_dir / "dict.txt"
    else:
        dict_path = resolve_path(args.dict_path or str(config.get("dict_filename")), base_dir)
    pinyin_list, pinyin_dict = load_pinyin_dict(dict_path, issues)
    result["dictionary"] = str(dict_path)
    result["dictionary_entries"] = len(pinyin_list)

    dataset = config.get("dataset")
    if not isinstance(dataset, dict):
        add_issue(issues, "error", str(config_path), "top-level 'dataset' must be an object")
    else:
        splits = args.split or list(dataset.keys())
        for split in splits:
            if split not in dataset:
                add_issue(issues, "error", f"dataset.{split}", "split is not present in config")
                continue
            descriptors = dataset[split]
            if not isinstance(descriptors, list):
                add_issue(issues, "error", f"dataset.{split}", "split value must be a list")
                continue
            for index, descriptor in enumerate(descriptors):
                result["splits"].append(validate_descriptor(descriptor, split, index, base_dir, pinyin_dict, args, issues))

    has_error = any(issue["level"] == "error" for issue in issues)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Config: {config_path}")
        print(f"Base dir: {base_dir}")
        print(f"Dictionary: {dict_path} ({len(pinyin_list)} entries)")
        for item in result["splits"]:
            if not item.get("ok"):
                continue
            print(
                "Split {split} descriptor {index} {name}: wav_rows={wav_rows}, label_rows={label_rows}, "
                "matched_ids={matched_ids}, audio_probed={audio_probed}".format(**item)
            )
            if item.get("audio_missing") is not None:
                print(f"  missing audio files: {item['audio_missing']}")
            for meta in item.get("audio_metadata", []):
                print(
                    f"  {meta['sample_id']}: rate={meta['sample_rate']}Hz channels={meta['channels']} "
                    f"byte_width={meta['byte_width']} frames={meta['frames']} duration={meta['duration_seconds']:.3f}s"
                )
        print_issues(issues)
        print("Result:", "FAIL" if has_error else "PASS")
    return 1 if has_error else 0


def print_issues(issues: List[Dict[str, Any]]) -> None:
    if not issues:
        print("Issues: none")
        return
    print("Issues:")
    for issue in issues:
        print(f"  [{issue['level']}] {issue['where']}: {issue['message']}")


if __name__ == "__main__":
    raise SystemExit(main())
