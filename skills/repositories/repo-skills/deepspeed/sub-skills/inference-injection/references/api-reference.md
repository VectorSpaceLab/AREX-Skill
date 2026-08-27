# Inference API Reference

## Entry Points

- `deepspeed.init_inference(model, config=None, **kwargs)` returns `deepspeed.InferenceEngine`.
- `config` may be a dictionary or a JSON file path. Keyword arguments are merged into it.
- If a key appears in both `config` and `kwargs`, values must be identical or `init_inference` raises `ValueError("Conflicting argument ...")`.
- `deepspeed.default_inference_config()` returns a default `DeepSpeedInferenceConfig` dictionary.

## Core Config Fields

Current installed facts show `DeepSpeedInferenceConfig` fields:

- `replace_with_kernel_inject`: enable built-in inference kernel replacement; alias `kernel_inject`.
- `dtype`: accepts `torch.float16`, `torch.float32`, `torch.bfloat16`, `torch.int8` and strings such as `fp16`, `float16`, `bf16`, `fp32`, `int8`.
- `tensor_parallel`: `DeepSpeedTPConfig`; alias `tp`; common nested keys are `tp_size`, `tp_grain_size`, `mpu`, and `tp_group`.
- `enable_cuda_graph`, `use_triton`, `triton_autotune`, `zero`, `triangular_masking` alias `tm`, `moe`, `keep_module_on_host`, `quant`.
- Checkpoint fields: `checkpoint`, `base_dir`, `save_mp_checkpoint_path`, `checkpoint_config` alias `ckpt_config`, `training_mp_size`, `set_empty_params`.
- Generation bounds: `max_out_tokens` alias `max_tokens`, `min_out_tokens` alias `min_tokens`.
- Injection fields: `injection_policy` alias `injection_dict`, `injection_policy_tuple`, deprecated `replace_method`.
- Deprecated compatibility fields include `mp_size` (use `tensor_parallel.tp_size`), `mpu` (use `tensor_parallel.mpu`), `ep_size`, `ep_group`, `ep_mp_group`, `moe_experts`, and `moe_type`.

## Injection Modes

`InferenceEngine` chooses one of three replacement paths:

1. Manual tensor-parallel policy: if `injection_policy` is provided, DeepSpeed asserts `replace_with_kernel_inject` is false, validates the target layer names, and applies the policy for each client module class.
2. Kernel injection: if `replace_with_kernel_inject` is true and no manual policy is supplied, DeepSpeed applies built-in policies.
3. AutoTP: if there is no manual policy, no kernel injection, and `tensor_parallel.tp_size > 1`, DeepSpeed asks `AutoTP.tp_parser(model)` to infer policies and then applies injection.

Built-in kernel policy classes are listed in `deepspeed.module_inject.replace_policy.replace_policies` and currently include BERT, GPT-Neo, GPT-NeoX, GPT-J, Megatron GPT, GPT-2, BLOOM, OPT, CLIP, DistilBERT, LLaMA, LLaMA2, and InternLM layer policies. Generic policies include UNet and VAE.

Manual `injection_policy` maps a client module class to a tuple of child module-name suffixes, usually the attention output projection and transformer output projection. Some encoder-decoder blocks need more than two names, such as T5 examples that include self-attention, cross-attention, and MLP output projections.

## Tensor Parallel and Checkpoint Reshaping

- Prefer `tensor_parallel={"tp_size": world_size}` over deprecated top-level `mp_size`.
- If using a custom model-parallel unit, pass it as `tensor_parallel={"mpu": mpu}` rather than top-level `mpu`.
- `training_mp_size` records the MP degree used when the checkpoint was produced. It may differ from inference `tensor_parallel.tp_size` so DeepSpeed can merge or split checkpoint shards during initialization.
- `checkpoint` can be a DeepSpeed-compatible checkpoint path or a JSON load policy. `base_dir` can define the root for checkpoint files. `save_mp_checkpoint_path` can persist a reshaped checkpoint for faster later loading.
- `keep_module_on_host=True` is intended for very large checkpoint loading with injection policies and AutoTP, giving a chance to quantize or reshape before moving tensors to the accelerator.

## Hugging Face TP Plan Conversion

`deepspeed.module_inject.tp_plan_converter.TPPlanConverter` converts Hugging Face `tp_plan` dictionaries into DeepSpeed AutoTP `TPLayerSpec` entries. It supports only `colwise` and `rowwise` partition styles. Unsupported styles such as replicated/local variants return `None` so callers can fall back to preset-based AutoTP.

## Quantization Fields

Current inference config uses `quant`, a `QuantizationConfig` with nested `activation`, `weight`, and `qkv` configs. Base quantization options include `enabled`, `num_bits`, `q_type` (`symmetric` or `asymmetric`), and `q_groups`. Weight quantization also has `quantized_initialization` and `post_init_quant` dictionaries.

Only use inference quantization guidance for `init_inference`. Older docs and examples may mention `quantization_setting`; that name is not a current `DeepSpeedInferenceConfig` field in the installed API facts. Translate intent into `dtype=torch.int8` plus `quant={...}` when targeting the current API.

## v1, v2, FastGen, and Hybrid Engine

- `deepspeed.init_inference` and `DeepSpeedInferenceConfig` are the classic v1 inference entrypoint.
- `deepspeed.inference.v2` contains newer FastGen-oriented internals and policies. The public docs route users looking for best current generation performance to DeepSpeed-FastGen/MII rather than treating v2 internals as a direct `init_inference` drop-in.
- `DeepSpeedHybridEngine` lives under training runtime. It is created by `deepspeed.initialize` when hybrid engine training config is enabled; it is not returned by `init_inference`.
