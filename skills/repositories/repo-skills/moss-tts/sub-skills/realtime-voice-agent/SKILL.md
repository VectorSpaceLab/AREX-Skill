---
name: realtime-voice-agent
description: "Operate MOSS-TTS-Realtime low-latency voice-agent streaming,
  Gradio, FastAPI, sessions, text deltas, and reference prompts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# realtime-voice-agent

Use this sub-skill when the task is about **MOSS-TTS-Realtime** voice-agent workflows: low-latency conversational TTS, reference-prompt voice cloning, Gradio streaming demos, FastAPI streaming sessions, client payloads, text-delta bridges from an LLM, or single-turn and multi-turn Python streaming with KV-cache control.

## Route elsewhere

- MOSS-TTS-Local-Transformer-v1.5 local streaming, 48 kHz stereo codec-v2, continuation prompts, or v1.5 browser app behavior: `../local-v15-streaming/SKILL.md`.
- Generic Hugging Face model loading, non-Realtime family generation, model packaging, or broad HF API questions: `../hf-family-workflows/SKILL.md`.
- Fine-tuning, manifest preparation, dataset conversion, or training workflows: `../finetuning-data-prep/SKILL.md`.

## Minimum operating facts

- Realtime checkpoint: `OpenMOSS-Team/MOSS-TTS-Realtime`.
- Audio codec/tokenizer checkpoint: `OpenMOSS-Team/MOSS-Audio-Tokenizer`.
- Audio sample rate: 24 kHz mono for Realtime generation and service output.
- Recommended decoding defaults: temperature `0.8`, top-p `0.6`, top-k `30`, repetition penalty `1.1`, repetition window `50`.
- Streaming prefill normally waits for `12` stable text tokens unless the stream is finalized earlier.
- The bundled FastAPI service supports request/audio split sessions and currently assumes batch size `1`.

## Use the bundled references

- End-to-end local workflows, basic inference, Gradio, single-turn streaming, multi-turn KV-cache reuse, text deltas, and prompt audio: `references/streaming-workflows.md`.
- FastAPI server launch, endpoints, session flow, client behavior, response headers, and operational caveats: `references/fastapi-service.md`.
- Public classes, method contracts, constants, JSON schemas, and decoding defaults: `references/api-reference.md`.
- Failure symptoms and fixes for prompt audio, empty streams, finalization, KV cache, token boundaries, batch size, server config, downloads, attention kernels, and memory: `references/troubleshooting.md`.
- Safe payload planner with no server/model imports: `scripts/realtime_session_payloads.py`.

## Fast path

1. For Python streaming, read `references/streaming-workflows.md` and choose single-turn, multi-turn, or text-delta bridge.
2. For HTTP service use, read `references/fastapi-service.md`, start the server on the intended GPU, then generate payloads with `scripts/realtime_session_payloads.py`.
3. Before debugging audio quality or latency, check `references/api-reference.md` for the exact session and decoder contracts.
4. If no audio arrives, a request hangs, or speaker identity changes across turns, go directly to `references/troubleshooting.md`.
