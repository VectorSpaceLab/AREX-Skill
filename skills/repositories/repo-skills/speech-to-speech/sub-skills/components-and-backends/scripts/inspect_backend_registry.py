#!/usr/bin/env python3
"""Print speech-to-speech backend registry and dataclass defaults as JSON.

This script imports registry metadata only. It does not instantiate handlers,
load models, open devices, or connect to providers.
"""

from __future__ import annotations

import dataclasses
import json
from typing import Any

from speech_to_speech.backend_registry import LLM_BACKENDS, STT_BACKENDS, TTS_BACKENDS
from speech_to_speech.arguments_classes.module_arguments import ModuleArguments
from speech_to_speech.arguments_classes.qwen3_tts_arguments import Qwen3TTSHandlerArguments
from speech_to_speech.arguments_classes.responses_api_language_model_arguments import (
    ResponsesApiLanguageModelHandlerArguments,
)
from speech_to_speech.arguments_classes.vad_arguments import VADHandlerArguments


def dataclass_defaults(cls: type[Any]) -> dict[str, Any]:
    if not dataclasses.is_dataclass(cls):
        return {}
    obj = cls()
    out: dict[str, Any] = {}
    for field in dataclasses.fields(obj):
        value = getattr(obj, field.name)
        if isinstance(value, (str, int, float, bool, type(None))):
            out[field.name] = value
        elif isinstance(value, (list, tuple)):
            out[field.name] = list(value)
        elif isinstance(value, dict):
            out[field.name] = value
        else:
            out[field.name] = repr(value)
    return out


def registry_to_json(kind: str, registry: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for name, spec in registry.items():
        rows.append(
            {
                "name": name,
                "kind": kind,
                "config_type": spec.config_type.__name__,
                "required_extra": spec.required_extra,
                "capabilities": dataclasses.asdict(spec.capabilities),
                "config_defaults": dataclass_defaults(spec.config_type),
            }
        )
    return rows


def main() -> None:
    payload = {
        "module_defaults": dataclass_defaults(ModuleArguments),
        "vad_defaults": dataclass_defaults(VADHandlerArguments),
        "responses_api_defaults": dataclass_defaults(ResponsesApiLanguageModelHandlerArguments),
        "qwen3_tts_defaults": dataclass_defaults(Qwen3TTSHandlerArguments),
        "registries": {
            "stt": registry_to_json("stt", STT_BACKENDS),
            "llm": registry_to_json("llm", LLM_BACKENDS),
            "tts": registry_to_json("tts", TTS_BACKENDS),
        },
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
