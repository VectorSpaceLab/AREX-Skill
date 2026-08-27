---
name: python-asr-pipelines
description: "Default Python ASR route for FunASR: AutoModel, funasr CLI, batch
  transcription, subtitle generation, hotword correction, audio-byte decoding,
  timestamps, punctuation-aware ASR, speaker verification, and common non-LLM
  model selection."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# python-asr-pipelines

Use this sub-skill for everyday local FunASR work: transcribe a file or folder, generate subtitles, choose a first model, inspect `AutoModel` inputs and outputs, handle hotwords, or interpret timestamps and speaker labels.

## Start here

- Python API and return shapes: [references/api-reference.md](references/api-reference.md)
- `funasr` CLI flags and outputs: [references/cli-reference.md](references/cli-reference.md)
- Practical workflows and model choice: [references/workflows.md](references/workflows.md)
- Recovery notes for common failures: [references/troubleshooting.md](references/troubleshooting.md)
- Batch transcription helper: [scripts/batch_transcribe.py](scripts/batch_transcribe.py)
- Subtitle helper: [scripts/generate_subtitles.py](scripts/generate_subtitles.py)

## This sub-skill owns

- `AutoModel` for offline Python ASR
- `funasr` CLI usage
- batch transcription and subtitle generation
- audio bytes and raw PCM decoding
- timestamps, sentence segmentation, and speaker labels
- hotword correction on final text
- non-LLM model selection among common checkpoints such as SenseVoice and Paraformer

## Route elsewhere when needed

- Punctuation cleanup or full ITN/TN: `text-normalization`
- OpenAI API, realtime WS, MCP, browser/client, runtime SDK: `serving-and-runtime`
- Fun-ASR-Nano / GLM-ASR / Qwen3-ASR / `AutoModelVLLM`: `llm-asr-and-vllm`
- Training, manifests, export, and local inference after export: `training-data-and-export`

## Helpful starting points

- CPU-friendly first try: `SenseVoiceSmall`
- Mandarin production with hotwords or timestamps: `Paraformer`
- Speaker-aware meeting transcript: `AutoModel` with `vad_model` and optional `spk_model`
- Import smoke: `import funasr` should work before `AutoModel` is touched, but `AutoModel` itself requires PyTorch

