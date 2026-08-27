#!/usr/bin/env python3
"""Safe smoke checks for MTEB evaluation workflow behavior.

Default mode is safe in lightweight environments: it reports whether mteb can be
imported and whether the expected evaluation API is present. If dependencies for
a local mock evaluation are available, it also exercises cache overwrite behavior
without downloading datasets or models.

Use `--strict` to convert any failed import/signature/mock check into a non-zero
exit code for CI.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import tempfile
from pathlib import Path
from typing import Any


EXPECTED_EVALUATE_PARAMETERS = {
    "model",
    "tasks",
    "co2_tracker",
    "raise_error",
    "encode_kwargs",
    "cache",
    "overwrite_strategy",
    "prediction_folder",
    "show_progress_bar",
    "public_only",
    "num_proc",
}


def import_optional(name: str) -> tuple[Any | None, str | None]:
    try:
        return importlib.import_module(name), None
    except Exception as exc:  # noqa: BLE001 - diagnostic script should report all import failures
        return None, f"{type(exc).__name__}: {exc}"


def check_signature(mteb: Any) -> dict[str, Any]:
    signature = inspect.signature(mteb.evaluate)
    missing = sorted(EXPECTED_EVALUATE_PARAMETERS.difference(signature.parameters))
    return {
        "ok": not missing,
        "signature": str(signature),
        "missing_parameters": missing,
    }


def run_mock_cache_check(mteb: Any, numpy: Any, datasets: Any) -> dict[str, Any]:
    from mteb.abstasks import AbsTaskClassification
    from mteb.abstasks.task_metadata import TaskMetadata
    from mteb.models import ModelMeta

    class TinyEncoder:
        """Deterministic encoder for local mock samples."""

        def __init__(self) -> None:
            self.seen_kwargs: list[dict[str, Any]] = []
            self.mteb_model_meta = ModelMeta(
                loader=None,
                name="skill-smoke/tiny-encoder",
                revision="local",
                release_date=None,
                languages=["eng-Latn"],
                n_parameters=0,
                memory_usage_mb=0,
                max_tokens=16,
                embed_dim=4,
                license="not specified",
                open_weights=True,
                public_training_code=None,
                public_training_data=None,
                framework=[],
                reference=None,
                similarity_fn_name=None,
                use_instructions=None,
                training_datasets=None,
                adapted_from=None,
                superseded_by=None,
                modalities=["text"],
            )

        def encode(self, inputs: Any, **kwargs: Any) -> Any:
            self.seen_kwargs.append(dict(kwargs))
            try:
                size = len(inputs.dataset)
            except AttributeError:
                size = len(inputs)
            rows = [[float(index), 1.0, 0.0, 0.5] for index in range(size)]
            return numpy.asarray(rows, dtype=numpy.float32)

    class TinyClassificationTask(AbsTaskClassification):
        metadata = TaskMetadata(
            name="SkillSmokeClassification",
            description="Tiny local classification task for evaluation smoke checks.",
            reference=None,
            dataset={"path": "skill-smoke/classification"},
            type="Classification",
            category="s2s",
            modalities=["text"],
            eval_splits=["test"],
            eval_langs=["eng-Latn"],
            main_score="accuracy",
            date=("2026-01-01", "2026-01-01"),
            domains=["Written"],
            task_subtypes=[],
            license="not specified",
            annotations_creators="derived",
            dialect=[],
            sample_creation="created",
            bibtex_citation="",
            prompt=None,
            n_samples={"test": 4},
            avg_character_length={"test": 7.0},
        )
        samples_per_label = 2

        def load_data(self, **kwargs: Any) -> None:
            rows = {
                "text": ["alpha", "beta", "gamma", "delta"],
                "label": [0, 0, 1, 1],
            }
            self.dataset = datasets.DatasetDict(
                {
                    "train": datasets.Dataset.from_dict(rows),
                    "test": datasets.Dataset.from_dict(rows),
                }
            )
            self.data_loaded = True

    model = TinyEncoder()
    task = TinyClassificationTask()

    with tempfile.TemporaryDirectory(prefix="mteb-skill-smoke-") as tmpdir:
        cache = mteb.ResultCache(cache_path=tmpdir)

        only_cache_empty_failed = False
        try:
            mteb.evaluate(
                model,
                task,
                cache=cache,
                overwrite_strategy="only-cache",
                co2_tracker=False,
                show_progress_bar=False,
            )
        except ValueError as exc:
            if "only-cache" not in str(exc):
                raise
            only_cache_empty_failed = True

        if not only_cache_empty_failed:
            raise AssertionError("only-cache unexpectedly evaluated without cache")

        first = mteb.evaluate(
            model,
            task,
            cache=cache,
            overwrite_strategy="only-missing",
            encode_kwargs={"batch_size": 2, "show_progress_bar": False},
            co2_tracker=False,
            show_progress_bar=False,
        )
        if len(first.task_results) != 1:
            raise AssertionError("expected one task result from first evaluation")
        if not model.seen_kwargs or model.seen_kwargs[-1].get("batch_size") != 2:
            raise AssertionError("batch_size encode kwarg was not forwarded")

        cached = mteb.evaluate(
            model,
            task,
            cache=cache,
            overwrite_strategy="only-cache",
            co2_tracker=False,
            show_progress_bar=False,
        )
        if len(cached.task_results) != 1:
            raise AssertionError("expected one cached task result")

        return {
            "ok": True,
            "only_cache_empty_failed": only_cache_empty_failed,
            "first_score": first.task_results[0].get_score(),
            "cached_score": cached.task_results[0].get_score(),
            "task_name": cached.task_results[0].task_name,
            "cache_path_removed": not Path(tmpdir).exists(),
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when import, signature, or optional mock checks fail.",
    )
    args = parser.parse_args()

    payload: dict[str, Any] = {"ok": True, "checks": {}}
    mteb, mteb_error = import_optional("mteb")
    if mteb is None:
        payload["ok"] = False
        payload["checks"]["import_mteb"] = {"ok": False, "error": mteb_error}
        payload["remediation"] = "Install or repair mteb in the active Python environment, then rerun with --strict."
        print(json.dumps(payload, sort_keys=True))
        return 1 if args.strict else 0

    payload["checks"]["import_mteb"] = {
        "ok": True,
        "version": getattr(mteb, "__version__", "unknown"),
    }
    payload["checks"]["signature"] = check_signature(mteb)
    payload["ok"] = payload["ok"] and payload["checks"]["signature"]["ok"]

    numpy, numpy_error = import_optional("numpy")
    datasets, datasets_error = import_optional("datasets")
    if numpy is None or datasets is None:
        payload["checks"]["mock_evaluation"] = {
            "ok": False,
            "skipped": True,
            "reason": "Optional dependencies for local mock evaluation are unavailable.",
            "numpy_error": numpy_error,
            "datasets_error": datasets_error,
        }
        if args.strict:
            payload["ok"] = False
    else:
        try:
            payload["checks"]["mock_evaluation"] = run_mock_cache_check(
                mteb, numpy, datasets
            )
        except Exception as exc:  # noqa: BLE001 - return actionable diagnostics
            payload["checks"]["mock_evaluation"] = {
                "ok": False,
                "error": f"{type(exc).__name__}: {exc}",
            }
            payload["ok"] = False

    print(json.dumps(payload, sort_keys=True))
    return 0 if payload["ok"] or not args.strict else 1


if __name__ == "__main__":
    raise SystemExit(main())
