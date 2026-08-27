#!/usr/bin/env python3
"""Validate Sparrow Agents API payload shapes without starting services.

This smoke check is intentionally dependency-free. It validates small JSON/form
payload examples for the built-in Sparrow Agents endpoints and catches common
mistakes before a user starts FastAPI, Redis, Celery, Tavily, or Sparrow LLM.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

KNOWN_AGENTS = {"medical_prescriptions", "trading", "bonds"}
DATA_AGENTS = {"trading", "bonds"}
FILE_AGENTS = {"medical_prescriptions"}
CACHE_BASENAME_RE = re.compile(r"^search_results(?:_\d+)?\.json$")

EXAMPLES: Dict[str, Dict[str, Any]] = {
    "trading": {
        "endpoint": "data",
        "payload": {
            "agent_name": "trading",
            "input_data": {
                "symbols": ["AAPL", "GOOGL"],
                "account_balance": 100000,
                "risk_tolerance": 0.5,
            },
        },
    },
    "bonds_cached": {
        "endpoint": "data",
        "payload": {
            "agent_name": "bonds",
            "input_data": {"search_results_file": "search_results.json"},
        },
    },
    "medical_file": {
        "endpoint": "file",
        "payload": {
            "agent_name": "medical_prescriptions",
            "extraction_params": '{"sparrow_key":"123456"}',
            "filename": "prescription.pdf",
            "content_type": "application/pdf",
            "page_count": 2,
        },
    },
    "invalid_medical_image": {
        "endpoint": "file",
        "payload": {
            "agent_name": "medical_prescriptions",
            "extraction_params": '{"sparrow_key":"123456"}',
            "filename": "prescription.png",
            "content_type": "image/png",
            "page_count": 1,
        },
    },
    "invalid_extraction_params": {
        "endpoint": "file",
        "payload": {
            "agent_name": "medical_prescriptions",
            "extraction_params": "{sparrow_key:123456}",
            "filename": "prescription.pdf",
            "content_type": "application/pdf",
            "page_count": 2,
        },
    },
}


def _is_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        try:
            float(value)
            return True
        except ValueError:
            return False
    return False


def _load_json_file(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_extraction_params(raw: Any) -> Tuple[Dict[str, Any] | None, List[str]]:
    if isinstance(raw, dict):
        return raw, []
    if not isinstance(raw, str):
        return None, ["extraction_params must be a JSON object string or object"]
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, [f"extraction_params is not valid JSON: {exc.msg} at char {exc.pos}"]
    if not isinstance(parsed, dict):
        return None, ["extraction_params must decode to a JSON object"]
    return parsed, []


def validate_data_payload(payload: Any) -> List[str]:
    errors: List[str] = []
    if not isinstance(payload, dict):
        return ["data payload must be a JSON object"]

    agent_name = payload.get("agent_name")
    if not isinstance(agent_name, str) or not agent_name:
        errors.append("agent_name must be a non-empty string")
    elif agent_name not in KNOWN_AGENTS:
        errors.append(f"unknown agent_name {agent_name!r}; expected one of {sorted(KNOWN_AGENTS)}")
    elif agent_name not in DATA_AGENTS:
        errors.append(f"agent {agent_name!r} is file-oriented; prefer /execute/file")

    input_data = payload.get("input_data")
    if not isinstance(input_data, dict):
        errors.append("input_data must be a JSON object")
        input_data = {}

    if agent_name == "trading":
        symbols = input_data.get("symbols")
        if not isinstance(symbols, list) or not symbols:
            errors.append("trading input_data.symbols must be a non-empty list")
        elif not all(isinstance(symbol, str) and symbol for symbol in symbols):
            errors.append("trading input_data.symbols entries must be non-empty strings")

        account_balance = input_data.get("account_balance")
        if account_balance in (None, "", 0, 0.0):
            errors.append("trading input_data.account_balance is required and must be truthy/non-zero")
        elif not _is_number(account_balance):
            errors.append("trading input_data.account_balance must be convertible to float")

        risk_tolerance = input_data.get("risk_tolerance", 0.5)
        if not _is_number(risk_tolerance):
            errors.append("trading input_data.risk_tolerance must be convertible to float when provided")

    elif agent_name == "bonds":
        search_results_file = input_data.get("search_results_file")
        if search_results_file is not None:
            if not isinstance(search_results_file, str) or not search_results_file:
                errors.append("bonds input_data.search_results_file must be a non-empty string")
            elif "/" in search_results_file or "\\" in search_results_file or ".." in search_results_file:
                errors.append("bonds search_results_file must be a basename, not a path")
            elif not CACHE_BASENAME_RE.match(search_results_file):
                errors.append("bonds search_results_file should look like search_results.json or search_results_1.json")

    return errors


def validate_file_payload(payload: Any) -> List[str]:
    errors: List[str] = []
    if not isinstance(payload, dict):
        return ["file payload must be a JSON object representing multipart form fields"]

    agent_name = payload.get("agent_name")
    if not isinstance(agent_name, str) or not agent_name:
        errors.append("agent_name must be a non-empty string")
    elif agent_name not in KNOWN_AGENTS:
        errors.append(f"unknown agent_name {agent_name!r}; expected one of {sorted(KNOWN_AGENTS)}")
    elif agent_name not in FILE_AGENTS:
        errors.append(f"agent {agent_name!r} is data-oriented in this skill; prefer /execute/data")

    params, param_errors = parse_extraction_params(payload.get("extraction_params", '{"sparrow_key":"12345"}'))
    errors.extend(param_errors)
    if params is not None:
        sparrow_key = params.get("sparrow_key")
        if not isinstance(sparrow_key, str) or not sparrow_key:
            errors.append("medical file extraction_params.sparrow_key must be a non-empty string")

    filename = payload.get("filename")
    content_type = payload.get("content_type", "")
    if not isinstance(filename, str) or not filename:
        errors.append("file payload filename must be a non-empty string")
        filename = ""
    if not isinstance(content_type, str):
        errors.append("file payload content_type must be a string")
        content_type = ""

    is_pdf = content_type.lower() == "application/pdf" or filename.lower().endswith(".pdf")
    if agent_name == "medical_prescriptions" and not is_pdf:
        errors.append("medical_prescriptions requires a PDF upload by content_type or .pdf filename")

    page_count = payload.get("page_count")
    if page_count is not None:
        if not isinstance(page_count, int) or isinstance(page_count, bool):
            errors.append("page_count, when supplied, must be an integer")
        elif agent_name == "medical_prescriptions" and page_count <= 1:
            errors.append("medical_prescriptions requires a multi-page PDF; page_count must be greater than 1")

    return errors


def validate(endpoint: str, payload: Any) -> List[str]:
    if endpoint == "data":
        return validate_data_payload(payload)
    if endpoint == "file":
        return validate_file_payload(payload)
    return [f"unsupported endpoint {endpoint!r}; expected 'data' or 'file'"]


def iter_cases(case: str) -> Iterable[Tuple[str, str, Dict[str, Any]]]:
    if case == "all":
        for name in ("trading", "bonds_cached", "medical_file"):
            example = EXAMPLES[name]
            yield name, example["endpoint"], example["payload"]
        return
    if case not in EXAMPLES:
        raise SystemExit(f"Unknown --case {case!r}; choose from all, {', '.join(sorted(EXAMPLES))}")
    example = EXAMPLES[case]
    yield case, example["endpoint"], example["payload"]


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case",
        default="all",
        help="Built-in example to validate: all, trading, bonds_cached, medical_file, invalid_medical_image, invalid_extraction_params",
    )
    parser.add_argument("--endpoint", choices=("data", "file"), help="Endpoint type for --payload-file")
    parser.add_argument("--payload-file", type=Path, help="JSON file containing a custom data payload or file-form metadata")
    parser.add_argument("--dump-examples", action="store_true", help="Print bundled valid examples as JSON")
    args = parser.parse_args(argv)

    if args.dump_examples:
        valid = {name: EXAMPLES[name] for name in ("trading", "bonds_cached", "medical_file")}
        print(json.dumps(valid, indent=2, sort_keys=True))

    results: List[Dict[str, Any]] = []

    if args.payload_file:
        if not args.endpoint:
            parser.error("--endpoint is required with --payload-file")
        payload = _load_json_file(args.payload_file)
        errors = validate(args.endpoint, payload)
        results.append({"case": str(args.payload_file), "endpoint": args.endpoint, "ok": not errors, "errors": errors})
    else:
        for name, endpoint, payload in iter_cases(args.case):
            errors = validate(endpoint, payload)
            results.append({"case": name, "endpoint": endpoint, "ok": not errors, "errors": errors})

    print(json.dumps({"results": results}, indent=2, sort_keys=True))
    return 0 if all(item["ok"] for item in results) else 1


if __name__ == "__main__":
    sys.exit(main())
