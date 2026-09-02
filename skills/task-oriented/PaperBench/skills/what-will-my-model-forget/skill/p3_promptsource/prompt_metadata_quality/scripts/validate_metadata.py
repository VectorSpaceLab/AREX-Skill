#!/usr/bin/env python3
import argparse
import json
from typing import Any, Dict, List

ALLOWED_METRICS = {
    "BLEU",
    "ROUGE",
    "Squad",
    "Trivia QA",
    "Accuracy",
    "Pearson Correlation",
    "Spearman Correlation",
    "MultiRC",
    "AUC",
    "COQA F1",
    "Edit Distance",
    "Mean Reciprocal Rank",
    "Other",
}
ALLOWED_LANGUAGES = {"en", "fr", "es", "de", "ar", "zh", "ru", "hi", "sw", "other"}
BOILERPLATE_TARGET_PREFIXES = ("the answer is", "answer:", "the correct answer is")


def validate_metadata(metadata: Dict[str, Any], rendered_examples: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    rendered_examples = rendered_examples or []
    errors: List[str] = []
    warnings: List[str] = []
    checked_fields: List[str] = []

    name = str(metadata.get("name", "")).strip()
    checked_fields.append("name")
    if not name:
        errors.append("metadata.name is required")

    checked_fields.append("reference")
    if not str(metadata.get("reference", metadata.get("rationale", ""))).strip():
        warnings.append("metadata should include a reference or rationale")

    metrics = metadata.get("metrics", [])
    checked_fields.append("metrics")
    if isinstance(metrics, str):
        metrics = [metrics]
    if not isinstance(metrics, list):
        errors.append("metadata.metrics must be a list or string")
        metrics = []
    for metric in metrics:
        if metric not in ALLOWED_METRICS:
            errors.append(f"unknown metric: {metric}")

    checked_fields.append("language")
    language = metadata.get("language")
    if language is not None and language not in ALLOWED_LANGUAGES:
        warnings.append(f"language tag not in compact validator vocabulary: {language}")

    answer_choices = metadata.get("answer_choices", [])
    valid_outputs_stated = bool(metadata.get("valid_outputs_stated", False))
    checked_fields.extend(["answer_choices", "valid_outputs_stated"])
    if valid_outputs_stated and not answer_choices:
        errors.append("valid_outputs_stated is true but answer_choices is empty")

    checked_fields.append("rendered_examples")
    for index, example in enumerate(rendered_examples):
        prompt_input = str(example.get("input", "")).strip()
        target = str(example.get("target", "")).strip()
        if not prompt_input:
            errors.append(f"rendered_examples[{index}].input is empty")
        if not target:
            errors.append(f"rendered_examples[{index}].target is empty")
        lower_target = target.lower()
        if any(lower_target.startswith(prefix) for prefix in BOILERPLATE_TARGET_PREFIXES):
            warnings.append(f"rendered_examples[{index}].target contains removable answer boilerplate")
        if "{" in prompt_input and "}" in prompt_input:
            errors.append(f"rendered_examples[{index}].input appears to contain unrendered template markers")

    return {"ok": not errors, "errors": errors, "warnings": warnings, "checked_fields": checked_fields}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate PromptSource-style prompt metadata.")
    parser.add_argument("--metadata-json", required=True)
    parser.add_argument("--rendered-examples-json", default="[]")
    args = parser.parse_args()
    report = validate_metadata(json.loads(args.metadata_json), json.loads(args.rendered_examples_json))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
