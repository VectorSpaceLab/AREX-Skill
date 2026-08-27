#!/usr/bin/env python3
"""Read-only Coqui TTS model-registry inspector.

This helper lists, counts, filters, and queries the installed Coqui TTS model
registry. It never calls ModelManager.download_model and therefore does not
trigger model downloads or TOS prompts.

Examples:
  python scripts/inspect_tts_models.py --count
  python scripts/inspect_tts_models.py --type tts_models --contains xtts --format table
  python scripts/inspect_tts_models.py --query tts_models/en/ljspeech/tacotron2-DDC --format json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

MODEL_TYPES = ("tts_models", "vocoder_models", "voice_conversion_models")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect the installed Coqui TTS model registry without downloading weights."
    )
    parser.add_argument(
        "--type",
        choices=("all",) + MODEL_TYPES,
        default="all",
        help="Registry section to inspect. Default: all.",
    )
    parser.add_argument(
        "--contains",
        default=None,
        help="Case-insensitive substring filter applied to full model names and descriptions.",
    )
    parser.add_argument(
        "--query",
        default=None,
        help="Full model name to query, e.g. tts_models/en/ljspeech/tacotron2-DDC.",
    )
    parser.add_argument(
        "--count",
        action="store_true",
        help="Print counts for the selected registry type before any listed matches.",
    )
    parser.add_argument(
        "--format",
        choices=("table", "json", "names"),
        default="table",
        help="Output format. Default: table.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Maximum number of listed matches. 0 means no limit. Default: 0.",
    )
    parser.add_argument(
        "--models-json",
        type=Path,
        default=None,
        help="Optional explicit registry JSON path for controlled inspections. Defaults to the installed package registry.",
    )
    return parser.parse_args(argv)


def fail(message: str, code: int = 2) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def build_manager(models_json: Optional[Path]):
    try:
        import TTS  # type: ignore
        from TTS.utils.manage import ModelManager  # type: ignore
    except Exception as exc:  # noqa: BLE001 - present a clean user-facing error
        fail(
            "Could not import the Coqui TTS package. Install distribution 'TTS' "
            "in a supported Python 3.9-3.11 environment before registry inspection. "
            f"Import error: {exc.__class__.__name__}: {exc}"
        )

    if models_json is None:
        package_file = getattr(TTS, "__file__", None)
        if not package_file:
            fail("Imported TTS package does not expose a package file for locating the registry.")
        models_json = Path(package_file).resolve().parent / ".models.json"

    try:
        return ModelManager(models_file=models_json, progress_bar=False, verbose=False)
    except Exception as exc:  # noqa: BLE001
        fail(f"Could not read the model registry. {exc.__class__.__name__}: {exc}")


def iter_entries(models_dict: Dict[str, Any], selected_type: str) -> Iterable[Dict[str, Any]]:
    types = MODEL_TYPES if selected_type == "all" else (selected_type,)
    for model_type in types:
        for language, datasets in models_dict.get(model_type, {}).items():
            for dataset, models in datasets.items():
                for model_name, item in models.items():
                    item = dict(item)
                    url_value = item.get("github_rls_url", item.get("hf_url"))
                    if isinstance(url_value, list):
                        download_shape = "multi-file"
                    elif url_value:
                        download_shape = "archive-or-file"
                    elif "fairseq" in f"{dataset}/{model_name}":
                        download_shape = "dynamic"
                    else:
                        download_shape = "none-or-implicit"
                    yield {
                        "name": f"{model_type}/{language}/{dataset}/{model_name}",
                        "model_type": model_type,
                        "language": language,
                        "dataset": dataset,
                        "model": model_name,
                        "description": item.get("description"),
                        "default_vocoder": item.get("default_vocoder"),
                        "license": item.get("license"),
                        "tos_required": bool(item.get("tos_required", False)),
                        "download_shape": download_shape,
                        "model_hash_present": "model_hash" in item,
                    }


def dynamic_query(query: str) -> Optional[Dict[str, Any]]:
    parts = query.split("/")
    if len(parts) == 4 and parts[0] == "tts_models" and parts[2] == "fairseq" and parts[3] == "vits":
        return {
            "name": query,
            "model_type": "tts_models",
            "language": parts[1],
            "dataset": "fairseq",
            "model": "vits",
            "description": "Dynamic Fairseq MMS VITS name handled by ModelManager at download/load time.",
            "default_vocoder": None,
            "license": "CC BY-NC 4.0",
            "tos_required": False,
            "download_shape": "dynamic-model-directory",
            "model_hash_present": False,
            "dynamic": True,
            "caution": "Verify the ISO language code before approving download; not every Fairseq language is enumerated in the static registry list.",
        }

    if "xtts" in query and len(parts) != 4:
        version = "main"
        match = re.search(r"v\d+\.\d+\.\d+", query)
        if match:
            version = match.group(0)
        return {
            "name": query,
            "model_type": "tts_models",
            "language": "multilingual",
            "dataset": "multi-dataset",
            "model": query,
            "description": "XTTS shorthand accepted by ModelManager at download/load time.",
            "default_vocoder": None,
            "license": "CPML",
            "tos_required": True,
            "download_shape": "dynamic-multi-file-model-directory",
            "model_hash_present": False,
            "dynamic": True,
            "version": version,
            "caution": "Prefer the full registry name for reproducibility unless the user explicitly wants an XTTS alias.",
        }
    return None


def counts(entries: List[Dict[str, Any]]) -> Dict[str, int]:
    result = {model_type: 0 for model_type in MODEL_TYPES}
    for entry in entries:
        result[entry["model_type"]] = result.get(entry["model_type"], 0) + 1
    result["total"] = sum(result.values())
    return result


def apply_filters(entries: List[Dict[str, Any]], contains: Optional[str], limit: int) -> List[Dict[str, Any]]:
    if contains:
        needle = contains.lower()
        entries = [
            entry
            for entry in entries
            if needle in entry["name"].lower() or needle in str(entry.get("description") or "").lower()
        ]
    if limit and limit > 0:
        entries = entries[:limit]
    return entries


def table_output(entries: List[Dict[str, Any]], include_description: bool = False) -> str:
    if not entries:
        return "No matching models."
    headers = ["name", "license", "tos", "default_vocoder", "download_shape"]
    if include_description:
        headers.append("description")
    rows = []
    for entry in entries:
        row = [
            entry["name"],
            str(entry.get("license") or ""),
            "yes" if entry.get("tos_required") else "no",
            str(entry.get("default_vocoder") or ""),
            str(entry.get("download_shape") or ""),
        ]
        if include_description:
            row.append(str(entry.get("description") or ""))
        rows.append(row)
    widths = [len(header) for header in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = min(max(widths[idx], len(cell)), 80)

    def fmt_row(values: List[str]) -> str:
        clipped = [value if len(value) <= widths[idx] else value[: widths[idx] - 1] + "…" for idx, value in enumerate(values)]
        return " | ".join(value.ljust(widths[idx]) for idx, value in enumerate(clipped))

    lines = [fmt_row(headers), "-+-".join("-" * width for width in widths)]
    lines.extend(fmt_row(row) for row in rows)
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    manager = build_manager(args.models_json)
    all_entries = list(iter_entries(manager.models_dict, args.type))

    if args.query:
        matching = [entry for entry in all_entries if entry["name"] == args.query]
        if not matching:
            dynamic = dynamic_query(args.query)
            if dynamic is not None:
                matching = [dynamic]
        if not matching:
            suggestions = apply_filters(all_entries, args.query.split("/")[-1], 5)
            payload = {
                "query": args.query,
                "found": False,
                "message": "Model not found in the selected static registry type. Check name grammar or dynamic Fairseq/XTTS rules.",
                "suggestions": [entry["name"] for entry in suggestions],
            }
            if args.format == "json":
                print(json.dumps(payload, indent=2, sort_keys=True))
            else:
                print(payload["message"])
                if payload["suggestions"]:
                    print("Suggestions:")
                    for name in payload["suggestions"]:
                        print(f"  {name}")
            return 1
        entries = matching
    else:
        entries = apply_filters(all_entries, args.contains, args.limit)

    selected_counts = counts(all_entries)

    if args.format == "json":
        print(json.dumps({"counts": selected_counts, "models": entries}, indent=2, sort_keys=True))
        return 0

    if args.count:
        print("Counts:")
        for key in (*MODEL_TYPES, "total"):
            print(f"  {key}: {selected_counts.get(key, 0)}")
        if entries:
            print()

    if args.format == "names":
        for entry in entries:
            print(entry["name"])
    else:
        print(table_output(entries, include_description=bool(args.query)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
