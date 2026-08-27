#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os

from sdgx.models.LLM.single_table.gpt import SingleTableGPTModel


def redact(value: str | None) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "***"
    return value[:4] + "..." + value[-4:]


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect SDGX SingleTableGPTModel settings without network calls.")
    parser.add_argument("--json", action="store_true", help="Print JSON.")
    args = parser.parse_args()

    model = SingleTableGPTModel()
    report = {
        "env_OPENAI_KEY_present": bool(os.getenv("OPENAI_KEY")),
        "env_OPENAI_KEY_redacted": redact(os.getenv("OPENAI_KEY")),
        "env_OPENAI_URL": os.getenv("OPENAI_URL", ""),
        "model_openai_API_url": model.openai_API_url,
        "model_openai_API_key_present": bool(model.openai_API_key),
        "model_openai_API_key_redacted": redact(model.openai_API_key),
        "gpt_model": model.gpt_model,
        "max_tokens": model.max_tokens,
        "temperature": model.temperature,
        "timeout": model.timeout,
        "query_batch": model.query_batch,
        "off_table_features": list(model.off_table_features),
    }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for key, value in report.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
