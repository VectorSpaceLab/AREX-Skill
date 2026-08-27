---
name: llama-cpp-backend
description: "Operate the torch-free and low-memory MOSS-TTS-Delay llama.cpp backend."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# llama-cpp-backend

Use this sub-skill when the task is to run, configure, validate, convert weights for, or debug the MOSS-TTS-Delay llama.cpp bridge backend. This backend replaces the full Torch/Hugging Face generation stack with a GGUF Qwen3 backbone, NumPy embeddings/LM heads, delay-pattern sampling, and ONNX Runtime or TensorRT audio tokenizer decoding.

## Scope

This sub-skill owns:

- Torch-free and torch-optional install profiles for the llama.cpp backend.
- Required GGUF, embedding, LM-head, tokenizer, ONNX, and TensorRT-engine file layout.
- The `PipelineConfig` YAML contract and safe config inspection before model loading.
- C bridge build requirements for `libbackbone_bridge.so`.
- CLI and Python API generation paths for text-to-speech and reference-audio voice cloning.
- ONNX, TensorRT, and Torch audio-tokenizer backend selection.
- `heads_backend` selection for NumPy versus optional Torch LM heads.
- Low-memory and 8 GB GPU tradeoffs.
- Weight extraction/conversion from a full MOSS-TTS-Delay checkpoint into backbone, embeddings, LM heads, and GGUF artifacts.
- Batch-evaluation layout and result interpretation for Seed-TTS/CV3-style suites.

## Route elsewhere

- For full Torch/Hugging Face MOSS-TTS family generation, use `../hf-family-workflows/SKILL.md`.
- For training, fine-tuning, or dataset preparation, use `../finetuning-data-prep/SKILL.md`.
- For realtime voice-agent workflows, use `../realtime-voice-agent/SKILL.md`.

## Fast operating path

1. Choose an install profile and backend mix from `references/build-and-configure.md`.
2. Place weights in the expected layout or adapt a YAML config to your chosen paths.
3. Build the C bridge so `libbackbone_bridge.so` is discoverable by the installed `moss_tts_delay.llama_cpp` package.
4. Inspect the YAML without loading models:

   ```bash
   python <this-skill>/scripts/inspect_llama_cpp_config.py <config.yaml>
   python <this-skill>/scripts/inspect_llama_cpp_config.py <config.yaml> --json
   ```

5. Run one CLI smoke generation with a short sentence and `--profile` only after the config inspector reports the required path fields are present.
6. For production runs, pin `audio_backend`, `heads_backend`, `n_gpu_layers`, `low_memory`, KV-cache type, and sampling values explicitly in the YAML or CLI overrides.

## Reference map

- `references/build-and-configure.md` — installs, weight layout, C bridge build, YAML profiles, and low-memory settings.
- `references/api-and-cli.md` — CLI flags, Python API, config field meanings, backend behavior, and generation caveats.
- `references/weight-conversion.md` — converting a full MOSS-TTS-Delay checkpoint into llama.cpp-ready artifacts.
- `references/evaluation.md` — batch-eval input/output layout, tasks, summaries, and quantization-quality context.
- `references/troubleshooting.md` — missing bridge/weights, ONNX/TRT/Torch backend failures, CUDA limits, downloads, and evaluation-layout failures.
- `scripts/inspect_llama_cpp_config.py` — safe YAML/path checker that does not import model code or download weights.
