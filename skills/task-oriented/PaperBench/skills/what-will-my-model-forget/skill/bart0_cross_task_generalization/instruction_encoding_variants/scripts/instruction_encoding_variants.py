from __future__ import annotations

from typing import Any

VARIANTS = {"no_instruction", "prompt", "prompt_definition", "positive_examples", "prompt_definition_positive_examples", "full_instruction"}


def render_encoding(task: dict[str, Any], instance_input: str, variant: str = "full_instruction") -> dict[str, Any]:
    if variant not in VARIANTS:
        raise ValueError(f"unknown variant: {variant}")
    lines: list[str] = []
    fields: list[str] = []
    def add(label: str, value: str, field: str) -> None:
        text = str(value or "").strip()
        if text:
            lines.append(f"{label}: {text}")
            fields.append(field)
    if variant in {"prompt_definition", "prompt_definition_positive_examples", "full_instruction"}:
        add("Definition", task.get("definition", ""), "definition")
    if variant in {"prompt", "prompt_definition", "prompt_definition_positive_examples", "full_instruction"}:
        add("Prompt", task.get("prompt", ""), "prompt")
    if variant == "full_instruction":
        add("Things to Avoid", task.get("things_to_avoid", ""), "things_to_avoid")
        add("Emphasis&Caution", task.get("emphasis", ""), "emphasis")
        for idx, example in enumerate(task.get("negative_examples", []), 1):
            lines.append(f"NegativeExample{idx}- input: {example.get('input','')} output: {example.get('output','')} reason: {example.get('reason','')}")
            fields.append("negative_examples")
    if variant in {"positive_examples", "prompt_definition_positive_examples", "full_instruction"}:
        for idx, example in enumerate(task.get("positive_examples", []), 1):
            lines.append(f"PositiveExample{idx}- input: {example.get('input','')} output: {example.get('output','')} reason: {example.get('reason','')}")
            fields.append("positive_examples")
    lines.append(f"input: {str(instance_input).strip()}")
    lines.append("output:")
    return {"text": "\n".join(lines), "included_fields": sorted(set(fields))}
