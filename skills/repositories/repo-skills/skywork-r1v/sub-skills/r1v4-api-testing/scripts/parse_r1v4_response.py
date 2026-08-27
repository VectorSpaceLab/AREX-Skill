#!/usr/bin/env python3
"""Parse tagged Skywork R1V4 responses from a string, file, or JSONL file."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

TAG_PATTERN = re.compile(r"<(think|tool_call|observation|answer)>(.*?)</\1>", re.DOTALL)


def _extract_tag_blocks(full_response: str) -> List[Dict[str, Any]]:
    blocks: List[Dict[str, Any]] = []
    for index, match in enumerate(TAG_PATTERN.finditer(full_response or "")):
        blocks.append(
            {
                "index": index,
                "tag": match.group(1),
                "raw": match.group(2),
                "text": match.group(2).strip(),
            }
        )
    return blocks


def _parse_json_block(raw_text: str) -> Tuple[Any, Optional[str]]:
    try:
        return json.loads(raw_text.strip()), None
    except json.JSONDecodeError as exc:
        return raw_text, str(exc)


def parse_full_response(full_response: str) -> Dict[str, Any]:
    """Parse a single tagged response string into rounds plus final answer."""

    full_response = full_response or ""
    tag_sequence = _extract_tag_blocks(full_response)
    grouped = {
        "think": [],
        "tool_call": [],
        "observation": [],
        "answer": [],
    }
    for block in tag_sequence:
        grouped[block["tag"]].append(block)

    round_count = max(len(grouped["tool_call"]), len(grouped["observation"]))
    rounds: List[Dict[str, Any]] = []
    parse_errors: List[Dict[str, Any]] = []

    for round_index in range(round_count):
        round_data: Dict[str, Any] = {
            "round_num": round_index + 1,
            "think": "",
            "think_raw": "",
            "tool_call": None,
            "tool_call_raw": "",
            "observation": None,
            "observation_raw": "",
        }

        if round_index < len(grouped["think"]):
            think_block = grouped["think"][round_index]
            round_data["think"] = think_block["text"]
            round_data["think_raw"] = think_block["raw"]

        if round_index < len(grouped["tool_call"]):
            tool_block = grouped["tool_call"][round_index]
            tool_value, tool_error = _parse_json_block(tool_block["raw"])
            round_data["tool_call"] = tool_value
            round_data["tool_call_raw"] = tool_block["raw"]
            if tool_error:
                round_data["tool_call_parse_error"] = tool_error
                parse_errors.append(
                    {
                        "round_num": round_index + 1,
                        "tag": "tool_call",
                        "error": tool_error,
                    }
                )

        if round_index < len(grouped["observation"]):
            observation_block = grouped["observation"][round_index]
            observation_value, observation_error = _parse_json_block(observation_block["raw"])
            round_data["observation"] = observation_value
            round_data["observation_raw"] = observation_block["raw"]
            if observation_error:
                round_data["observation_parse_error"] = observation_error
                parse_errors.append(
                    {
                        "round_num": round_index + 1,
                        "tag": "observation",
                        "error": observation_error,
                    }
                )

        rounds.append(round_data)

    final_think = ""
    final_think_raw = ""
    if len(grouped["think"]) > round_count:
        think_block = grouped["think"][-1]
        final_think = think_block["text"]
        final_think_raw = think_block["raw"]
    elif round_count == 0 and grouped["think"]:
        think_block = grouped["think"][-1]
        final_think = think_block["text"]
        final_think_raw = think_block["raw"]

    final_answer = ""
    final_answer_raw = ""
    if grouped["answer"]:
        answer_block = grouped["answer"][0]
        final_answer = answer_block["text"]
        final_answer_raw = answer_block["raw"]

    tag_counts = {tag: len(blocks) for tag, blocks in grouped.items()}

    return {
        "raw_response": full_response,
        "rounds": rounds,
        "final_round": {
            "think": final_think,
            "think_raw": final_think_raw,
            "answer": final_answer,
            "answer_raw": final_answer_raw,
        },
        "tag_sequence": tag_sequence,
        "tag_counts": tag_counts,
        "parse_errors": parse_errors,
    }


def get_round_statistics(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize round counts, tools used, and parse issues for a parsed response."""

    rounds = parsed_data.get("rounds", []) if isinstance(parsed_data, dict) else []
    final_round = parsed_data.get("final_round", {}) if isinstance(parsed_data, dict) else {}
    tag_counts = parsed_data.get("tag_counts", {}) if isinstance(parsed_data, dict) else {}

    stats = {
        "total_rounds": len(rounds),
        "has_final_answer": bool(final_round.get("answer", "")),
        "tools_used": [],
        "tool_call_parse_errors": 0,
        "observation_parse_errors": 0,
        "tag_counts": tag_counts,
        "parse_error_count": len(parsed_data.get("parse_errors", [])) if isinstance(parsed_data, dict) else 0,
    }

    for round_data in rounds:
        tool_call = round_data.get("tool_call")
        if isinstance(tool_call, dict) and "name" in tool_call:
            stats["tools_used"].append(tool_call["name"])
        if round_data.get("tool_call_parse_error"):
            stats["tool_call_parse_errors"] += 1
        if round_data.get("observation_parse_error"):
            stats["observation_parse_errors"] += 1

    return stats


