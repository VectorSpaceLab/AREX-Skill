# Cross-cutting troubleshooting

## Import fails or warns about version mismatch

Symptoms:

- `ModuleNotFoundError: No module named 'vllm'` or optional media package imports fail.
- Import logs a major/minor mismatch between vLLM and vLLM-Omni.
- `vllm serve` does not recognize `--omni` or Omni-specific flags.

Recovery:

1. Use a fresh environment and install an upstream vLLM version aligned with the vLLM-Omni release line.
2. Verify metadata with `python scripts/check_environment.py --require-vllm 0.26`.
3. Import `vllm_omni` before expecting Omni model registration side effects in worker subprocesses.
4. If working from a source checkout, remember that a dev SCM version may not look like the release line even when the code imports.

## Wrong dependency variant installed

Symptoms:

- CPU-only Torch is installed on a GPU host.
- CUDA libraries import but `torch.cuda.is_available()` is false.
- ROCm/NPU/XPU/MUSA packages conflict with CUDA packages.

Recovery:

1. Create a new environment rather than repairing a mixed one.
2. Set `VLLM_OMNI_TARGET_DEVICE` explicitly during vLLM-Omni installation.
3. Install the matching upstream vLLM backend build before installing vLLM-Omni.
4. Run the root environment checker with `--require-cuda` only when CUDA is truly required.

## Model download, cache, or license blocks execution

Symptoms:

- Hugging Face gated repository errors.
- Model repository not found.
- Long startup with no GPU work because weights are still downloading.
- Offline scripts fail on remote model names in an air-gapped environment.

Recovery:

1. Confirm the exact model id, revision, and access terms outside the serving run.
2. Prefer a local checkpoint path when the user has already staged weights.
3. Avoid running full examples in verification unless cache/network/license status is explicit.
4. Keep skill-generated helpers as no-network scaffolds until runtime prerequisites are known.

## Server starts but request fields are ignored

Symptoms:

- Logs mention ignored fields such as `height`, `width`, or `num_inference_steps`.
- Diffusion output uses defaults even though request parameters were intended.

Recovery:

1. For OpenAI SDK calls, pass diffusion fields through the SDK's `extra_body=` keyword.
2. For raw JSON/curl/requests, send an `"extra_body"` object in the request body.
3. Confirm the selected endpoint supports the fields. Image/edit/video/speech endpoints may expose some fields directly; chat completions is stricter.
4. Use the online-serving payload builder to generate a no-network example.

## Out of memory or bad stage placement

Symptoms:

- CUDA OOM during initialization or first request.
- Stage 0 starts but headless worker never becomes usable.
- Streaming has high first-packet latency or queue buildup.

Recovery:

1. Reduce `gpu_memory_utilization`, `max_num_seqs`, or `max_num_batched_tokens` on the affected stage.
2. Use stage-configuration helpers to validate YAML and estimate placement.
3. Keep head/headless `--omni-master-address` and `--omni-master-port` consistent.
4. Use `--stage-id` and `--headless` only in the stage-based launch paradigm.
5. For diffusion, consider VAE slicing/tiling, CPU/layerwise offload, HSDP, or lower resolution only when the model supports them.

## Optional feature dependency missing

Symptoms:

- Forced aligner, custom voice, IndexTTS, LongCat, SoulX, Blackwell FA4/quack, or demo client imports fail.
- A model-specific adapter errors before model load.

Recovery:

1. Identify the model family and feature, then install only the matching optional extra or package.
2. Do not install all optional extras into a production serving environment.
3. Keep optional imports lazy and report user-actionable install instructions when editing adapters.
4. Use model-integration's static checker before running full TTS/audio models.

## Native examples/tests are skipped

This skill treats original repo examples and tests as evidence, not runtime dependencies. A skip is not a pass. Run native model examples only when the user confirms:

- compatible hardware/backend;
- model weights and license access;
- runtime budget;
- output artifacts are safe to write;
- no external credentials or services are required.
