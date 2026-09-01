#!/usr/bin/env python3
import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(ROOT, "prompt_template_rendering", "scripts"))
sys.path.insert(0, os.path.join(ROOT, "prompt_metadata_quality", "scripts"))

from render_prompt import render_prompt
from validate_metadata import validate_metadata


def materialize_p3(
    dataset_name: str,
    subset_name: Optional[str],
    examples: List[Dict[str, Any]],
    templates: List[Dict[str, Any]],
    choice_index: int = 0,
) -> Dict[str, Any]:
    records: List[Dict[str, Any]] = []
    errors: List[str] = []
    metadata_reports: Dict[str, Dict[str, Any]] = {}
    skipped = 0
    metrics = set()

    for template_record in templates:
        template_id = str(template_record.get("id", template_record.get("name", "template")))
        metadata = {key: value for key, value in template_record.items() if key not in {"template"}}
        metadata_report = validate_metadata(metadata)
        metadata_reports[template_id] = metadata_report
        if not metadata_report["ok"]:
            errors.extend([f"{template_id}: {message}" for message in metadata_report["errors"]])
        for metric in template_record.get("metrics", []) or []:
            metrics.add(metric)

        for example_index, example in enumerate(examples):
            result = render_prompt(example, template_record.get("template", ""), template_record.get("answer_choices"), choice_index)
            if not result["ok"]:
                errors.extend([f"{template_id}[{example_index}]: {message}" for message in result["errors"]])
                continue
            if result["skipped"]:
                skipped += 1
                continue
            records.append(
                {
                    "dataset_name": dataset_name,
                    "subset_name": subset_name,
                    "example_index": example_index,
                    "template_id": template_id,
                    "template_name": template_record.get("name", template_id),
                    "input": result["input"],
                    "target": result["target"],
                    "metadata": metadata,
                }
            )

    return {
        "ok": not errors,
        "records": records,
        "summary": {
            "dataset_name": dataset_name,
            "subset_name": subset_name,
            "template_count": len(templates),
            "example_count": len(examples),
            "produced_records": len(records),
            "skipped_records": skipped,
            "error_count": len(errors),
            "metrics": sorted(metrics),
        },
        "metadata_reports": metadata_reports,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Materialize PromptSource/P3-style prompt records.")
    parser.add_argument("--dataset-name", required=True)
    parser.add_argument("--subset-name")
    parser.add_argument("--examples-json", required=True)
    parser.add_argument("--templates-json", required=True)
    parser.add_argument("--choice-index", type=int, default=0)
    args = parser.parse_args()
    report = materialize_p3(
        args.dataset_name,
        args.subset_name,
        json.loads(args.examples_json),
        json.loads(args.templates_json),
        args.choice_index,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