def _read_jsonl_records(path: str) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as handle:
        for line_num, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                records.append(
                    {
                        "line_num": line_num,
                        "parse_error": f"invalid JSON: {exc}",
                        "raw_line": line.rstrip("\n"),
                    }
                )
                continue

            response_block: Dict[str, Any] = {}
            full_response = None
            if isinstance(record, dict):
                raw_response = record.get("response")
                if isinstance(raw_response, dict):
                    response_block = raw_response
                    full_response = raw_response.get("full_response")
                elif isinstance(record.get("full_response"), str):
                    response_block = {"full_response": record.get("full_response")}
                    full_response = record.get("full_response")
                elif isinstance(raw_response, str):
                    response_block = {"full_response": raw_response}
                    full_response = raw_response

            parsed_response = None
            stats = {
                "total_rounds": 0,
                "has_final_answer": False,
                "tools_used": [],
                "tool_call_parse_errors": 0,
                "observation_parse_errors": 0,
                "tag_counts": {},
                "parse_error_count": 0,
            }
            parse_error = None
            if isinstance(full_response, str):
                parsed_response = parse_full_response(full_response)
                stats = get_round_statistics(parsed_response)
            else:
                parse_error = "missing response.full_response"

            output_record: Dict[str, Any] = {
                "line_num": line_num,
                "image": record.get("image", "") if isinstance(record, dict) else "",
                "question": record.get("question", "") if isinstance(record, dict) else "",
                "raw_response": response_block,
                "parsed_response": parsed_response,
                "statistics": stats,
            }
            if parse_error:
                output_record["parse_error"] = parse_error
            records.append(output_record)
    return records


def parse_jsonl_file(input_file: str, output_file: Optional[str] = None) -> List[Dict[str, Any]]:
    """Parse a JSONL file and optionally write the parsed records back to JSONL."""

    records = _read_jsonl_records(input_file)
    if output_file:
        with open(output_file, "w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return records


def _aggregate_jsonl_stats(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    parsed_count = sum(1 for record in records if record.get("parsed_response"))
    error_count = sum(1 for record in records if record.get("parse_error"))
    total_rounds = sum(
        int(record.get("statistics", {}).get("total_rounds", 0)) for record in records
    )
    tool_names: List[str] = []
    for record in records:
        tool_names.extend(record.get("statistics", {}).get("tools_used", []))
    return {
        "total_records": len(records),
        "parsed_records": parsed_count,
        "parse_error_records": error_count,
        "total_rounds": total_rounds,
        "tools_used": tool_names,
    }


def _read_text_source(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _dump_json(data: Any, pretty: bool = True) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2 if pretty else None)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Parse one Skywork R1V4 response string, text file, or JSONL file.",
    )
    parser.add_argument("--text", help="Parse one raw response string directly.")
    parser.add_argument("--input", help="Parse a text file or JSONL file.")
    parser.add_argument(
        "--jsonl",
        action="store_true",
        help="Treat --input as JSONL even if the file extension is not .jsonl.",
    )
    parser.add_argument(
        "--output",
        help="Optional output file. Single inputs are written as JSON; JSONL inputs are written as JSONL.",
    )
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Print only the summary statistics.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    args = parser.parse_args()

    if args.text is not None:
        parsed = parse_full_response(args.text)
        stats = get_round_statistics(parsed)
        output = {"parsed_response": parsed, "statistics": stats}
        if args.stats_only:
            output = stats
        text = _dump_json(output, pretty=args.pretty or args.output is None)
        if args.output:
            Path(args.output).write_text(text + "\n", encoding="utf-8")
        else:
            print(text)
        return 0

    if not args.input:
        parser.error("provide either --text or --input")

    input_path = args.input
    is_jsonl = args.jsonl or input_path.lower().endswith(".jsonl")

    if is_jsonl:
        records = parse_jsonl_file(input_path, output_file=args.output)
        summary = _aggregate_jsonl_stats(records)
        output: Any = summary if args.stats_only else {"summary": summary, "results": records}
        text = _dump_json(output, pretty=args.pretty or args.output is None)
        if not args.output:
            print(text)
        elif not args.stats_only:
            print(text)
        else:
            print(text)
        return 0

    full_response = _read_text_source(input_path)
    parsed = parse_full_response(full_response)
    stats = get_round_statistics(parsed)
    output = stats if args.stats_only else {"parsed_response": parsed, "statistics": stats}
    text = _dump_json(output, pretty=args.pretty or args.output is None)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
