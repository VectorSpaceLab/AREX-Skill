#!/usr/bin/env python3
"""Service-free smoke checks for tracing, logging, and config wiring.

The script keeps all artifacts under a caller-chosen directory or a temporary
folder. It exercises:

- `.env` loading with `setup_env`
- root/named logging with `get_logger`
- generator state and call loggers
- callback ordering with `CallbackManager`
- trace/span creation with a recording processor
- optional MLflow setup when installed
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence

import yaml

from adalflow.core.types import GeneratorOutput
from adalflow.tracing import (
    GLOBAL_TRACE_PROVIDER,
    GeneratorCallLogger,
    GeneratorStateLogger,
    NoOpTrace,
    custom_span,
    enable_mlflow_local,
    generator_span,
    get_trace_processors,
    set_trace_processors,
    set_tracing_disabled,
    trace,
)
from adalflow.tracing.callback_manager import CallbackManager
from adalflow.tracing.processor_interface import TracingProcessor
from adalflow.utils import get_adalflow_default_root_path, get_logger, setup_env


CONFIG_YAML = """
env:
  dotenv_name: .env
logging:
  name: tracing_smoke
  level: INFO
  enable_console: false
  enable_file: true
  filename: tracing_smoke.log
tracing:
  disabled: false
  trace_name: tracing_smoke
  state_project: tracing_smoke
  call_project: tracing_smoke
  state_filename: generator_state_trace.json
mlflow:
  enabled: true
  experiment_name: AdalFlow-Tracing-Smoke
  project_name: AdalFlow-Tracing-Smoke
  tracking_uri: null
