# Voice Pipeline Reference

Use this reference when a task asks for `VoicePipeline`, `AudioInput`, `StreamedAudioInput`, speech-to-text/text-to-speech orchestration, or the `openai-agents[voice]` optional dependency group.

## Voice Pipeline vs Realtime Session

| Need | Use | Why |
| --- | --- | --- |
| Low-latency bidirectional model session with direct Realtime API events | `RealtimeAgent` + `RealtimeRunner` | One live realtime transport streams input/output, tools, interruptions, raw events, and handoffs. |
| Speech input → normal SDK workflow → spoken output | `VoicePipeline` | Pipeline runs STT, then normal agent/workflow code, then TTS. |
| Normal text streaming over HTTP/SSE | `Runner.run_streamed` | Not realtime voice; route to ../core-runtime/SKILL.md. |

`agents.realtime` imports under the base install. `agents.voice` requires optional dependencies, currently including `numpy` and `websockets`, installed with:

```bash
pip install 'openai-agents[voice]'
```

If `agents.voice` raises an import error mentioning `numpy` and `websockets`, install the `voice` extra rather than unrelated optional groups.

## Pipeline Model

`VoicePipeline` is a three-step pipeline:

1. Speech-to-text turns audio into text.
2. Your workflow turns text into one or more text chunks.
3. Text-to-speech turns those chunks into streamed audio events.

The pipeline class:

```python
from agents.voice import VoicePipeline

pipeline = VoicePipeline(
    workflow=my_workflow,
    stt_model=None,
    tts_model=None,
    config=None,
)
```

Constructor fields:

| Field | Purpose |
| --- | --- |
| `workflow` | A `VoiceWorkflowBase` implementation that receives transcription text and yields response text. |
| `stt_model` | Optional `STTModel` instance or model name string. Defaults through the configured provider. |
| `tts_model` | Optional `TTSModel` instance or model name string. Defaults through the configured provider. |
| `config` | Optional `VoicePipelineConfig` for provider, tracing, STT settings, and TTS settings. |

## Audio Inputs

### Static AudioInput

Use `AudioInput` when the application already has a complete clip, such as push-to-talk audio or a pre-recorded sample.

```python
import numpy as np
from agents.voice import AudioInput

buffer = np.zeros(24_000 * 3, dtype=np.int16)
audio_input = AudioInput(buffer=buffer)
```

`AudioInput` fields:

| Field | Default | Notes |
| --- | --- | --- |
| `buffer` | required | Numpy array of `int16` or `float32`. |
| `frame_rate` | `24000` | Used when converting to WAV-style upload data. |
| `sample_width` | `2` | Bytes per sample for WAV conversion. |
| `channels` | `1` | Mono by default. |

Supported buffer dtypes are `np.int16` and `np.float32`. Other dtypes raise `UserError`. `float32` is clipped to `[-1.0, 1.0]` and converted to `int16` for file/base64 conversion.

### StreamedAudioInput

Use `StreamedAudioInput` when the application pushes chunks and wants the STT session to detect turns.

```python
from agents.voice import StreamedAudioInput

streamed_input = StreamedAudioInput()
await streamed_input.add_audio(audio_chunk_array)
await streamed_input.add_audio(None)  # marks end of stream for producers that use it
```

The example streamed app records `int16` microphone chunks at 24 kHz and pushes them into `StreamedAudioInput.add_audio(...)` while the pipeline is running.

## Workflows

### Single-Agent Workflow

For a normal single-agent voice app, use `SingleAgentVoiceWorkflow`:

```python
from agents import Agent
from agents.voice import SingleAgentVoiceWorkflow, VoicePipeline

agent = Agent(name="Assistant", instructions="Answer concisely.")
pipeline = VoicePipeline(workflow=SingleAgentVoiceWorkflow(agent))
```

`SingleAgentVoiceWorkflow` maintains input history and the current agent across turns. It runs `Runner.run_streamed(...)`, yields output text deltas, then updates its history from the result.

Optional callbacks:

```python
from agents.voice import SingleAgentVoiceWorkflow, SingleAgentWorkflowCallbacks

class Callbacks(SingleAgentWorkflowCallbacks):
    def on_run(self, workflow, transcription: str) -> None:
        log_transcription(transcription)

workflow = SingleAgentVoiceWorkflow(agent, callbacks=Callbacks())
```

### Custom Workflow

Subclass `VoiceWorkflowBase` when the response logic needs custom routing, external state, multiple agent calls, or non-agent logic.

```python
from collections.abc import AsyncIterator
from agents import Runner
from agents.voice import VoiceWorkflowBase, VoiceWorkflowHelper

class MyWorkflow(VoiceWorkflowBase):
    async def run(self, transcription: str) -> AsyncIterator[str]:
        if "secret word" in transcription.lower():
            yield "You guessed the secret word."
            return

        result = Runner.run_streamed(agent, [{"role": "user", "content": transcription}])
        async for text in VoiceWorkflowHelper.stream_text_from(result):
            yield text

    async def on_start(self) -> AsyncIterator[str]:
        yield "Ready when you are."
```

`VoiceWorkflowHelper.stream_text_from(...)` extracts text deltas from `RunResultStreaming.stream_events()` where raw response events are `response.output_text.delta`.

## Running a Pipeline

```python
result = await pipeline.run(audio_input)

async for event in result.stream():
    if event.type == "voice_stream_event_audio":
        play_audio(event.data)
    elif event.type == "voice_stream_event_lifecycle":
        handle_lifecycle(event.event)
    elif event.type == "voice_stream_event_error":
        report_error(event.error)
```

