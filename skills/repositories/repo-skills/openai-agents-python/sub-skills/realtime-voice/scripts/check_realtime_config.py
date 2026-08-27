#!/usr/bin/env python3
"""Validate small OpenAI Agents realtime/voice configs without network or audio calls."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

KNOWN_AUDIO_FORMATS = {"pcm16", "g711_ulaw", "g711_alaw", "audio/pcm", "audio/pcmu", "audio/pcma"}
KNOWN_TURN_DETECTION_TYPES = {"semantic_vad", "server_vad"}
KNOWN_MODALITIES = {"text", "audio"}


def _load_config(args: argparse.Namespace) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    if args.config_json and args.config_file:
        raise ValueError("Use only one of --config-json or --config-file.")

    if args.config_json:
        raw = args.config_json
    elif args.config_file:
        raw = Path(args.config_file).read_text(encoding="utf-8")
    else:
        return {}, warnings

    loaded = json.loads(raw)
    if not isinstance(loaded, dict):
        raise ValueError("Config must be a JSON object.")
    return loaded, warnings


def _check_realtime_imports() -> tuple[dict[str, Any], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    details: dict[str, Any] = {}
    try:
        from agents.realtime import (  # noqa: PLC0415
            OpenAIRealtimeSIPModel,
            OpenAIRealtimeWebSocketModel,
            RealtimeAgent,
            RealtimePlaybackTracker,
            RealtimeRunner,
            RealtimeSession,
            realtime_handoff,
        )

        details["realtime_imports"] = {
            "RealtimeAgent": RealtimeAgent.__name__,
            "RealtimeRunner": RealtimeRunner.__name__,
            "RealtimeSession": RealtimeSession.__name__,
            "RealtimePlaybackTracker": RealtimePlaybackTracker.__name__,
            "OpenAIRealtimeWebSocketModel": OpenAIRealtimeWebSocketModel.__name__,
            "OpenAIRealtimeSIPModel": OpenAIRealtimeSIPModel.__name__,
            "realtime_handoff": getattr(realtime_handoff, "__name__", "realtime_handoff"),
        }
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Failed to import agents.realtime: {exc}")
    return details, warnings, errors


def _check_voice_import() -> tuple[dict[str, Any], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    details: dict[str, Any] = {}
    try:
        from agents.voice import (  # noqa: PLC0415
            AudioInput,
            SingleAgentVoiceWorkflow,
            StreamedAudioInput,
            VoicePipeline,
            VoicePipelineConfig,
        )

        details["voice_imports"] = {
            "AudioInput": AudioInput.__name__,
            "StreamedAudioInput": StreamedAudioInput.__name__,
            "SingleAgentVoiceWorkflow": SingleAgentVoiceWorkflow.__name__,
            "VoicePipeline": VoicePipeline.__name__,
            "VoicePipelineConfig": VoicePipelineConfig.__name__,
        }
    except ImportError as exc:
        errors.append(
            "Failed to import agents.voice. Install the optional voice extra with: "
            "pip install 'openai-agents[voice]'. Original error: "
            f"{exc}"
        )
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Failed to import agents.voice: {exc}")
    return details, warnings, errors


def _as_mapping(value: Any, path: str, errors: list[str]) -> Mapping[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return value
    errors.append(f"{path} must be an object when provided.")
    return {}


def _check_audio_format(value: Any, path: str, warnings: list[str], errors: list[str]) -> None:
    if value is None:
        return
    if isinstance(value, str):
        if value not in KNOWN_AUDIO_FORMATS:
            warnings.append(
                f"{path} uses unrecognized audio format {value!r}; known SDK examples use "
                "pcm16, g711_ulaw, or g711_alaw."
            )
        return
    if isinstance(value, Mapping):
        format_type = value.get("type")
        if format_type not in KNOWN_AUDIO_FORMATS:
            warnings.append(f"{path}.type is not a common realtime audio format: {format_type!r}.")
        if format_type in {"audio/pcm", "pcm16", "pcm"}:
            rate = value.get("rate", 24000)
            if rate != 24000:
                warnings.append(f"{path}.rate is {rate!r}; SDK PCM examples assume 24000 Hz.")
        return
    errors.append(f"{path} must be a string or object when provided.")


def _check_turn_detection(value: Any, path: str, warnings: list[str], errors: list[str]) -> None:
    if value is None:
        return
    mapping = _as_mapping(value, path, errors)
    detection_type = mapping.get("type")
    if detection_type is not None and detection_type not in KNOWN_TURN_DETECTION_TYPES:
        warnings.append(f"{path}.type is not one of {sorted(KNOWN_TURN_DETECTION_TYPES)}.")
    for bool_key in ("create_response", "interrupt_response"):
        if bool_key in mapping and not isinstance(mapping[bool_key], bool):
            errors.append(f"{path}.{bool_key} must be a boolean when provided.")
    for int_key in ("prefix_padding_ms", "silence_duration_ms", "idle_timeout_ms"):
        if int_key in mapping and not isinstance(mapping[int_key], int):
            errors.append(f"{path}.{int_key} must be an integer number of milliseconds.")
    if "threshold" in mapping and not isinstance(mapping["threshold"], (int, float)):
        errors.append(f"{path}.threshold must be numeric when provided.")


def _check_modalities(value: Any, path: str, warnings: list[str], errors: list[str]) -> None:
    if value is None:
        return
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        errors.append(f"{path} must be a list of strings when provided.")
        return
    unknown = [item for item in value if item not in KNOWN_MODALITIES]
    if unknown:
        warnings.append(f"{path} contains nonstandard modalities: {unknown!r}.")


def _check_model_settings(settings: Mapping[str, Any], warnings: list[str], errors: list[str]) -> None:
    model_name = settings.get("model_name")
    if model_name is not None and not isinstance(model_name, str):
        errors.append("model_settings.model_name must be a string when provided.")
    elif model_name and not model_name.startswith(("gpt-realtime", "gpt-4o-realtime")):
        warnings.append(
            "model_settings.model_name does not look like a realtime model name; "
            "new realtime agents usually start with gpt-realtime-2."
        )

    _check_modalities(settings.get("modalities"), "model_settings.modalities", warnings, errors)
    _check_modalities(
        settings.get("output_modalities"), "model_settings.output_modalities", warnings, errors
    )

    audio = settings.get("audio")
    if audio is not None:
        audio_mapping = _as_mapping(audio, "model_settings.audio", errors)
        input_audio = _as_mapping(
            audio_mapping.get("input"), "model_settings.audio.input", errors
        )
        output_audio = _as_mapping(
            audio_mapping.get("output"), "model_settings.audio.output", errors
        )
        _check_audio_format(
            input_audio.get("format"), "model_settings.audio.input.format", warnings, errors
        )
        _check_audio_format(
            output_audio.get("format"), "model_settings.audio.output.format", warnings, errors
        )
        _check_turn_detection(
            input_audio.get("turn_detection"),
            "model_settings.audio.input.turn_detection",
            warnings,
            errors,
        )
        transcription = input_audio.get("transcription")
        if transcription is not None:
            transcription_mapping = _as_mapping(
                transcription, "model_settings.audio.input.transcription", errors
            )
            transcription_model = transcription_mapping.get("model")
            if transcription_model is not None and not isinstance(transcription_model, str):
                errors.append("model_settings.audio.input.transcription.model must be a string.")
        speed = output_audio.get("speed")
        if speed is not None and not isinstance(speed, (int, float)):
            errors.append("model_settings.audio.output.speed must be numeric when provided.")

    _check_audio_format(
        settings.get("input_audio_format"), "model_settings.input_audio_format", warnings, errors
    )
    _check_audio_format(
        settings.get("output_audio_format"), "model_settings.output_audio_format", warnings, errors
    )
    _check_turn_detection(
        settings.get("turn_detection"), "model_settings.turn_detection", warnings, errors
    )

    if "output_type" in settings:
        errors.append("RealtimeAgent does not support structured outputs; do not use output_type.")


def _validate_config(config: Mapping[str, Any]) -> tuple[dict[str, Any], list[str], list[str]]:
    details: dict[str, Any] = {}
    warnings: list[str] = []
    errors: list[str] = []

    runner_config = _as_mapping(config.get("runner_config"), "runner_config", errors)
    run_model_config = _as_mapping(config.get("model_config"), "model_config", errors)

    direct_model_settings = config.get("model_settings")
    if direct_model_settings is not None:
        warnings.append(
            "Top-level model_settings detected; prefer runner_config.model_settings or "
            "model_config.initial_model_settings in app code."
        )
        _check_model_settings(_as_mapping(direct_model_settings, "model_settings", errors), warnings, errors)

    runner_model_settings = runner_config.get("model_settings")
    if runner_model_settings is not None:
        _check_model_settings(
            _as_mapping(runner_model_settings, "runner_config.model_settings", errors),
            warnings,
            errors,
        )

    initial_model_settings = run_model_config.get("initial_model_settings")
    if initial_model_settings is not None:
        _check_model_settings(
            _as_mapping(initial_model_settings, "model_config.initial_model_settings", errors),
            warnings,
            errors,
        )

    if "headers" in run_model_config:
        headers = _as_mapping(run_model_config.get("headers"), "model_config.headers", errors)
        lowered = {str(key).lower() for key in headers}
        if "authorization" not in lowered and "api-key" not in lowered:
            warnings.append(
                "model_config.headers is set without authorization/api-key; the SDK does not "
                "inject Authorization when custom headers are supplied."
            )

    if "call_id" in run_model_config and not isinstance(run_model_config.get("call_id"), str):
        errors.append("model_config.call_id must be a string for SIP attach flows.")

    if "async_tool_calls" in runner_config and not isinstance(runner_config["async_tool_calls"], bool):
        errors.append("runner_config.async_tool_calls must be a boolean when provided.")

    guardrails_settings = runner_config.get("guardrails_settings")
    if guardrails_settings is not None:
        guardrails_mapping = _as_mapping(
            guardrails_settings, "runner_config.guardrails_settings", errors
        )
        debounce = guardrails_mapping.get("debounce_text_length")
        if debounce is not None and not isinstance(debounce, int):
            errors.append("runner_config.guardrails_settings.debounce_text_length must be an integer.")

    tool_execution = runner_config.get("tool_execution")
    if tool_execution is not None:
        tool_execution_mapping = _as_mapping(tool_execution, "runner_config.tool_execution", errors)
        pre_approval = tool_execution_mapping.get("pre_approval_tool_input_guardrails")
        if pre_approval is not None and not isinstance(pre_approval, bool):
            errors.append(
                "runner_config.tool_execution.pre_approval_tool_input_guardrails must be boolean."
            )

    details["config_keys"] = sorted(config.keys())
    return details, warnings, errors


def _text_report(result: Mapping[str, Any]) -> str:
    lines = [f"ok: {result['ok']}"]
    for section in ("errors", "warnings"):
        values = result.get(section, [])
        if values:
            lines.append(f"{section}:")
            lines.extend(f"- {value}" for value in values)
    if not result.get("errors") and not result.get("warnings"):
        lines.append("No static realtime config issues found.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-json", help="Small JSON object to validate.")
    parser.add_argument("--config-file", help="Path to a JSON config object to validate.")
    parser.add_argument("--check-voice", action="store_true", help="Also import agents.voice.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)

    errors: list[str] = []
    warnings: list[str] = []
    details: dict[str, Any] = {"network_calls": False, "audio_device_calls": False}

    try:
        config, config_warnings = _load_config(args)
        warnings.extend(config_warnings)
    except Exception as exc:  # noqa: BLE001
        config = {}
        errors.append(str(exc))

    import_details, import_warnings, import_errors = _check_realtime_imports()
    details.update(import_details)
    warnings.extend(import_warnings)
    errors.extend(import_errors)

    if args.check_voice:
        voice_details, voice_warnings, voice_errors = _check_voice_import()
        details.update(voice_details)
        warnings.extend(voice_warnings)
        errors.extend(voice_errors)

    if config:
        config_details, config_warnings, config_errors = _validate_config(config)
        details.update(config_details)
        warnings.extend(config_warnings)
        errors.extend(config_errors)

    result = {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "details": details,
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(_text_report(result))

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
