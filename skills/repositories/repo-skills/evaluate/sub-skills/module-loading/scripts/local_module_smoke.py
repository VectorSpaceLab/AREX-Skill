#!/usr/bin/env python3
"""Create and load a tiny local Evaluate metric without Hub access."""

from __future__ import annotations

import json
import textwrap
import tempfile
from pathlib import Path

try:
    import evaluate
except ModuleNotFoundError as error:
    raise SystemExit(
        "This smoke helper requires an environment where `evaluate` and its dependencies are installed. "
        "Install the package or run it from the intended Evaluate environment."
    ) from error


MODULE_NAME = "tiny_local_match"
MODULE_CODE = r'''
import datasets
import evaluate


_DESCRIPTION = "Deterministic tiny local metric for loading smoke tests."
_KWARGS_DESCRIPTION = """
Args:
    predictions: Predicted integer labels.
    references: Reference integer labels.
Returns:
    tiny_local_match: Fraction of equal prediction/reference pairs.
"""


class TinyLocalMatch(evaluate.Metric):
    def _info(self):
        return evaluate.MetricInfo(
            description=_DESCRIPTION,
            citation="",
            inputs_description=_KWARGS_DESCRIPTION,
            features=datasets.Features(
                {
                    "predictions": datasets.Value("int32"),
                    "references": datasets.Value("int32"),
                }
            ),
        )

    def _compute(self, predictions, references):
        total = len(predictions)
        score = 0.0 if total == 0 else sum(int(pred == ref) for pred, ref in zip(predictions, references)) / total
        return {"tiny_local_match": score}
'''


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="evaluate-local-module-") as temporary_directory:
        module_directory = Path(temporary_directory) / MODULE_NAME
        module_directory.mkdir()
        module_path = module_directory / f"{MODULE_NAME}.py"
        module_path.write_text(textwrap.dedent(MODULE_CODE).strip() + "\n", encoding="utf-8")

        metric = evaluate.load(str(module_directory), module_type="metric")
        result = metric.compute(predictions=[1, 0, 1, 1], references=[1, 1, 1, 0])

        expected = {"tiny_local_match": 0.5}
        if result != expected:
            raise AssertionError(f"unexpected local metric result: {result!r} != {expected!r}")

        print(
            json.dumps(
                {
                    "ok": True,
                    "module_type": metric.module_type,
                    "module_name": MODULE_NAME,
                    "result": result,
                },
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
