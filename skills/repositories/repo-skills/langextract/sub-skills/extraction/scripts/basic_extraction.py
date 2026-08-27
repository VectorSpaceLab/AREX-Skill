#!/usr/bin/env python3
"""Safe starter for example-based LangExtract extraction.

Default behavior is a dry run that prints the configured prompt/example shape.
Add --run to call the selected model provider. Live extraction may incur model
costs and usually requires provider credentials, such as GEMINI_API_KEY,
LANGEXTRACT_API_KEY, or OPENAI_API_KEY depending on the model/provider. For
provider routing and credential details, use the sibling providers sub-skill.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any


def build_clinical_demo(lx: Any) -> tuple[str, str, list[Any]]:
    """Return input text, prompt, and examples for a compact clinical demo."""
    input_text = "Patient is prescribed metformin 500mg twice daily."
    prompt = (
        "Extract medications and conditions with attributes. Use exact text "
        "from the input and return extractions in order of appearance."
    )
    examples = [
        lx.data.ExampleData(
            text="Patient takes lisinopril 10mg daily for hypertension.",
            extractions=[
                lx.data.Extraction(
                    extraction_class="medication",
                    extraction_text="lisinopril",
                    attributes={"dose": "10mg", "frequency": "daily"},
                ),
                lx.data.Extraction(
                    extraction_class="condition",
                    extraction_text="hypertension",
                    attributes={"status": "active"},
                ),
            ],
        )
    ]
    return input_text, prompt, examples


def build_relationship_demo(lx: Any) -> tuple[str, str, list[Any]]:
    """Return a demo that groups related entities through attributes."""
    input_text = (
        "The patient takes Lisinopril 10mg daily for hypertension and "
        "Metformin 500mg twice daily for diabetes."
    )
    prompt = (
        "Extract medications, dosages, frequencies, and conditions. Use exact "
        "source text. Add a medication_group attribute to every extraction so "
        "details that belong to the same medication share the same group value."
    )
    examples = [
        lx.data.ExampleData(
            text="Patient takes Aspirin 100mg daily for heart health.",
            extractions=[
                lx.data.Extraction(
                    extraction_class="medication",
                    extraction_text="Aspirin",
                    attributes={"medication_group": "Aspirin"},
                ),
                lx.data.Extraction(
                    extraction_class="dosage",
                    extraction_text="100mg",
                    attributes={"medication_group": "Aspirin"},
                ),
                lx.data.Extraction(
                    extraction_class="frequency",
                    extraction_text="daily",
                    attributes={"medication_group": "Aspirin"},
                ),
                lx.data.Extraction(
                    extraction_class="condition",
                    extraction_text="heart health",
                    attributes={"medication_group": "Aspirin"},
                ),
            ],
        )
    ]
    return input_text, prompt, examples


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
    """Return explicit api_key kwargs or fail early when no likely key exists."""
    if api_key_env:
        value = os.environ.get(api_key_env)
        if not value:
            raise SystemExit(f"Environment variable {api_key_env} is not set.")
        return {"api_key": value}

    candidates = candidate_key_envs(model_id)
    if not candidates:
        return {}
    if any(os.environ.get(name) for name in candidates):
        return {}
    if allow_provider_defaults:
        return {}
    joined = ", ".join(candidates)
    raise SystemExit(
        "No likely provider credential environment variable is set "
        f"({joined}). Set one, pass --api-key-env NAME, or use "
        "--allow-provider-defaults if credentials are resolved another way."
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
        print(f"Text length: {len(document.text or '')} characters")
        extractions = document.extractions or []
        if not extractions:
            print("No extractions returned.")
            continue
        for extraction in extractions:
            interval = extraction.char_interval
            if interval is None:
                span = "ungrounded"
            else:
                span = f"{interval.start_pos}-{interval.end_pos}"
            status = getattr(extraction.alignment_status, "name", None)
            status_text = status or extraction.alignment_status or "unknown"
            print(
                f"- {extraction.extraction_class}: "
                f"{extraction.extraction_text!r} [{span}; {status_text}]"
            )
            if extraction.attributes:
                print(f"  attributes: {extraction.attributes}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a compact LangExtract extraction demo. By default this is a "
            "dry run; add --run to call a model provider."
        )
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Actually call lx.extract(); may incur model/provider costs.",
    )
    parser.add_argument(
        "--demo",
        choices=("clinical", "relationship"),
        default="clinical",
        help="Choose the prompt/example pattern to demonstrate.",
    )
    parser.add_argument(
        "--input-text",
        help="Override the demo input text. If it is a URL, it is literal text unless --fetch-url is set.",
    )
    parser.add_argument(
        "--fetch-url",
        action="store_true",
        help="Fetch --input-text when it is an http(s) URL. Use only for trusted URLs in a sandbox.",
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
    parser.add_argument("--max-char-buffer", type=int, default=1000)
    parser.add_argument("--batch-length", type=int, default=10)
    parser.add_argument("--max-workers", type=int, default=10)
    parser.add_argument("--extraction-passes", type=int, default=1)
    parser.add_argument("--context-window-chars", type=int)
    parser.add_argument(
        "--prompt-validation",
        choices=("OFF", "WARNING", "ERROR"),
        default="ERROR",
    )
    parser.add_argument(
        "--prompt-validation-strict",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Treat fuzzy/lesser example matches as validation failures in ERROR mode.",
    )
    parser.add_argument(
        "--unicode-tokenizer",
        action="store_true",
        help="Use UnicodeTokenizer for CJK/non-spaced/grapheme-sensitive text.",
    )
    parser.add_argument(
        "--show-progress",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Show or hide LangExtract progress display while running.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    lx = import_langextract()

    if args.demo == "clinical":
        default_text, prompt, examples = build_clinical_demo(lx)
    else:
        default_text, prompt, examples = build_relationship_demo(lx)
    input_text = args.input_text or default_text

    print("Prompt:")
    print(prompt)
    print(f"\nInput text: {input_text}")
    print(f"Examples: {len(examples)}")

    if not args.run:
        print("\nDry run only. Add --run to call lx.extract().")
        return 0

    provider_kwargs = provider_kwargs_from_env(
        model_id=args.model_id,
        api_key_env=args.api_key_env,
        allow_provider_defaults=args.allow_provider_defaults,
    )
    from langextract.prompt_validation import (  # pylint: disable=import-outside-toplevel
        PromptValidationLevel,
    )

    tokenizer = None
    if args.unicode_tokenizer:
        from langextract.core import tokenizer as tokenizer_lib  # pylint: disable=import-outside-toplevel

        tokenizer = tokenizer_lib.UnicodeTokenizer()

    result = lx.extract(
        text_or_documents=input_text,
        prompt_description=prompt,
        examples=examples,
        model_id=args.model_id,
        max_char_buffer=args.max_char_buffer,
        batch_length=args.batch_length,
        max_workers=args.max_workers,
        extraction_passes=args.extraction_passes,
        context_window_chars=args.context_window_chars,
        fetch_urls=args.fetch_url,
        prompt_validation_level=getattr(PromptValidationLevel, args.prompt_validation),
        prompt_validation_strict=args.prompt_validation_strict,
        tokenizer=tokenizer,
        show_progress=args.show_progress,
        **provider_kwargs,
    )
    print_result(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
