#!/usr/bin/env python3
"""Build a VLMEvalKit TSV for LongDocURL-style JSONL data.

The safe default is local mode:

    python build_longdocurl_tsv.py --jsonl LongDocURL.jsonl --output LongDocURL.tsv

If --jsonl is omitted, the script optionally downloads the public JSONL from
Hugging Face. Image archives are intentionally not downloaded or extracted here;
prepare image files separately and use --image-root only to validate paths.
"""

from __future__ import annotations

import argparse
import json
import os
import os.path as osp
import sys
from pathlib import Path
from typing import Any

import pandas as pd


REPO_ID = "dengchao/LongDocURL"
DATA_FILE = "LongDocURL_public_with_subtask_category.jsonl"

OUTPUT_COLUMNS = [
    "index",
    "question_id",
    "question",
    "answer",
    "image_path",
    "doc_no",
    "total_pages",
    "start_end_idx",
    "question_type",
    "answer_format",
    "task_tag",
    "evidence_pages",
    "evidence_sources",
    "subTask",
    "detailed_evidences",
    "pdf_path",
]


class ConversionError(RuntimeError):
    """Raised when a source file cannot be converted safely."""


def hf_download(filename: str, download_dir: str, token: str | None = None) -> str:
    """Download one public LongDocURL file from Hugging Face."""
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as err:  # pragma: no cover - exercised only without optional dep
        raise ImportError(
            "huggingface_hub is required to download LongDocURL. "
            "Install it with `pip install huggingface_hub`, or pass --jsonl."
        ) from err

    return hf_hub_download(
        repo_id=REPO_ID,
        filename=filename,
        repo_type="dataset",
        local_dir=download_dir,
        token=token,
    )


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def relative_image_path(path: Any) -> str:
    """Normalize LongDocURL image references relative to the pdf_pngs root."""
    text = str(path).replace("\\", "/").strip()
    marker = "/pdf_pngs/"
    if marker in text:
        return text.split(marker, 1)[1]
    if text.startswith("pdf_pngs/"):
        return text.split("pdf_pngs/", 1)[1]
    return text.lstrip("/")


def row_from_sample(sample: dict[str, Any], idx: int) -> dict[str, Any]:
    images = [relative_image_path(p) for p in as_list(sample.get("images", [])) if str(p).strip()]
    answer = sample.get("answer", "")
    if isinstance(answer, (list, dict)):
        answer = json_dumps(answer)

    row = {
        "index": idx,
        "question_id": sample.get("question_id", ""),
        "question": sample.get("question", ""),
        "answer": answer,
        "image_path": json_dumps(images),
        "doc_no": sample.get("doc_no", ""),
        "total_pages": sample.get("total_pages", ""),
        "start_end_idx": json_dumps(sample.get("start_end_idx", [])),
        "question_type": sample.get("question_type", ""),
        "answer_format": sample.get("answer_format", ""),
        "task_tag": sample.get("task_tag", ""),
        "evidence_pages": json_dumps(sample.get("evidence_pages", [])),
        "evidence_sources": json_dumps(sample.get("evidence_sources", [])),
        "subTask": json_dumps(sample.get("subTask", [])),
        "detailed_evidences": sample.get("detailed_evidences", ""),
        "pdf_path": sample.get("pdf_path", ""),
    }
    return {col: row.get(col, "") for col in OUTPUT_COLUMNS}


def load_jsonl(path: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as err:
                raise ConversionError(f"Invalid JSON on line {line_no}: {err}") from err
            if not isinstance(obj, dict):
                raise ConversionError(f"Line {line_no} is {type(obj).__name__}, expected object")
            rows.append(obj)
    return rows


def validate_rows(rows: list[dict[str, Any]], *, strict: bool = False) -> None:
    problems: list[str] = []
    for row in rows:
        idx = row["index"]
        if not str(row.get("question", "")).strip():
            problems.append(f"row {idx}: empty question")
        try:
            images = json.loads(row.get("image_path", "[]"))
        except Exception as err:
            problems.append(f"row {idx}: image_path is not valid JSON: {err}")
            continue
        if not isinstance(images, list):
            problems.append(f"row {idx}: image_path JSON must be a list")
    if problems:
        preview = "\n".join(problems[:10])
        message = f"Detected {len(problems)} row issue(s):\n{preview}"
        if strict:
            raise ConversionError(message)
        print(f"warning: {message}", file=sys.stderr)


def validate_image_root(rows: list[dict[str, Any]], image_root: str, *, strict: bool = False) -> None:
    root = Path(image_root)
    missing: list[str] = []
    for row in rows:
        for rel in json.loads(row["image_path"]):
            candidate = root / rel
            if not candidate.exists():
                missing.append(str(candidate))
                if len(missing) >= 20:
                    break
        if len(missing) >= 20:
            break
    if missing:
        message = "Missing image files under --image-root; first examples:\n" + "\n".join(missing[:10])
        if strict:
            raise ConversionError(message)
        print(f"warning: {message}", file=sys.stderr)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a VLMEvalKit TSV for LongDocURL.")
    parser.add_argument("--jsonl", default=None, help="Local LongDocURL JSONL path. Preferred for fixtures/offline use.")
    parser.add_argument("--download-dir", default=None, help="Directory for optional Hugging Face download.")
    parser.add_argument("--output", required=True, help="Output TSV path, for example LongDocURL.tsv.")
    parser.add_argument("--token", default=os.environ.get("HF_TOKEN"), help="Optional Hugging Face token; defaults to HF_TOKEN.")
    parser.add_argument("--limit", type=int, default=None, help="Optional row limit for smoke conversions.")
    parser.add_argument("--image-root", default=None, help="Optional root containing LongDocURL pdf_pngs for path validation only.")
    parser.add_argument("--strict", action="store_true", help="Fail on empty questions or malformed image_path cells.")
    parser.add_argument("--strict-images", action="store_true", help="Fail when --image-root validation finds missing images.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    jsonl_path = args.jsonl
    if jsonl_path is None:
        download_dir = args.download_dir or osp.join(osp.dirname(osp.abspath(args.output)), "downloads")
        os.makedirs(download_dir, exist_ok=True)
        print(f"downloading {DATA_FILE} from {REPO_ID} ...")
        jsonl_path = hf_download(DATA_FILE, download_dir, token=args.token)

    samples = load_jsonl(jsonl_path)
    if args.limit is not None:
        if args.limit < 0:
            raise ConversionError("--limit must be non-negative")
        samples = samples[:args.limit]
    if not samples:
        raise ConversionError("No samples to write")

    rows = [row_from_sample(sample, i) for i, sample in enumerate(samples)]
    validate_rows(rows, strict=args.strict)
    if args.image_root:
        validate_image_root(rows, args.image_root, strict=args.strict_images)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=OUTPUT_COLUMNS).to_csv(output, sep="\t", index=False)
    print(f"wrote {len(rows)} rows -> {output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ConversionError as err:
        print(f"error: {err}", file=sys.stderr)
        raise SystemExit(2)
