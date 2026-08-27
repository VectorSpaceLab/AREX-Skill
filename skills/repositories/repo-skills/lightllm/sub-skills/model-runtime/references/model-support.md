# Model support and runtime selection

## Registry behavior

The model registry in `lightllm.models.registry` maps a `model_type` to one or
more model classes. A registry entry may also carry:

- `is_multimodal`: marks model families that need multimodal routing.
- `condition`: a callable that decides whether the class should be selected
  for a specific config.

The operational question is not just “is the package importable?” but “does the
model config select a registry entry that can run on the chosen backend and
hardware?”

## Model-family buckets

This repository organizes model code into family directories such as:

- text LLM families,
- vision-language families,
- image / vision transformer support,
- audio / speech support,
- reward-model or RL-related paths.

Representative model directories observed in the installed package include:
`bloom`, `deepseek2`, `deepseek3_2`, `deepseek_mtp`, `gemma3`, `gemma4`,
`gpt_oss`, `internlm`, `internlm2`, `internvl`, `llama`, `llava`, `mistral`,
`mixtral`, `phi3`, `qwen`, `qwen2`, `qwen2_5_vl`, `qwen2_reward`, `qwen2_vl`,
`qwen3`, `qwen3_5`, `qwen3_5_moe`, `qwen3_5_mtp`, `qwen3_moe`, `qwen3_mtp`,
`qwen3_omni_moe_thinker`, `qwen3_vl`, `qwen3_vl_moe`, `qwen3next`,
`qwen_vl`, `stablelm`, `starcoder`, `starcoder2`, `tarsier2`, `vit`, and
`whisper`.

The exact roster changes over time, so use the bundled model-roster helper and
this reference together rather than hardcoding a stale list.

## Runtime flags that affect model support

| Flag family | Why it matters |
| --- | --- |
| `--model_dir`, `--model_name`, `--model_owner` | Choose the concrete checkpoint and display metadata. |
| `--tokenizer_mode`, `--load_way` | Affect tokenizer loading and weight-loading strategy. |
| `--trust_remote_code` | Needed for some Hugging Face model repos. |
| `--enable_multimodal`, `--disable_vision`, `--disable_audio` | Control multimodal routing and sub-modality activation. |
| `--use_reward_model`, `--enable_rl` | Switch into reward / RL serving modes. |
| `--quant_type`, `--quant_cfg`, `--vit_quant_type`, `--vit_quant_cfg` | Select quantized runtime variants. |
| `--llm_prefill_att_backend`, `--llm_decode_att_backend`, `--vit_att_backend` | Select attention kernels or fallback paths. |
| `--llm_kv_type`, `--llm_kv_quant_group_size` | Configure KV-cache format and quantization grouping. |
| `--hardware_platform` | Declare the backend family expected by the runtime. |
| `--enable_torch_fallback`, `--enable_triton_fallback` | Control fallback behavior when an optimized kernel is unavailable. |

## Backend compatibility notes

- Treat a successful Python import as an install check, not as proof that a
  CUDA/ROCm/MPS backend works for the model.
- Use backend validation results to separate “installed” from “supported on this
  host”.
- Optional kernel packages can improve performance without being required for
  every workflow.
- If the repo logs a kernel warning but the selected route does not depend on
  that backend, record it as an optional gap rather than a hard failure.

## Adding a new model

The source docs and code imply this operational checklist:

1. Create or update the model-family directory under `lightllm/models/`.
2. Register the class in `lightllm.models.registry` with the right condition.
3. Add any modality-specific helpers or hooks.
4. Make sure the CLI / runtime flags expose the needed backend or modality
   controls.
5. Update the docs and a representative regression or smoke case.

## Useful sources

- `lightllm/models/registry.py`
- `lightllm/utils/backend_validator.py`
- `lightllm/server/core/objs/start_args_type.py`
- `docs/EN/source/models/supported_models.rst`
- `docs/EN/source/models/add_new_model.md`
- `docs/EN/source/tutorial/fp8_kv_quantization.rst`
- `docs/EN/source/tutorial/reward_model.rst`
- `docs/EN/source/tutorial/multimodal.rst`

## How to use this reference

When answering a model-support question, identify:

- the model family,
- the modality,
- the required backend,
- the expected quantization or fallback,
- and whether the question is about existing support or new support.

Then route to the deployment or serving sub-skill only after the model-runtime
compatibility story is clear.
