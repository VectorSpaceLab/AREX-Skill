#!/usr/bin/env python3
"""Small self-contained PaddleX pipeline smoke helper.

This helper intentionally does not depend on a PaddleX source checkout. Run it
inside an environment where PaddleX is installed. A real pipeline run may
trigger model downloads; use --dry-run for a no-download import/API check.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict


SAVE_METHODS = [
    "save_to_json",
    "save_to_img",
    "save_to_csv",
    "save_to_html",
    "save_to_xlsx",
    "save_to_markdown",
    "save_to_video",
]


def _json_arg(value: str | None, label: str) -> Dict[str, Any] | None:
    if value in (None, ""):
        return None
    try:
        data = json.loads(value)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON for {label}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{label} must decode to a JSON object")
    return data


def _load_input(raw: str | None, input_json: str | None) -> Any:
    if input_json:
        try:
            return json.loads(input_json)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid --input-json: {exc}") from exc
    if raw is None:
        raise SystemExit("Provide --input for a real run, or use --dry-run")
    return raw


def _save_result(result: Any, save_path: Path) -> Dict[str, str]:
    save_path.mkdir(parents=True, exist_ok=True)
    status: Dict[str, str] = {}
    for method_name in SAVE_METHODS:
        method = getattr(result, method_name, None)
        if not callable(method):
            status[method_name] = "not-supported"
            continue
        try:
            method(str(save_path))
        except Exception as exc:  # noqa: BLE001 - report all save method failures.
            status[method_name] = f"failed: {type(exc).__name__}: {exc}"
        else:
            status[method_name] = "ok"
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pipeline", default="image_classification", help="Built-in pipeline name or local YAML path")
    parser.add_argument("--input", help="Input path, URL, directory, or scalar accepted by the selected pipeline")
    parser.add_argument("--input-json", help="JSON value to pass as the input object instead of --input")
    parser.add_argument("--save-path", default="paddlex_pipeline_smoke_out", help="Directory for result artifacts")
    parser.add_argument("--device", default="cpu", help="PaddleX device string, e.g. cpu, gpu:0, gpu:0,1")
    parser.add_argument("--engine", help="Optional inference engine override")
    parser.add_argument("--engine-config-json", help="JSON object for create_pipeline(engine_config=...)")
    parser.add_argument("--hpi-config-json", help="JSON object for create_pipeline(hpi_config=...)")
    parser.add_argument("--kwargs-json", help="Additional JSON object passed as create_pipeline(**kwargs)")
    parser.add_argument("--predict-kwargs-json", help="JSON object passed as pipeline.predict(..., **kwargs)")
    parser.add_argument("--use-hpip", action="store_true", help="Set create_pipeline(use_hpip=True)")
    parser.add_argument("--max-results", type=int, default=3, help="Maximum results to consume from the generator")
    parser.add_argument("--dry-run", action="store_true", help="Only verify imports/API availability; do not create a pipeline")
    args = parser.parse_args()

    import paddlex  # noqa: WPS433 - intentional runtime check.
    from paddlex import create_pipeline

    print(json.dumps({"paddlex_version": getattr(paddlex, "__version__", None)}, indent=2))

    if args.dry_run:
        print("DRY_RUN_OK: imported paddlex and resolved create_pipeline")
        return 0

    create_kwargs: Dict[str, Any] = _json_arg(args.kwargs_json, "--kwargs-json") or {}
    engine_config = _json_arg(args.engine_config_json, "--engine-config-json")
    hpi_config = _json_arg(args.hpi_config_json, "--hpi-config-json")
    predict_kwargs = _json_arg(args.predict_kwargs_json, "--predict-kwargs-json") or {}

    pipeline = create_pipeline(
        pipeline=args.pipeline,
        device=args.device,
        engine=args.engine,
        engine_config=engine_config,
        use_hpip=args.use_hpip or None,
        hpi_config=hpi_config,
        **create_kwargs,
    )
    input_data = _load_input(args.input, args.input_json)
    out_dir = Path(args.save_path)
    print(f"Created pipeline={args.pipeline!r}; writing artifacts under {out_dir}")

    consumed = 0
    for result in pipeline.predict(input_data, **predict_kwargs):
        consumed += 1
        print(f"--- result {consumed} ---")
        printer = getattr(result, "print", None)
        if callable(printer):
            printer()
        else:
            print(repr(result))
        save_status = _save_result(result, out_dir / f"result_{consumed:03d}")
        print(json.dumps(save_status, indent=2, sort_keys=True))
        if consumed >= args.max_results:
            break

    if consumed == 0:
        raise SystemExit("pipeline.predict produced no results")
    print(f"SMOKE_OK results={consumed} save_path={os.fspath(out_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
