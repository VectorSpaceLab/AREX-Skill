# Local Inference Troubleshooting

## Local inference starts by accident

**Cause:** `OPTILLM_API_KEY` is set.

**Fix:** Unset it when using external providers. Set `OPENAI_API_KEY`, `CEREBRAS_API_KEY`, or `AZURE_*` instead. Use server auth separately through `--optillm-api-key` only when intended.

## HuggingFace authentication errors

**Symptoms:** illegal header value, unauthorized model access, or private model download failures.

**Fix:** Ensure token env vars are either valid non-empty tokens or unset. Blank `HF_TOKEN`, `HUGGING_FACE_HUB_TOKEN`, `HUGGINGFACE_HUB_TOKEN`, and `HF_HUB_TOKEN` values are removed by OptiLLM import cleanup, which means anonymous access is used.

## Model download surprises

Some plugins/decoding paths can load default HuggingFace models. Before running generation:

1. Probe backend with `scripts/check_local_backend.py`.
2. Confirm model ids and adapters are accessible or cached.
3. Ask before large downloads in constrained environments.
4. Set small `max_tokens` for first run.

## CUDA unavailable or broken

- Run `scripts/check_local_backend.py --json`.
- If CUDA is false on a GPU host, check torch wheel, driver, container GPU passthrough, and `CUDA_VISIBLE_DEVICES`.
- If allocation fails, reduce model size/quantization or use CPU.
- If bitsandbytes fails, verify CUDA compatibility or avoid quantized paths.

## MLX/MPS confusion

MLX paths require Apple Silicon/macOS and `mlx-lm`. MPS availability in PyTorch is not the same as MLX support. On Linux, use CUDA or CPU paths instead.

## LoRA adapter problems

- Verify base model and adapter architectures match.
- Use the exact adapter id in `active_adapter`.
- If multiple adapters are appended with `+`, remember the last adapter is active by default.
- PEFT import success does not prove a specific adapter can load.

## Small model rambles to token limit

Some small models do not emit EOS reliably. Set request `max_tokens`/`max_completion_tokens` or environment `OPTILLM_MAX_TOKENS` for smoke tests.

## Logprobs missing

Logprobs are supported by local inference code paths that can access logits. External provider pass-through depends on provider support and should not be assumed.

## DeepConf/AutoThink failures

- DeepConf needs local logits/probability access and can be expensive with many traces.
- AutoThink needs classifier and steering-vector resources plus compatible model internals.
- If either tries to download resources, stop and ask unless downloads were expected.

## Reasoning-token count looks wrong

Reasoning tokens are counted from text inside `<think>...</think>` tags using tokenizer when available or a character estimate fallback. Missing tags produce zero; truncated open tags still count the trailing thinking text.
