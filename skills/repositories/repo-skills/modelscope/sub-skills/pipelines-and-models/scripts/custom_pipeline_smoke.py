#!/usr/bin/env python3
"""Safe local ModelScope custom pipeline smoke test.

This script registers an in-process custom pipeline, instantiates it through
modelscope.pipelines.pipeline(), exercises single/list/batched calls on CPU, and
optionally checks JSON Config loading. It does not download models, train, touch
CUDA intentionally, require the ModelScope source checkout, or write outside a
TemporaryDirectory.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List


TASK = "disco-local-smoke-task"
PIPELINE_NAME = "disco-local-smoke-pipeline"


def _write_config(tmp: Path) -> Path:
    cfg = {
        "framework": "dummy",
        "task": TASK,
        "pipeline": {"type": PIPELINE_NAME},
    }
    cfg_path = tmp / "configuration.json"
    cfg_path.write_text(json.dumps(cfg, indent=2, sort_keys=True), encoding="utf-8")
    return cfg_path


def run_smoke(verbose: bool = False) -> int:
    try:
        from modelscope.outputs import OutputKeys
        from modelscope.pipelines import Pipeline, pipeline
        from modelscope.pipelines.builder import PIPELINES
    except Exception as exc:  # pragma: no cover - depends on caller env
        print(f"FAIL import: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    if PIPELINES.get(PIPELINE_NAME, group_key=TASK) is None:

        @PIPELINES.register_module(group_key=TASK, module_name=PIPELINE_NAME)
        class DiscoLocalSmokePipeline(Pipeline):  # type: ignore[unused-ignore]
            """Minimal deterministic pipeline for local registry validation."""

            def __init__(self, config_file: str | None = None, model=None, preprocessor=None, **kwargs):
                device = kwargs.pop("device", "cpu")
                auto_collate = kwargs.pop("auto_collate", False)
                if preprocessor is None:
                    preprocessor = lambda value, **_: value
                super().__init__(
                    config_file=config_file,
                    model=model,
                    preprocessor=preprocessor,
                    device=device,
                    auto_collate=auto_collate,
                    **kwargs,
                )
                # The local directory is used only so the base class can read
                # configuration.json. This smoke pipeline has no model object
                # and should not run model preparation.
                self.model = None
                self.models = [None]
                self.has_multiple_models = False

            def _sanitize_parameters(self, suffix: str = "", **kwargs):
                return {}, {}, {"suffix": suffix}

            def preprocess(self, inputs: Any, **preprocess_params) -> Dict[str, Any]:
                return {"text": str(inputs)}

            def forward(self, inputs: Dict[str, Any], **forward_params) -> Dict[str, Any]:
                text = inputs["text"]
                if isinstance(text, list):
                    return {"text": [item.upper() for item in text]}
                return {"text": text.upper()}

            def postprocess(self, inputs: Dict[str, Any], suffix: str = "") -> Dict[str, Any]:
                return {OutputKeys.TEXT: inputs["text"] + suffix}

    with tempfile.TemporaryDirectory(prefix="modelscope-smoke-") as tmp_name:
        cfg_path = _write_config(Path(tmp_name))
        try:
            pipe = pipeline(
                task=TASK,
                pipeline_name=PIPELINE_NAME,
                model=str(cfg_path.parent),
                device="cpu",
                trust_remote_code=False,
            )
            single = pipe("abc", suffix="!")
            listed = pipe(["a", "b"], suffix="?")
            batched = pipe(["x", "y", "z"], batch_size=2, suffix=".")
        except Exception as exc:
            print(f"FAIL smoke: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 1

    expected_single = {"text": "ABC!"}
    expected_list: List[Dict[str, str]] = [{"text": "A?"}, {"text": "B?"}]
    expected_batch: List[Dict[str, str]] = [{"text": "X."}, {"text": "Y."}, {"text": "Z."}]
    if single != expected_single:
        print(f"FAIL single: expected {expected_single!r}, got {single!r}", file=sys.stderr)
        return 1
    if listed != expected_list:
        print(f"FAIL list: expected {expected_list!r}, got {listed!r}", file=sys.stderr)
        return 1
    if batched != expected_batch:
        print(f"FAIL batch: expected {expected_batch!r}, got {batched!r}", file=sys.stderr)
        return 1

    if verbose:
        print("single=", single)
        print("list=", listed)
        print("batch=", batched)
    print("PASS custom pipeline smoke: registry, config_file, CPU single/list/batch")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run a deterministic local ModelScope custom pipeline smoke test "
            "without downloads, training, CUDA, or source-checkout dependencies."
        )
    )
    parser.add_argument("--verbose", action="store_true", help="Print successful smoke outputs.")
    args = parser.parse_args(argv)
    return run_smoke(verbose=args.verbose)


if __name__ == "__main__":
    raise SystemExit(main())
