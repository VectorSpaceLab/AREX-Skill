---
name: text-normalization
description: "Use FunASR text-normalization and punctuation cleanup safely
  without making the optional Pynini stack mandatory."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# FunASR text-normalization

Use this sub-skill when the user asks for FunASR post-ASR text cleanup, punctuation spacing fixes, inverse text normalization (spoken form to written form), or text normalization (written form to spoken form). Keep this layer separate from ASR inference, serving, training/export, and vLLM acceleration.

## Fast route selection

- **Lightweight punctuation cleanup:** use the bundled [`scripts/post_process_punct.py`](scripts/post_process_punct.py) helper when the text already has the right words and you only need spaces around quotes or punctuation to match an original string.
- **Full inverse text normalization (ITN):** use the optional FunTextProcessing ITN path only when spoken ASR text should become written text, such as words for numbers becoming digits or units.
- **Full text normalization (TN):** use the optional FunTextProcessing TN path only when written text should become spoken text, usually for TTS-style preprocessing.
- **Not this sub-skill:** route model choice, transcription, subtitles, hotwords, audio loading, or punctuation-aware ASR models to `python-asr-pipelines`; route HTTP/WebSocket services to `serving-and-runtime`; route export/training to `training-data-and-export`; route Nano/GLM/Qwen3/vLLM acceleration to `llm-asr-and-vllm`.

## Minimum facts to collect

1. Is the user asking for punctuation spacing only, ITN, or TN?
2. If using punctuation alignment, what is the original input text and what is the normalized candidate text?
3. If using full ITN/TN, what language is required and is the optional Pynini-backed stack installed?
4. Where should grammar cache files be written if the full stack is used?

## Operating workflow

1. Prefer the bundled helper for pure punctuation/quote spacing issues because it is standalone and does not need Pynini or tokenizer packages.
2. For punctuation alignment, run:

   ```bash
   python scripts/post_process_punct.py align --input "test' example" --normalized "test 'example"
   ```

   Add `--unicode-punct` when the original text contains Unicode punctuation such as Chinese comma/exclamation marks.
3. If the request needs semantic normalization, read [`references/workflows.md`](references/workflows.md) before using the optional FunTextProcessing route.
4. If full ITN/TN imports or grammar generation fail, read [`references/troubleshooting.md`](references/troubleshooting.md) and run:

   ```bash
   python scripts/post_process_punct.py check-full-stack
   ```

## Safety and boundary notes

- The bundled helper is safe for CPU/any-backend use and does not download models, compile grammars, or mutate environments.
- The full ITN/TN stack is optional and may require Pynini, language-specific grammars, tokenizer/NLP helpers, and a writable cache directory.
- Do not claim Pynini-backed ITN/TN is available until imports and cache creation succeed in the user's runtime.
- Do not tell users to run source-tree scripts directly; use installed package APIs/CLIs where available or the bundled helper in this sub-skill.
