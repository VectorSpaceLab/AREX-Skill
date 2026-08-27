#!/usr/bin/env python3
"""Offline parser for saved Stanford Alpaca/OpenAI completion text."""
from __future__ import annotations

import argparse
import json
import re
import string
import sys
from pathlib import Path
from typing import Iterable, List, Sequence

BLACKLIST = [
    "image",
    "images",
    "graph",
    "graphs",
    "picture",
    "pictures",
    "file",
    "files",
    "map",
    "maps",
    "draw",
    "plot",
    "go to",
    "video",
    "audio",
    "music",
    "flowchart",
    "diagram",
]

SELF_CHECK_RESPONSE = {
    "text": " Sort the following words alphabetically.\n4. Input:\npear, apple, grape\n4. Output:\napple, grape, pear\n###\n5. Instruction: Write a program that prints hello world.\n5. Input:\n<noinput>\n5. Output:\nprint('hello world')\n###\n6. Instruction: ???\n",
    "finish_reason": "stop",
}


def find_word_in_string(word: str, text: str):
    return re.compile(r"\b({0})\b".format(word), flags=re.IGNORECASE).search(text)


def _coerce_response_payload(payload):
    if payload is None:
        return None
    if isinstance(payload, str):
        return {"text": payload, "finish_reason": "stop"}
    if isinstance(payload, dict):
        if "choices" in payload and payload["choices"]:
            first = payload["choices"][0]
            text = first.get("text", "")
            finish_reason = first.get("finish_reason", payload.get("finish_reason", "stop"))
            return {"text": text, "finish_reason": finish_reason}
        if "text" in payload:
            return {"text": payload.get("text", ""), "finish_reason": payload.get("finish_reason", "stop")}
    raise TypeError(f"Unsupported completion payload: {type(payload)!r}")


def load_response(path: Path | None, raw_text: str | None, finish_reason: str | None):
    if raw_text is not None:
        return {"text": raw_text, "finish_reason": finish_reason or "stop"}
    if path is None:
        return SELF_CHECK_RESPONSE

    text = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {"text": text, "finish_reason": finish_reason or "stop"}
    payload = _coerce_response_payload(payload)
    if finish_reason is not None:
        payload["finish_reason"] = finish_reason
    return payload


def post_process_gpt3_response(num_prompt_instructions: int, response):
    if response is None:
        return []
    response = _coerce_response_payload(response)
    raw_instructions = f"{num_prompt_instructions + 1}. Instruction:" + response["text"]
    raw_instructions = re.split("###", raw_instructions)
    instructions = []
    for idx, inst in enumerate(raw_instructions):
        if idx == len(raw_instructions) - 1 and response.get("finish_reason") == "length":
            continue
        idx += num_prompt_instructions + 1
        splitted_data = re.split(rf"{idx}\.\s+(Instruction|Input|Output):", inst)
        if len(splitted_data) != 7:
            continue
        inst_text = splitted_data[2].strip()
        input_text = splitted_data[4].strip()
        input_text = "" if input_text.lower() == "<noinput>" else input_text
        output_text = splitted_data[6].strip()
        if len(inst_text.split()) <= 3 or len(inst_text.split()) > 150:
            continue
        if any(find_word_in_string(word, inst_text) for word in BLACKLIST):
            continue
        if inst_text.startswith("Write a program"):
            continue
        if not inst_text:
            continue
        if inst_text[0] in string.punctuation:
            continue
        if not inst_text[0].isascii():
            continue
        instructions.append({"instruction": inst_text, "input": input_text, "output": output_text})
    return instructions


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--completion-path",
        type=Path,
        help="Path to saved completion text or JSON payload.",
    )
    parser.add_argument(
        "--response-text",
        help="Raw completion text passed directly on the command line.",
    )
    parser.add_argument(
        "--finish-reason",
        default=None,
        help="Override the finish reason when the payload is raw text.",
    )
    parser.add_argument(
        "--num-prompt-instructions",
        type=int,
        default=3,
        help="Number of seed instructions that preceded the completion text.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output file for the parsed JSON records.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the JSON output.",
    )
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="Parse a built-in synthetic completion and print a short success message.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    response = load_response(args.completion_path, args.response_text, args.finish_reason)
    records = post_process_gpt3_response(args.num_prompt_instructions, response)
    payload = json.dumps(records, indent=2 if args.pretty else None, ensure_ascii=False)

    if args.output:
        args.output.write_text(payload + ("\n" if not payload.endswith("\n") else ""), encoding="utf-8")
    else:
        sys.stdout.write(payload)
        if not payload.endswith("\n"):
            sys.stdout.write("\n")

    if args.self_check:
        assert len(records) == 1
        assert records[0]["instruction"] == "Sort the following words alphabetically."
        print(f"[ok] parsed {len(records)} filtered instruction record", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
