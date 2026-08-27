---
name: inference-injection
description: "Use DeepSpeed inference initialization, kernel/manual module
  injection, tensor-parallel inference, checkpoint reshaping, and inference
  quantization."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DeepSpeed Inference Injection

Use this sub-skill when the task involves `deepspeed.init_inference`, `DeepSpeedInferenceConfig`, `InferenceEngine`, inference kernel injection, manual `injection_policy`, AutoTP inference tensor parallelism, checkpoint MP reshaping, or inference quantization.

## Route Here For

- Choosing between `replace_with_kernel_inject=True`, manual `injection_policy`, and AutoTP when `tensor_parallel.tp_size > 1`.
- Building or debugging `DeepSpeedInferenceConfig` dictionaries, including aliases like `kernel_inject`, `tp`, `tm`, `ckpt_config`, `max_tokens`, and `min_tokens`.
- Loading inference checkpoints while changing model-parallel degree with `training_mp_size`, `tensor_parallel.tp_size`, `checkpoint`, and `save_mp_checkpoint_path`.
- Reasoning about inference-only quantization fields (`dtype=torch.int8`, `quant`) and older docs that mention `quantization_setting`.
- Distinguishing classic v1 `init_inference` from v2/FastGen surfaces and from training-time hybrid engine.

## Start With

1. Inspect the installed API before advising on aliases or optional modules:
   `python scripts/inspect_inference_config.py --check-modules`
2. Use `references/api-reference.md` for current fields, aliases, and injection modes.
3. Use `references/workflows.md` for configuration patterns and decision points.
4. Use `references/troubleshooting.md` when errors involve config merge conflicts, unsupported injection, TP/CUDA graph, missing optional packages, or v1/v2 confusion.

## Boundaries

- For training config, ZeRO training, schedulers, and optimizers, use the training/config sub-skill instead.
- For MoE training, expert parallelism training, or sequence parallelism, use the parallelism/MoE sub-skill.
- For build failures, CUDA op compilation, Triton installation, or kernel diagnostics, use the ops/tooling sub-skill.
- Treat `DeepSpeedHybridEngine` as `deepspeed.initialize(..., enable_hybrid_engine=True)` training runtime support, not as a replacement for `deepspeed.init_inference`.
