#!/usr/bin/env python3
"""Smoke test for the xTuring evaluation scaffold.

This script exercises:
- EvalMetric / EvalRunResult serialization
- BaseEvalAdapter via a dummy adapter
- run_eval_adapter timing and persistence
- persist_eval_result direct JSON writing
- LMEvalAdapter scaffold metadata

It does not download models or run external benchmarks.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from xturing.evaluation import (
    BaseEvalAdapter,
    EvalMetric,
    EvalRunResult,
    LMEvalAdapter,
    persist_eval_result,
    run_eval_adapter,
)


class DummyEvalAdapter(BaseEvalAdapter):
    adapter_name = "dummy"

    def run(
        self,
        *,
        model: Any,
        dataset: Any,
        task_name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EvalRunResult:
        result_metadata: Dict[str, Any] = {
            "dataset_type": type(dataset).__name__,
            "model_type": type(model).__name__,
        }
        if metadata:
            result_metadata.update(metadata)

        return EvalRunResult(
            adapter_name=self.adapter_name,
            task_name=task_name,
            status="completed",
            metrics=[
                EvalMetric(name="accuracy", value=0.75, higher_is_better=True)
            ],
            metadata=result_metadata,
        )


def _assert_metric_schema(metric_payload: Dict[str, Any]) -> None:
    assert set(metric_payload) == {
        "name",
        "value",
        "higher_is_better",
    }, metric_payload
    assert metric_payload["name"] == "accuracy"
    assert metric_payload["value"] == 0.75
    assert metric_payload["higher_is_better"] is True


def _assert_result_schema(payload: Dict[str, Any], expected_status: str) -> None:
    assert set(payload) == {
        "adapter_name",
        "task_name",
        "status",
        "metrics",
        "metadata",
        "started_at",
        "finished_at",
        "duration_seconds",
    }, payload
    assert payload["status"] == expected_status
    assert isinstance(payload["metrics"], list)
    assert isinstance(payload["metadata"], dict)
    assert payload["started_at"] is not None
    assert payload["finished_at"] is not None
    assert payload["duration_seconds"] is not None


def _run_smoke(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    dummy_output = output_dir / "dummy_result.json"
    planned_output = output_dir / "planned_result.json"
    direct_output = output_dir / "direct_result.json"

    dummy_result = run_eval_adapter(
        DummyEvalAdapter(),
        model=object(),
        dataset=[{"text": "hello"}],
        task_name="smoke",
        output_path=dummy_output,
        metadata={"suite": "evaluation_scaffold_smoke"},
    )

    assert dummy_result.status == "completed"
    assert dummy_result.started_at is not None
    assert dummy_result.finished_at is not None
    assert dummy_result.duration_seconds is not None
    assert dummy_result.metadata["suite"] == "evaluation_scaffold_smoke"
    assert dummy_result.metrics[0].as_dict()["name"] == "accuracy"

    dummy_payload = json.loads(dummy_output.read_text(encoding="utf-8"))
    _assert_result_schema(dummy_payload, expected_status="completed")
    _assert_metric_schema(dummy_payload["metrics"][0])
    assert dummy_payload["metadata"]["suite"] == "evaluation_scaffold_smoke"

    persisted_path = persist_eval_result(dummy_result, direct_output)
    assert persisted_path == direct_output
    direct_payload = json.loads(direct_output.read_text(encoding="utf-8"))
    assert direct_payload == dummy_payload

    adapter = LMEvalAdapter(tasks=["arc_easy"], num_fewshot=1, batch_size=2)
    planned_result = run_eval_adapter(
        adapter,
        model=object(),
        dataset=None,
        task_name="arc_easy",
        output_path=planned_output,
        metadata={"suite": "evaluation_scaffold_smoke"},
    )

    assert planned_result.status == "planned"
    assert planned_result.metadata["integration_status"] == "scaffold_only"
    assert planned_result.metadata["tasks"] == ["arc_easy"]
    assert planned_result.metadata["num_fewshot"] == 1
    assert planned_result.metadata["batch_size"] == 2
    assert planned_result.started_at is not None
    assert planned_result.finished_at is not None
    assert planned_result.duration_seconds is not None

    planned_payload = json.loads(planned_output.read_text(encoding="utf-8"))
    _assert_result_schema(planned_payload, expected_status="planned")
    assert planned_payload["metrics"] == []
    assert planned_payload["metadata"]["integration_status"] == "scaffold_only"
    assert planned_payload["metadata"]["suite"] == "evaluation_scaffold_smoke"

    print(
        json.dumps(
            {
                "dummy_output": str(dummy_output),
                "planned_output": str(planned_output),
                "direct_output": str(direct_output),
            },
            indent=2,
            ensure_ascii=False,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Smoke test xTuring evaluation persistence and scaffold adapters."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory where smoke JSON files should be written.",
    )
    args = parser.parse_args()

    if args.output_dir is None:
        with tempfile.TemporaryDirectory(prefix="xturing-eval-smoke-") as tmpdir:
            _run_smoke(Path(tmpdir))
    else:
        _run_smoke(args.output_dir)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
