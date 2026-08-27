#!/usr/bin/env python3
"""Safe starter for LangExtract output_schema extraction.

This demo uses lx.schema.extraction_item_schema() and
lx.schema.extractions_schema() to constrain the raw LangExtract JSON envelope.
The user-provided output_schema path is supported by Gemini and supported
OpenAI models, but not by Ollama. output_schema requires raw JSON: this script
sets fence_output=False and deliberately does not set a YAML format or provider
schema kwargs. Default behavior is a dry run; add --run for a live call.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any


def build_schema(lx: Any) -> dict[str, Any]:
    return lx.schema.extractions_schema(
        lx.schema.extraction_item_schema(
            "condition",
            attributes={
                "status": {
                    "type": "string",
                    "enum": ["present", "absent"],
                }
            },
        )
    )


def build_examples(lx: Any) -> list[Any]:
    return [
        lx.data.ExampleData(
            text="Patient has asthma. Patient denies fever.",
            extractions=[
                lx.data.Extraction(
                    extraction_class="condition",
                    extraction_text="asthma",
                    attributes={"status": "present"},
                ),
                lx.data.Extraction(
                    extraction_class="condition",
                    extraction_text="fever",
                    attributes={"status": "absent"},
                ),
            ],
        )
    ]


def candidate_key_envs(model_id: str) -> list[str]:
    lower = model_id.lower()
    if "ollama" in lower or lower.startswith("local"):
        return []
    if lower.startswith("gpt") or "openai" in lower:
        return ["OPENAI_API_KEY", "LANGEXTRACT_API_KEY"]
    if "gemini" in lower:
        return ["GEMINI_API_KEY", "LANGEXTRACT_API_KEY"]
    return ["GEMINI_API_KEY", "OPENAI_API_KEY", "LANGEXTRACT_API_KEY"]


def provider_kwargs_from_env(
    *, model_id: str, api_key_env: str | None, allow_provider_defaults: bool
) -> dict[str, str]:
    if api_key_env:
        value = os.environ.get(api_key_env)
        if not value:
            raise SystemExit(f"Environment variable {api_key_env} is not set.")
        return {"api_key": value}

    candidates = candidate_key_envs(model_id)
    if not candidates or any(os.environ.get(name) for name in candidates):
        return {}
    if allow_provider_defaults:
        return {}
    raise SystemExit(
        "No likely provider credential environment variable is set "
        f"({', '.join(candidates)}). Set one, pass --api-key-env NAME, or use "
        "--allow-provider-defaults."
    )


def import_langextract() -> Any:
    try:
        import langextract as lx  # pylint: disable=import-outside-toplevel
    except Exception as exc:  # pragma: no cover - diagnostic path for users
        raise SystemExit(
            "Could not import langextract. Install the package in the current "
            f"Python environment before running this demo. Original error: {exc}"
        ) from exc
    return lx


def print_result(result: Any) -> None:
    documents = result if isinstance(result, list) else [result]
    for document in documents:
        print(f"\nDocument: {document.document_id}")
        for extraction in document.extractions or []:
            interval = extraction.char_interval
            span = (
                "ungrounded"
                if interval is None
                else f"{interval.start_pos}-{interval.end_pos}"
            )
            print(
                f"- {extraction.extraction_class}: "
                f"{extraction.extraction_text!r} [{span}] "
                f"attributes={extraction.attributes or {}}"
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a schema-constrained LangExtract demo. Default is a dry run; "
            "add --run to call Gemini or a supported OpenAI model."
        )
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Actually call lx.extract(); may incur model/provider costs.",
    )
    parser.add_argument(
        "--without-examples",
        action="store_true",
        help="Demonstrate that examples are optional when output_schema is present.",
    )
    parser.add_argument("--model-id", default="gemini-2.5-flash")
    parser.add_argument(
        "--api-key-env",
        help="Optional environment variable name whose value should be passed as api_key.",
    )
    parser.add_argument(
        "--allow-provider-defaults",
        action="store_true",
        help="Do not preflight common API-key environment variables before --run.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    lx = import_langextract()
    output_schema = build_schema(lx)
    examples = None if args.without_examples else build_examples(lx)

    print("Output schema:")
    print(json.dumps(output_schema, indent=2))
    print(
        "\nThe live call uses raw JSON with fence_output=False. "
        "It does not pass provider-native schema kwargs."
    )

    if not args.run:
        print("Dry run only. Add --run to call lx.extract().")
        return 0

    if "ollama" in args.model_id.lower():
        raise SystemExit(
            "Ollama does not support this user-provided output_schema path; "
            "choose a supported Gemini or OpenAI model instead."
        )

    provider_kwargs = provider_kwargs_from_env(
        model_id=args.model_id,
        api_key_env=args.api_key_env,
        allow_provider_defaults=args.allow_provider_defaults,
    )
    from langextract.prompt_validation import (  # pylint: disable=import-outside-toplevel
        PromptValidationLevel,
    )

    result = lx.extract(
        text_or_documents="The note mentions hypertension and denies diabetes.",
        prompt_description=(
            "Extract conditions with exact source text. Set status to present "
            "or absent according to the note."
        ),
        examples=examples,
        model_id=args.model_id,
        output_schema=output_schema,
        # output_schema requires raw JSON; fence_output=True is invalid.
        fence_output=False,
        temperature=0.0,
        prompt_validation_level=PromptValidationLevel.ERROR,
        show_progress=False,
        **provider_kwargs,
    )
    print_result(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