`VoicePipeline.run(...)` accepts either `AudioInput` or `StreamedAudioInput` and returns `StreamedAudioResult`.

Events emitted by `StreamedAudioResult.stream()`:

| Event class | `type` | Important field |
| --- | --- | --- |
| `VoiceStreamEventAudio` | `voice_stream_event_audio` | `data`, a numpy audio array or `None`. |
| `VoiceStreamEventLifecycle` | `voice_stream_event_lifecycle` | `event`, one of `turn_started`, `turn_ended`, `session_ended`. |
| `VoiceStreamEventError` | `voice_stream_event_error` | `error`, the exception that occurred. |

Tests verify that static and streamed runs produce `turn_started`, one or more `audio` events, `turn_ended`, and then `session_ended`; multi-turn streamed input repeats the turn sequence.

## VoicePipelineConfig

`VoicePipelineConfig` controls model lookup, tracing, and STT/TTS settings.

| Field | Default / purpose |
| --- | --- |
| `model_provider` | Defaults to `OpenAIVoiceModelProvider`; maps STT/TTS names to model implementations. |
| `tracing_disabled` | Whether to disable pipeline tracing. |
| `tracing` | Optional `TracingConfig`. |
| `trace_include_sensitive_data` | Whether transcripts and other sensitive text are included in traces; defaults true. |
| `trace_include_sensitive_audio_data` | Whether audio data is included in traces; defaults true. |
| `workflow_name` | Trace workflow name; defaults to `Voice Agent`. |
| `group_id` | Trace grouping id, auto-generated by default. |
| `trace_metadata` | Optional metadata dictionary for traces. |
| `stt_settings` | `STTModelSettings`. |
| `tts_settings` | `TTSModelSettings`. |

For privacy-sensitive voice apps, explicitly set `trace_include_sensitive_data=False` and `trace_include_sensitive_audio_data=False`, or disable tracing where policy requires it.

## STT Settings

`STTModelSettings` fields:

| Field | Purpose |
| --- | --- |
| `prompt` | Optional transcription instructions. |
| `language` | Optional input language hint. |
| `temperature` | Optional transcription temperature. |
| `turn_detection` | Provider-specific turn detection settings for streamed audio input. |

`STTModel` implementations expose:

- `model_name`
- `transcribe(AudioInput, settings, trace_include_sensitive_data, trace_include_sensitive_audio_data)`
- `create_session(StreamedAudioInput, settings, trace_include_sensitive_data, trace_include_sensitive_audio_data)` returning a `StreamedTranscriptionSession`

`StreamedTranscriptionSession.transcribe_turns()` yields turn transcripts and returns only after the session is closed.

## TTS Settings

`TTSModelSettings` fields:

| Field | Purpose |
| --- | --- |
| `voice` | Optional TTS voice, such as `alloy`, `ash`, `coral`, `echo`, `fable`, `onyx`, `nova`, `sage`, or `shimmer`. |
| `buffer_size` | Minimum chunk size for streamed output buffering; default is `120`. |
| `dtype` | Desired output array dtype, default `np.int16`. |
| `transform_data` | Optional callable to transform each output audio array. |
| `instructions` | TTS model instructions for reading partial text. |
| `text_splitter` | Callable that splits pending text into speakable chunks. |
| `speed` | Optional speech speed, typically between `0.25` and `4.0`. |

Tests cover odd-length audio buffers, cross-chunk sample boundaries, custom splitters, output dtypes, and `transform_data`.

## Interruption Expectations

Do not confuse `VoicePipeline` streamed input with `RealtimeSession` interruption handling:

- `RealtimeSession` supports `interrupt()`, `audio_interrupted`, server-side `interrupt_response`, and `RealtimePlaybackTracker`.
- `VoicePipeline` does not provide built-in interruption handling for `StreamedAudioInput`.
- Each detected streamed-audio turn triggers a separate workflow run.
- If an app needs voice-pipeline interruption semantics, listen for lifecycle events and implement app-level microphone/speaker gating.

The docs suggest muting the microphone when a `turn_started` lifecycle event indicates processing is beginning, then unmuting after the related audio is flushed after `turn_ended`.

## Model Provider Notes

The default `OpenAIVoiceModelProvider` supplies OpenAI STT/TTS models when `stt_model` or `tts_model` is omitted or passed as a string. Use custom `STTModel`, `TTSModel`, or `VoiceModelProvider` implementations when:

- The app uses non-OpenAI STT/TTS services.
- Tests need fake deterministic models.
- Audio data must be transformed, buffered, or routed through a custom provider.

For unit tests, prefer fake `STTModel`/`TTSModel` objects like the repo tests do; do not call real audio devices or network services.

## Tracing

Voice pipeline tracing wraps the full async processing lifecycle:

- Single-turn trace stays open until the workflow and TTS output finish.
- Multi-turn trace stays open until streamed turn processing ends.
- `workflow_name`, `group_id`, and `trace_metadata` help group traces across a conversation.
- `trace_include_sensitive_data` controls transcript-like sensitive data.
- `trace_include_sensitive_audio_data` controls raw audio in traces.

Recommended privacy-aware config:

```python
from agents.voice import VoicePipelineConfig

config = VoicePipelineConfig(
    workflow_name="Support voice workflow",
    trace_include_sensitive_data=False,
    trace_include_sensitive_audio_data=False,
)
```

## Safe Local Validation

Use [../scripts/check_realtime_config.py](../scripts/check_realtime_config.py) with `--check-voice` to detect whether the optional voice import surface is available without recording or playing audio. The helper imports `agents.voice` only and reports the install hint when the extra is missing.
