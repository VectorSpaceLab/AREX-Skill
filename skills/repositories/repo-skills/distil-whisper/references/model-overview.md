# Model Overview

## Purpose

Read this when choosing a checkpoint or deciding whether to use short-form, long-form, or speculative decoding.

## Core facts

- Distil-Whisper is English-only. For multilingual speech recognition, the repo points users to Whisper Turbo instead of the distilled checkpoints.
- The main recommendation in the README is `distil-whisper/distil-large-v3`.
- The smaller English checkpoint `distil-small.en` is the memory-friendly choice.
- The older `distil-large-v2` and `distil-medium.en` checkpoints are still useful for compatibility checks and comparison work.

## Practical checkpoint guide

| Checkpoint | Best use | Notes |
| --- | --- | --- |
| `distil-whisper/distil-large-v3` | Default choice for most inference and reproduction tasks | Best balance of speed and accuracy in the repo docs |
| `distil-whisper/distil-small.en` | Low-memory or device-constrained inference | Smallest distilled English checkpoint in the README |
| `distil-whisper/distil-medium.en` | Mid-size comparison runs | Useful when the user wants a smaller model without going all the way to the smallest checkpoint |
| `distil-whisper/distil-large-v2` | Compatibility and legacy comparison | Mentioned in the repo but superseded by `distil-large-v3` for most tasks |
| `openai/whisper-large-v3` | Teacher model / reference baseline | Used in pseudo-labelling, student initialization, and speculative decoding examples |

## Inference modes

- **Short-form transcription**: use the standard Transformers ASR pipeline for audio under 30 seconds.
- **Sequential long-form transcription**: use the sliding-window / sequential approach when accuracy matters more than latency.
- **Chunked long-form transcription**: use chunking when a single long file needs lower-latency throughput.
- **Speculative decoding**: use Distil-Whisper as the assistant model for Whisper when matching teacher outputs matters.

## Library compatibility notes

The README notes compatibility with:

- Hugging Face Transformers
- OpenAI Whisper
- whisper.cpp
- Transformers.js
- Candle

For direct user tasks, prefer the sub-skills and keep the export-compatibility notes as background context.