""".strip()


@dataclass
class FakeGenerator:
    template: str
    prompt_kwargs: Dict[str, Any]


class RecordingTracingProcessor(TracingProcessor):
    def __init__(self) -> None:
        self.trace_starts: List[Dict[str, Any]] = []
        self.trace_ends: List[Dict[str, Any]] = []
        self.span_starts: List[Dict[str, Any]] = []
        self.span_ends: List[Dict[str, Any]] = []

    def on_trace_start(self, trace_obj) -> None:
        self.trace_starts.append(trace_obj.export())

    def on_trace_end(self, trace_obj) -> None:
        self.trace_ends.append(trace_obj.export())

    def on_span_start(self, span_obj) -> None:
        self.span_starts.append(span_obj.export())

    def on_span_end(self, span_obj) -> None:
        self.span_ends.append(span_obj.export())

    def shutdown(self) -> None:
        return None

    def force_flush(self) -> None:
        return None


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def flush_logger(logger) -> None:
    for handler in logger.handlers:
        flush = getattr(handler, "flush", None)
        if callable(flush):
            flush()


def run_callback_cycle(callback_manager: CallbackManager, output: GeneratorOutput) -> List[str]:
    events: List[str] = []

    def record(label: str):
        def _callback(**kwargs):
            events.append(label)

        return _callback

    callback_manager.register_callback("on_complete", record("complete"))
    callback_manager.register_callback("on_success", record("success"))
    callback_manager.register_callback("on_failure", record("failure"))

    payload = {
        "output": output,
        "input": {"input_str": "smoke"},
        "prompt_kwargs": {"input_str": "smoke"},
        "model_kwargs": {"model": "debug"},
    }
    callback_manager.trigger_callbacks("on_complete", **payload)
    if output.error:
        callback_manager.trigger_callbacks("on_failure", **payload)
    else:
        callback_manager.trigger_callbacks("on_success", **payload)
    return events


def exercise_env_setup(artifact_root: Path) -> Dict[str, Any]:
    env_path = artifact_root / ".env"
    write_text(
        env_path,
        "TRACING_SMOKE_KEEP=from_env\nTRACING_SMOKE_LOADED=1\nADALFLOW_DISABLE_TRACING=false\n",
    )

    previous_keep = os.environ.get("TRACING_SMOKE_KEEP")
    previous_loaded = os.environ.get("TRACING_SMOKE_LOADED")
    os.environ["TRACING_SMOKE_KEEP"] = "original"
    try:
        setup_env(dotenv_path=str(env_path))

        missing_env_ok = False
        try:
            setup_env(dotenv_path=str(artifact_root / "missing.env"))
        except FileNotFoundError:
            missing_env_ok = True

        assert os.environ["TRACING_SMOKE_KEEP"] == "original"
        assert os.environ["TRACING_SMOKE_LOADED"] == "1"

        default_root = Path(get_adalflow_default_root_path())

        return {
            "dotenv_loaded": True,
            "missing_env_raises": missing_env_ok,
            "default_root_tail": default_root.name,
        }
    finally:
        if previous_keep is None:
            os.environ.pop("TRACING_SMOKE_KEEP", None)
        else:
            os.environ["TRACING_SMOKE_KEEP"] = previous_keep

        if previous_loaded is None:
            os.environ.pop("TRACING_SMOKE_LOADED", None)
        else:
            os.environ["TRACING_SMOKE_LOADED"] = previous_loaded


def exercise_logging(artifact_root: Path) -> Dict[str, Any]:
    log_dir = artifact_root / "logs"
    logger = get_logger(
        name="tracing_smoke",
        level="INFO",
        save_dir=str(log_dir),
        filename="tracing_smoke.log",
        enable_console=False,
        enable_file=True,
    )
    logger.info("tracing smoke log message")
    flush_logger(logger)

    log_file = log_dir / "tracing_smoke.log"
    log_text = log_file.read_text(encoding="utf-8")

    return {
        "log_file": str(log_file),
        "logger_name": logger.name,
        "propagate": logger.propagate,
        "contains_message": "tracing smoke log message" in log_text,
    }


def exercise_state_logger(artifact_root: Path) -> Dict[str, Any]:
    traces_root = artifact_root / "traces"
    state_logger = GeneratorStateLogger(
        save_dir=str(traces_root),
        project_name="tracing_smoke",
        filename="generator_state_trace.json",
    )

    fake_generator = FakeGenerator(
        template="Hello {{name}}",
        prompt_kwargs={"name": "Ada"},
    )
    state_logger.log_prompt(fake_generator, name="demo_generator")
    state_logger.log_prompt(fake_generator, name="demo_generator")
    fake_generator.prompt_kwargs["name"] = "Flow"
    state_logger.log_prompt(fake_generator, name="demo_generator")

    log_file = Path(state_logger.get_log_location())
    content = json.loads(log_file.read_text(encoding="utf-8"))

    return {
        "log_file": str(log_file),
        "record_count": len(content["demo_generator"]),
        "latest_name": content["demo_generator"][-1]["prompt_states"]["data"]["prompt_kwargs"]["name"],
    }


def exercise_call_logger(artifact_root: Path) -> Dict[str, Any]:
    traces_root = artifact_root / "traces"
    call_logger = GeneratorCallLogger(
        save_dir=str(traces_root),
        project_name="tracing_smoke",
    )
    call_logger.register_generator("demo_generator")

    success_output = GeneratorOutput(
        data="ok",
        error=None,
        raw_response="ok",
        metadata={"kind": "success"},
    )
    failure_output = GeneratorOutput(
        data=None,
        error="boom",
        raw_response="boom",
        metadata={"kind": "failure"},
    )

    call_logger.log_call(
        name="demo_generator",
        output=success_output,
        input={"prompt": "ok"},
        prompt_kwargs={"name": "Ada"},
        model_kwargs={"model": "debug"},
    )
    call_logger.log_call(
        name="demo_generator",
        output=failure_output,
        input={"prompt": "fail"},
        prompt_kwargs={"name": "Flow"},
        model_kwargs={"model": "debug"},
    )

    records = call_logger.get_calls("demo_generator")
    log_file = Path(call_logger.get_log_location("demo_generator"))

    return {
        "log_file": str(log_file),
        "record_count": len(records),
        "last_error": records[-1].output.error,
    }


def exercise_callbacks() -> Dict[str, Any]:
    success_manager = CallbackManager()
    success_output = GeneratorOutput(data="ok", error=None, raw_response="ok")
    success_events = run_callback_cycle(success_manager, success_output)

    failure_manager = CallbackManager()
    failure_output = GeneratorOutput(data=None, error="boom", raw_response="boom")
    failure_events = run_callback_cycle(failure_manager, failure_output)

    return {
        "success_events": success_events,
        "failure_events": failure_events,
        "success_order_ok": success_events == ["complete", "success"],
        "failure_order_ok": failure_events == ["complete", "failure"],
    }


def exercise_mlflow(artifact_root: Path, config: Dict[str, Any], skip_mlflow: bool) -> Dict[str, Any]:
    original_disabled = GLOBAL_TRACE_PROVIDER._disabled
    original_processors = list(get_trace_processors())
    original_env_disable = os.environ.get("ADALFLOW_DISABLE_TRACING")
    result: Dict[str, Any] = {"attempted": False, "enabled": False}

    try:
        if skip_mlflow or not config["mlflow"]["enabled"]:
            result["reason"] = "skipped"
            return result

        result["attempted"] = True
        tracking_uri = config["mlflow"]["tracking_uri"] or str(artifact_root / "mlruns")

        try:
            enabled = enable_mlflow_local(
                tracking_uri=tracking_uri,
                experiment_name=config["mlflow"]["experiment_name"],
                project_name=config["mlflow"]["project_name"],
            )
        except Exception as exc:  # pragma: no cover - defensive smoke path
            result["error"] = f"{type(exc).__name__}: {exc}"
            return result

        result["enabled"] = bool(enabled)
        result["tracking_uri"] = tracking_uri

        if enabled:
            with trace("tracing_smoke_mlflow", metadata={"backend": "mlflow"}):
                with custom_span("mlflow_note", data={"status": "ok"}):
                    pass

        return result
    finally:
        set_trace_processors(original_processors)
        set_tracing_disabled(original_disabled)
        if original_env_disable is None:
            os.environ.pop("ADALFLOW_DISABLE_TRACING", None)
        else:
            os.environ["ADALFLOW_DISABLE_TRACING"] = original_env_disable


def exercise_tracing() -> Dict[str, Any]:
    original_disabled = GLOBAL_TRACE_PROVIDER._disabled
    original_processors = list(get_trace_processors())
    processor = RecordingTracingProcessor()

    try:
        set_tracing_disabled(True)
        disabled_trace = trace("disabled_check")
        assert isinstance(disabled_trace, NoOpTrace)

        set_tracing_disabled(False)
        set_trace_processors([processor])

        with trace("tracing_smoke", metadata={"suite": "observability"}) as root_trace:
            with custom_span(
                "debug_note",
                data={"phase": "config"},
                parent=root_trace,
            ):
                pass

            with generator_span(
                generator_id="demo_generator",
                model_kwargs={"model": "debug"},
                prompt_kwargs={"input_str": "trace smoke"},
                parent=root_trace,
            ) as generator_trace:
                generator_trace.span_data.update_attributes(
                    {
                        "raw_response": "raw",
                        "final_response": "done",
                        "generation_time_in_seconds": 0.01,
                    }
                )

        return {
            "trace_count": len(processor.trace_starts),
            "span_count": len(processor.span_starts),
            "trace_name": processor.trace_starts[0]["workflow_name"],
            "span_names": [span["span_data"]["name"] for span in processor.span_starts],
            "disabled_check": True,
            "trace_finished": processor.trace_ends[0]["workflow_name"],
            "span_export_names": [span["span_data"]["name"] for span in processor.span_ends],
        }
    finally:
        set_trace_processors(original_processors)
        set_tracing_disabled(original_disabled)


def build_config(artifact_root: Path, skip_mlflow: bool) -> Dict[str, Any]:
    config_path = artifact_root / "tracing_config.yaml"
    write_text(config_path, CONFIG_YAML)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["mlflow"]["tracking_uri"] = str(artifact_root / "mlruns")
    if skip_mlflow:
        config["mlflow"]["enabled"] = False
    config["paths"] = {
        "root": str(artifact_root),
        "config": str(config_path),
        "env": str(artifact_root / ".env"),
        "logs": str(artifact_root / "logs"),
        "traces": str(artifact_root / "traces"),
    }
    return config


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact-root",
        type=Path,
        default=None,
        help="Directory for smoke artifacts. Defaults to a temporary directory.",
    )
    parser.add_argument(
        "--skip-mlflow",
        action="store_true",
        help="Skip the optional MLflow setup step.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    artifact_root = args.artifact_root or Path(
        tempfile.mkdtemp(prefix="adalflow-tracing-smoke-")
    )
    artifact_root.mkdir(parents=True, exist_ok=True)

    config = build_config(artifact_root, skip_mlflow=args.skip_mlflow)
    summary: Dict[str, Any] = {"config": config["paths"]}

    summary["env"] = exercise_env_setup(artifact_root)
    summary["logging"] = exercise_logging(artifact_root)
    summary["state_logger"] = exercise_state_logger(artifact_root)
    summary["call_logger"] = exercise_call_logger(artifact_root)
    summary["callbacks"] = exercise_callbacks()
    summary["mlflow"] = exercise_mlflow(artifact_root, config, skip_mlflow=args.skip_mlflow)
    summary["tracing"] = exercise_tracing()

    summary_path = artifact_root / "summary.json"
    write_text(summary_path, json.dumps(summary, indent=2, sort_keys=True))

    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"Artifacts written to: {artifact_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
