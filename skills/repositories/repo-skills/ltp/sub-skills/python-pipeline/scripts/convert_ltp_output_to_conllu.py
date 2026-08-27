#!/usr/bin/env python3
"""Convert saved LTP-shaped JSON output to CoNLL-U-like rows.

The script does not load an LTP model. It expects JSON containing at least
`cws`, and optionally `pos`, `dep`, and `sdpg` fields from a pipeline run.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List


def ensure_batch(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list) and (not value or isinstance(value[0], list) or isinstance(value[0], dict)):
        return value
    return [value]


def dep_for(dep_batch: List[Any], sent_idx: int, n: int) -> Dict[str, List[Any]]:
    if sent_idx >= len(dep_batch) or dep_batch[sent_idx] is None:
        return {"head": [0] * n, "label": ["_"] * n}
    dep = dep_batch[sent_idx]
    if isinstance(dep, dict):
        return {"head": dep.get("head", [0] * n), "label": dep.get("label", ["_"] * n)}
    return {"head": [0] * n, "label": ["_"] * n}


def sdpg_deps(sdpg: Any, token_id: int) -> str:
    deps: List[str] = []
    if not isinstance(sdpg, list):
        return "_"
    for arc in sdpg:
        if not isinstance(arc, (list, tuple)) or len(arc) < 3:
            continue
        src, head, label = arc[0], arc[1], arc[2]
        if int(src) == token_id:
            deps.append(f"{head}:{label}")
    return "|".join(deps) if deps else "_"


def convert(data: Dict[str, Any]) -> str:
    cws_batch = ensure_batch(data.get("cws"))
    if not cws_batch:
        raise ValueError("input JSON must contain a non-empty 'cws' field")
    pos_batch = ensure_batch(data.get("pos"))
    dep_batch = ensure_batch(data.get("dep"))
    sdpg_batch = ensure_batch(data.get("sdpg"))

    blocks: List[str] = []
    for sent_idx, words in enumerate(cws_batch):
        if not isinstance(words, list):
            raise ValueError(f"cws sentence {sent_idx} is not a list")
        n = len(words)
        pos = pos_batch[sent_idx] if sent_idx < len(pos_batch) and isinstance(pos_batch[sent_idx], list) else ["_"] * n
        dep = dep_for(dep_batch, sent_idx, n)
        sdpg = sdpg_batch[sent_idx] if sent_idx < len(sdpg_batch) else []
        rows: List[str] = []
        for idx, word in enumerate(words, start=1):
            xpos = pos[idx - 1] if idx - 1 < len(pos) else "_"
            head = dep["head"][idx - 1] if idx - 1 < len(dep["head"]) else 0
            rel = dep["label"][idx - 1] if idx - 1 < len(dep["label"]) else "_"
            deps = sdpg_deps(sdpg, idx)
            rows.append("\t".join([str(idx), str(word), "_", "_", str(xpos), "_", str(head), str(rel), deps, "_"]))
        blocks.append("\n".join(rows))
    return "\n\n".join(blocks) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert LTP JSON output to CoNLL-U-like rows.")
    parser.add_argument("--input", required=True, help="input JSON file containing cws/pos/dep/sdpg-like fields")
    parser.add_argument("--output", help="output file; defaults to stdout")
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    if isinstance(data, list):
        # Allow a list of sentence dictionaries by transposing fields.
        merged: Dict[str, List[Any]] = {}
        for item in data:
            if not isinstance(item, dict):
                raise ValueError("list input must contain dictionaries")
            for key, value in item.items():
                merged.setdefault(key, []).append(value)
        data = merged
    text = convert(data)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
