#!/usr/bin/env python3
"""No-download smoke checks for txtai workflows.

This helper is adapted from txtai workflow quickstart patterns but avoids
network access, Streamlit, API servers, and model downloads. It validates pure
Python task chaining, lazy generator consumption, batching, and YAML workflow
template shape.
"""

from __future__ import annotations

import argparse
import json
import textwrap
from typing import Iterable, List


def strip_text(rows: Iterable[str]) -> List[str]:
    """Normalize whitespace for each row."""

    return [row.strip() for row in rows]


def summarize_text(rows: Iterable[str]) -> List[str]:
    """Create deterministic summaries without a model dependency."""

    summaries = []
    for row in rows:
        words = row.split()
        summaries.append(" ".join(words[:6]))
    return summaries


def translate_marker(rows: Iterable[str], language: str = "fr") -> List[str]:
    """Mark text as translated without calling a model."""

    return [f"[{language}] {row}" for row in rows]


def run_python_workflow() -> List[str]:
    """Run a pure Python txtai Workflow and return consumed results."""

    try:
        from txtai.workflow import Task, Workflow
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Unable to import txtai. Run this script in an environment where the txtai package is installed."
        ) from exc

    workflow = Workflow(
        [
            Task(strip_text),
            Task(summarize_text),
            Task(lambda rows: translate_marker(rows, "fr")),
        ],
        batch=2,
    )

    data = [
        "  txtai workflows process batches lazily and stream results  ",
        "  pipeline tasks can be composed with ordinary Python callables  ",
        "  consume the generator to force execution  ",
    ]

    results = list(workflow(data))
    expected = [
        "[fr] txtai workflows process batches lazily and",
        "[fr] pipeline tasks can be composed with",
        "[fr] consume the generator to force execution",
    ]

    if results != expected:
        raise AssertionError(f"unexpected workflow results: {results!r}")

    return results


def yaml_template() -> str:
    """Return a YAML workflow template using callable action paths."""

    return textwrap.dedent(
        """
        workflow:
          deterministic:
            batch: 2
            tasks:
              - action: __main__.strip_text
              - action: __main__.summarize_text
              - action: __main__.translate_marker
                args: [fr]
        """
    ).strip()


def validate_yaml_template() -> dict:
    """Validate YAML template syntax when PyYAML is available."""

    try:
        import yaml
    except ModuleNotFoundError:
        template = yaml_template()
        required = ["workflow:", "deterministic:", "__main__.strip_text", "__main__.translate_marker"]
        missing = [value for value in required if value not in template]
        if missing:
            raise AssertionError(f"YAML template missing markers: {missing!r}")
        return {"workflow": "deterministic", "validated": False, "reason": "PyYAML is not installed"}

    config = yaml.safe_load(yaml_template())
    tasks = config["workflow"]["deterministic"]["tasks"]
    actions = [task["action"] for task in tasks]

    if actions != ["__main__.strip_text", "__main__.summarize_text", "__main__.translate_marker"]:
        raise AssertionError(f"unexpected YAML actions: {actions!r}")

    return {"workflow": "deterministic", "tasks": len(tasks), "actions": actions, "validated": True}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-download txtai workflow smoke checks.")
    parser.add_argument(
        "--mode",
        choices=("python", "yaml", "all"),
        default="all",
        help="which check to run",
    )
    args = parser.parse_args()

    output = {}

    if args.mode in {"python", "all"}:
        output["python"] = run_python_workflow()

    if args.mode in {"yaml", "all"}:
        output["yaml"] = validate_yaml_template()
        output["yaml_template"] = yaml_template()

    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
