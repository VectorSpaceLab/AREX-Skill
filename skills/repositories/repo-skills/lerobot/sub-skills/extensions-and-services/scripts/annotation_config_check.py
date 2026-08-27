#!/usr/bin/env python3
"""Check annotation config and synthetic staging rows locally only.

No VLM/HF client is imported, no endpoint is contacted, and no dataset shard is
read or rewritten. A rows file is an optional JSON list used only to exercise
staging invariants before a real annotation run.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

TOP_LEVEL = {
    "repo_id",
    "new_repo_id",
    "root",
    "staging_dir",
    "seed",
    "plan",
    "interjections",
    "vqa",
    "vlm",
    "executor",
    "job",
    "skip_validation",
    "only_episodes",
    "video_backend",
    "push_to_hub",
    "push_private",
    "push_commit_message",
}
NESTED = {
    "plan": {
        "enabled", "n_task_rephrasings", "derive_task_from_video", "derive_task_min_words",
        "frames_per_second", "max_frames_per_prompt", "contact_sheet_columns",
        "contact_sheet_frames_per_sheet", "contact_sheet_frame_width", "contact_sheet_quality",
        "min_subtask_seconds", "plan_max_steps", "subtask_describe_first", "subtask_seeded_relabel",
        "subtask_relabel_frames", "emit_plan", "emit_memory", "task_aug_axes",
    },
    "interjections": {"enabled", "max_interjections_per_episode", "interjection_min_t", "interjection_window_seconds", "interjection_window_frames"},
    "vqa": {"enabled", "vqa_emission_hz", "K", "question_types", "restrict_to_default_camera"},
    "vlm": {"backend", "model_id", "api_base", "api_key", "auto_serve", "serve_port", "serve_command", "parallel_servers", "num_gpus", "client_concurrency", "serve_ready_timeout_s", "max_new_tokens", "temperature", "camera_key", "chat_template_kwargs", "reasoning_effort"},
    "executor": {"episode_parallelism"},
    "job": {"target", "image", "timeout", "lerobot_ref", "detach", "tags"},
}
PERSISTENT = {"subtask", "plan", "memory", "motion", "task_aug"}
EVENTS = {"interjection", "vqa", "trace"}
VIEW_DEPENDENT = {"vqa", "trace"}
VQA_SHAPES = {
    "bbox": {"detections"},
    "keypoint": {"label", "point_format", "point"},
    "count": {"label", "count"},
    "attribute": {"label", "attribute", "value"},
    "spatial": {"subject", "relation", "object"},
}


def _load_mapping(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        value = json.loads(text)
    else:
        try:
            import yaml  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ValueError("YAML input needs PyYAML; use JSON or install the YAML dependency.") from exc
        value = yaml.safe_load(text)
    if not isinstance(value, dict):
        raise ValueError("configuration must contain a mapping/object at the top level")
    return value


def _number(value: Any, name: str, errors: list[str], *, minimum: float | None = None) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        errors.append(f"{name} must be numeric")
    elif minimum is not None and value < minimum:
        errors.append(f"{name} must be >= {minimum}")


def _integer(value: Any, name: str, errors: list[str], *, minimum: int | None = None) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        errors.append(f"{name} must be an integer")
    elif minimum is not None and value < minimum:
        errors.append(f"{name} must be >= {minimum}")


def _validate_config(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    unknown = sorted(set(config) - TOP_LEVEL)
    if unknown:
        errors.append(f"unknown top-level keys: {unknown}")
    if not config.get("root") and not config.get("repo_id"):
        errors.append("provide root for a local dataset or repo_id for a Hub dataset")
    for key in ("repo_id", "new_repo_id", "root", "staging_dir"):
        if key in config and config[key] is not None and not isinstance(config[key], str):
            errors.append(f"{key} must be a string/path value or null")
    episodes = config.get("only_episodes")
    if episodes is not None:
        if not isinstance(episodes, (list, tuple)):
            errors.append("only_episodes must be a list of non-negative integers")
        else:
            if any(isinstance(ep, bool) or not isinstance(ep, int) or ep < 0 for ep in episodes):
                errors.append("only_episodes must contain only non-negative integers")
            if len(episodes) != len(set(episodes)):
                errors.append("only_episodes must not contain duplicates")
    if config.get("push_to_hub") and not (config.get("new_repo_id") or config.get("repo_id")):
        errors.append("push_to_hub requires new_repo_id or repo_id")
    plan = config.get("plan", {})
    interjections = config.get("interjections", {})
    vqa = config.get("vqa", {})
    vlm = config.get("vlm", {})
    executor = config.get("executor", {})
    job = config.get("job", {})
    for section, values in (("plan", plan), ("interjections", interjections), ("vqa", vqa), ("vlm", vlm), ("executor", executor), ("job", job)):
        if not isinstance(values, dict):
            errors.append(f"{section} must be a mapping")
            continue
        extra = sorted(set(values) - NESTED[section])
        if extra:
            errors.append(f"unknown {section} keys: {extra}")
    if isinstance(plan, dict):
        _number(plan.get("frames_per_second", 2.0), "plan.frames_per_second", errors, minimum=0.000001)
        _integer(plan.get("max_frames_per_prompt", 60), "plan.max_frames_per_prompt", errors, minimum=1)
        _integer(plan.get("contact_sheet_columns", 5), "plan.contact_sheet_columns", errors, minimum=1)
        _integer(plan.get("plan_max_steps", 8), "plan.plan_max_steps", errors, minimum=1)
        if plan.get("derive_task_from_video", "if_short") not in {"off", "if_short", "always"}:
            errors.append("plan.derive_task_from_video must be off, if_short, or always")
    if isinstance(interjections, dict):
        _integer(interjections.get("max_interjections_per_episode", 3), "interjections.max_interjections_per_episode", errors, minimum=0)
        _number(interjections.get("interjection_min_t", 2.0), "interjections.interjection_min_t", errors, minimum=0)
    if isinstance(vqa, dict):
        _number(vqa.get("vqa_emission_hz", 1.0), "vqa.vqa_emission_hz", errors, minimum=0.000001)
        _integer(vqa.get("K", 1), "vqa.K", errors, minimum=1)
        allowed = {"bbox", "keypoint", "count", "attribute", "spatial"}
        question_types = vqa.get("question_types", ["bbox", "keypoint", "count", "attribute", "spatial"])
        if (
            not isinstance(question_types, (list, tuple))
            or not question_types
            or not set(question_types) <= allowed
        ):
            errors.append(f"vqa.question_types must be a non-empty subset of {sorted(allowed)}")
    if isinstance(vlm, dict):
        if vlm.get("backend", "openai") not in {"openai", "stub"}:
            errors.append("vlm.backend must be openai or stub")
        for key in ("model_id", "api_base"):
            if not isinstance(vlm.get(key), str) or not vlm[key].strip():
                errors.append(f"vlm.{key} must be a non-empty string")
        if isinstance(vlm.get("api_base", ""), str):
            parsed = urlparse(vlm.get("api_base", ""))
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                errors.append("vlm.api_base must be an http(s) URL; it is not contacted")
        port = vlm.get("serve_port", 8000)
        _integer(port, "vlm.serve_port", errors, minimum=1)
        if isinstance(port, int) and port > 65535:
            errors.append("vlm.serve_port must be <= 65535")
        for key in ("parallel_servers", "client_concurrency", "max_new_tokens"):
            _integer(vlm.get(key, {"parallel_servers": 1, "client_concurrency": 16, "max_new_tokens": 512}[key]), f"vlm.{key}", errors, minimum=1)
        _number(vlm.get("temperature", 0.2), "vlm.temperature", errors, minimum=0)
        _number(vlm.get("serve_ready_timeout_s", 600.0), "vlm.serve_ready_timeout_s", errors, minimum=0.000001)
    if isinstance(executor, dict):
        _integer(executor.get("episode_parallelism", 16), "executor.episode_parallelism", errors, minimum=1)
    if isinstance(job, dict):
        target = job.get("target")
        if target is not None and (not isinstance(target, str) or not target.strip()):
            errors.append("job.target must be null, local, or a non-empty HF Jobs flavor")
        if target not in (None, "local") and not config.get("repo_id"):
            errors.append("remote annotation requires repo_id; a local root is not visible in the pod")
    return errors


def _classify_vqa(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    keys = set(payload)
    for kind, required in VQA_SHAPES.items():
        if required <= keys:
            return kind
    return None


def _validate_rows(rows: list[Any], frame_timestamps: list[float]) -> list[str]:
    errors: list[str] = []
    frame_set = {float(ts) for ts in frame_timestamps}
    seen_vqa: set[tuple[float, str, str]] = set()
    interjection_times: set[float] = set()
    speech_times: set[float] = set()
    plan_times: set[float] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"row {index} is not an object")
            continue
        style = row.get("style")
        if style not in PERSISTENT | EVENTS and style is not None:
            errors.append(f"row {index}: unknown style {style!r}")
        column = "language_persistent" if style in PERSISTENT else "language_events"
        if row.get("_column", column) != column:
            errors.append(f"row {index}: style {style!r} must route to {column}")
        camera = row.get("camera")
        if style in VIEW_DEPENDENT and not isinstance(camera, str):
            errors.append(f"row {index}: view-dependent style {style!r} requires camera")
        if style not in VIEW_DEPENDENT and camera is not None:
            errors.append(f"row {index}: style {style!r} must have camera=null")
        timestamp = row.get("timestamp")
        timestamp_value: float | None = None
        if timestamp is not None:
            try:
                timestamp_value = float(timestamp)
            except (TypeError, ValueError):
                errors.append(f"row {index}: timestamp must be numeric")
        if column == "language_events":
            if timestamp_value is None or timestamp_value not in frame_set:
                errors.append(f"row {index}: event timestamp must exactly match a source frame")
        if style == "interjection" and timestamp_value is not None:
            interjection_times.add(timestamp_value)
        if style is None and row.get("role") == "assistant" and timestamp_value is not None:
            speech_times.add(timestamp_value)
        if style == "plan" and timestamp_value is not None:
            plan_times.add(timestamp_value)
        if style == "vqa":
            key = (timestamp_value, str(camera), str(row.get("role"))) if timestamp_value is not None else None
            if key is not None:
                if key in seen_vqa:
                    errors.append(f"row {index}: duplicate VQA role at timestamp/camera")
                seen_vqa.add(key)
            if row.get("role") == "assistant":
                content = row.get("content")
                try:
                    payload = json.loads(content)
                except (TypeError, ValueError):
                    errors.append(f"row {index}: VQA assistant content is not valid JSON")
                else:
                    if _classify_vqa(payload) is None:
                        errors.append(f"row {index}: VQA assistant JSON has no known answer shape")
    for timestamp in sorted(interjection_times):
        if timestamp not in speech_times:
            errors.append(f"interjection at {timestamp} has no paired speech atom")
        if timestamp not in plan_times:
            errors.append(f"interjection at {timestamp} has no same-time plan refresh")
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate local annotation config and optional synthetic staging rows. "
            "Never calls a VLM/Hub endpoint, starts vLLM, submits Jobs, or rewrites parquet."
        )
    )
    parser.add_argument("--config", type=Path, help="Local JSON/YAML AnnotationPipelineConfig mapping.")
    parser.add_argument("--rows", type=Path, help="Optional JSON list of synthetic staging rows.")
    parser.add_argument("--frame-timestamps", type=float, nargs="*", default=[], help="Source timestamps for --rows.")
    parser.add_argument("--job-target", dest="job_target", help="Local override for job.target.")
    parser.add_argument("--repo-id", dest="repo_id", help="Local override; value is not contacted or printed.")
    parser.add_argument("--root", help="Local dataset root override; it is not read.")
    parser.add_argument("--push-to-hub", action="store_true", help="Validate push target presence only; never upload.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        config = _load_mapping(args.config) if args.config else {}
    except (OSError, ValueError) as exc:
        print(f"INVALID annotation configuration: {exc}", file=sys.stderr)
        print("No endpoint, credential, daemon, Hub, or parquet write was attempted.", file=sys.stderr)
        return 2
    for key, value in (("job_target", args.job_target), ("repo_id", args.repo_id), ("root", args.root)):
        if value is not None:
            if key == "job_target":
                if "job" in config and not isinstance(config["job"], dict):
                    print("INVALID annotation configuration: job must be a mapping", file=sys.stderr)
                    print("No endpoint, credential, daemon, Hub, or parquet write was attempted.", file=sys.stderr)
                    return 2
                config.setdefault("job", {})["target"] = value
            else:
                config[key] = value
    if args.push_to_hub:
        config["push_to_hub"] = True
    errors = _validate_config(config)
    if args.rows:
        try:
            rows_value = json.loads(args.rows.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            errors.append(f"could not read JSON rows: {exc}")
        else:
            if not isinstance(rows_value, list):
                errors.append("rows file must contain a JSON list")
            elif not args.frame_timestamps:
                errors.append("--frame-timestamps is required when --rows is supplied")
            else:
                errors.extend(_validate_rows(rows_value, args.frame_timestamps))
    if errors:
        print("INVALID annotation configuration/staging", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        print("No endpoint, credential, daemon, Hub, or parquet write was attempted.", file=sys.stderr)
        return 2
    print(json.dumps({"config_valid": True, "rows_checked": bool(args.rows), "remote_checked": False}, indent=2))
    print("Local validation passed; VLM readiness, credentials, dataset contents, and publication remain unchecked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
