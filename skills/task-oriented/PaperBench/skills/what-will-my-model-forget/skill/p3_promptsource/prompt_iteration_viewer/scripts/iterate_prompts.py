#!/usr/bin/env python3
import argparse
import json
import os
import sys
from typing import Any, Dict, List

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(ROOT, "prompt_template_rendering", "scripts"))

from render_prompt import render_prompt


def iterate_prompts(
    examples: List[Dict[str, Any]],
    templates: List[Dict[str, Any]],
    choice_index: int = 0,
    include_skipped: bool = False,
) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    coverage: Dict[str, Dict[str, int]] = {}
    errors: List[str] = []
    target_variants = set()

    for template_record in templates:
        template_id = str(template_record.get("id", template_record.get("name", "template")))
        coverage[template_id] = {"produced": 0, "skipped": 0, "errors": 0}
        for example_index, example in enumerate(examples):
            result = render_prompt(
                example,
                template_record.get("template", ""),
                template_record.get("answer_choices"),
                choice_index,
            )
            if not result["ok"]:
                coverage[template_id]["errors"] += 1
                errors.extend([f"{template_id}[{example_index}]: {message}" for message in result["errors"]])
            elif result["skipped"]:
                coverage[template_id]["skipped"] += 1
            else:
                coverage[template_id]["produced"] += 1
                target_variants.add(result["target"])

            if include_skipped or (result["ok"] and not result["skipped"]):
                rows.append(
                    {
                        "template_id": template_id,
                        "template_name": template_record.get("name", template_id),
                        "example_index": example_index,
                        "input": result["input"],
                        "target": result["target"],
                        "ok": result["ok"],
                        "skipped": result["skipped"],
                        "errors": result["errors"],
                    }
                )

    return {
        "ok": not errors,
        "rows": rows,
        "coverage": coverage,
        "variation_summary": {
            "template_count": len(templates),
            "example_count": len(examples),
            "template_names": [template.get("name", template.get("id", "template")) for template in templates],
            "target_variant_count": len(target_variants),
        },
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply prompt templates across examples and summarize diagnostics.")
    parser.add_argument("--examples-json", required=True)
    parser.add_argument("--templates-json", required=True)
    parser.add_argument("--choice-index", type=int, default=0)
    parser.add_argument("--include-skipped", action="store_true")
    args = parser.parse_args()
    report = iterate_prompts(json.loads(args.examples_json), json.loads(args.templates_json), args.choice_index, args.include_skipped)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
