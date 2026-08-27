#!/usr/bin/env python3
"""Run safe CLI/default checks without starting a server or loading models.

This checker intentionally exercises only the lightweight command parser,
Realtime URL helper, and dataclass defaults. It does not invoke the pipeline
parser, which imports runtime components and may prepare first-run resources.
"""

from __future__ import annotations

import contextlib
import io

from speech_to_speech.arguments_classes.module_arguments import ModuleArguments
from speech_to_speech.arguments_classes.qwen3_tts_arguments import Qwen3TTSHandlerArguments
from speech_to_speech.arguments_classes.responses_api_language_model_arguments import (
    ResponsesApiLanguageModelHandlerArguments,
)
from speech_to_speech.arguments_classes.vad_arguments import VADHandlerArguments
from speech_to_speech.api.openai_realtime.audio_client import normalize_realtime_url
from speech_to_speech.cli import parse_command, parse_talk_arguments


def _expect_system_exit(callable_obj, *args: object) -> None:
    with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
        try:
            callable_obj(*args)
        except SystemExit:
            return
    raise AssertionError(f"expected parser rejection from {callable_obj.__name__}{args!r}")


def _check_commands() -> None:
    assert parse_command(["serve"]) == ("serve", [])
    assert parse_command(["talk", "--url", "ws://127.0.0.1:8765/v1/realtime"])[0] == "talk"
    assert parse_command(["local", "--port", "9876"])[0] == "local"

    with contextlib.redirect_stderr(io.StringIO()):
        assert parse_command(["--mode", "realtime", "--port", "9876"]) == ("serve", ["--port", "9876"])
    with contextlib.redirect_stderr(io.StringIO()):
        assert parse_command(["--mode=local"])[0] == "local"

    for removed_mode in ("socket", "raw-websocket", "websocket"):
        _expect_system_exit(parse_command, ["--mode", removed_mode])


def _check_talk_parser() -> None:
    config = parse_talk_arguments([])
    assert config.url == "ws://127.0.0.1:8765/v1/realtime"
    assert config.model == "local"
    assert config.api_key is None
    assert config.send_rate == 16000
    assert config.recv_rate == 16000
    assert config.chunk_size == 1024
    assert config.block_mic_during_playback is False

    remote = parse_talk_arguments(["--url", "wss://voice.example/v1/realtime", "--api-key", "secret"])
    assert remote.url == "wss://voice.example/v1/realtime"
    assert remote.api_key == "secret"

    for flag in ("--host", "--port", "--base-url", "--websocket-base-url", "--stt"):
        _expect_system_exit(parse_talk_arguments, [flag, "value"])

    assert normalize_realtime_url("https://voice.example/v1/realtime") == (
        "https://voice.example/v1",
        "wss://voice.example/v1",
    )
    for bad_url in (
        "127.0.0.1:8765/v1/realtime",
        "ws://127.0.0.1:8765/v1",
        "ws://127.0.0.1:8765/v1/realtime?token=secret",
    ):
        try:
            normalize_realtime_url(bad_url)
        except ValueError:
            continue
        raise AssertionError(f"expected URL validation failure for {bad_url!r}")


def _check_defaults() -> None:
    module = ModuleArguments()
    vad = VADHandlerArguments()
    llm = ResponsesApiLanguageModelHandlerArguments()
    tts = Qwen3TTSHandlerArguments()

    assert (module.stt, module.llm_backend, module.tts) == ("parakeet-tdt", "responses-api", "qwen3")
    assert module.enable_live_transcription is True
    assert module.live_transcription_update_interval == 0.5
    assert module.num_pipelines == 1
    assert module.enable_llm_proxy is False

    assert vad.thresh == 0.6
    assert vad.sample_rate == 16000
    assert vad.min_silence_ms == 64
    assert vad.min_speech_ms == 384
    assert vad.min_speech_continuation_ms == 192
    assert vad.smart_turn is True
    assert vad.smart_turn_threshold == 0.5
    assert vad.smart_turn_max_wait_ms == 2000
    assert vad.smart_turn_incomplete_delay_ms == 600

    assert llm.model_name == "gpt-5.4-mini"
    assert llm.responses_api_base_url is None
    assert llm.responses_api_api_key is None
    assert llm.responses_api_stream is True
    assert llm.responses_api_audio_content_type == "input_audio"

    assert tts.qwen3_tts_model_name == "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
    assert tts.qwen3_tts_speaker == "Aiden"
    assert tts.qwen3_tts_language == "auto"
    assert tts.qwen3_tts_backend == "ggml"
    assert tts.qwen3_tts_non_streaming_mode is True
    assert tts.qwen3_tts_mlx_quantization == "6bit"


def main() -> None:
    _check_commands()
    _check_talk_parser()
    _check_defaults()
    print("CLI profile/default smoke passed; no server or model was started")


if __name__ == "__main__":
    main()
