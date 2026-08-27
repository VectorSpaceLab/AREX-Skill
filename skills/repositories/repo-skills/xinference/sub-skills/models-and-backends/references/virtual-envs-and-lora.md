# Virtual Environments and LoRA

## Virtual environments

- Enable them globally with `XINFERENCE_ENABLE_VIRTUAL_ENV=1` and disable them globally with `0`.
- Per-model launch flags override the global setting.
- `virtualenv.packages` is a list of pip requirement strings or marker placeholders.
- Engine markers use `#engine#` or `#model_engine#` comparisons and are case-sensitive in the source payload.
- Common placeholders include `#transformers_dependencies#`, `#vllm_dependencies#`, `#sglang_dependencies#`, `#llama_cpp_dependencies#`, `#mlx_dependencies#`, `#diffusers_dependencies#`, `#sentence_transformers_dependencies#`, and `#system_numpy#`.
- Markers can advertise engines during discovery, but they do not create a GPU, an MPS device, or a Linux kernel.
- If a vLLM or SGLang launch inside a virtualenv hits cuDNN-related import errors, make the matching CUDA libraries visible before relaunching.

## Model-hub JSON guidance

- Put engine-aware markers in the `virtualenv` block when a single model JSON should cover multiple engines.
- Keep the package list explicit enough that engine discovery can tell which backends are intended.
- Do not hard-code transient package cache paths into the model JSON.

## LoRA

- LLM and image models support attached LoRA models.
- For LLMs, register the LoRA path at launch and choose the adapter later by `generate_config["lora_name"]`.
- For image models, use the image-specific LoRA load and fuse kwargs plus the adapter list.
- A LoRA that changes prompt style is a poor fit for chat models.
- The base model and its LoRA share the same device memory budget.

## Practical check

If a model only works after you toggle virtualenv, that usually means the package set was missing, not that the backend is universally supported. Confirm the OS and hardware gates separately.
