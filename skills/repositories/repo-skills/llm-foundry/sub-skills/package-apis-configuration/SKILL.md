---
name: package-apis-configuration
description: "Inspect and use LLM Foundry package APIs, registries, MPT/HF model
  classes, tokenizers, callbacks, optimizers, metrics, loggers, config
  transforms, optional backends, and MCLI adaptation patterns."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Package APIs and Configuration

Use this sub-skill when the task is about LLM Foundry's installed Python package surface: package import health, registry entries, custom registry extensions, MPT/Hugging Face model constructors, tokenizers, callbacks, optimizers, schedulers, metrics, loggers, configuration transforms, optional dependency gates, or MosaicML platform YAML adaptation.

Start here:

- Use [references/api-reference.md](references/api-reference.md) for package identity, installed registry entries, public signatures, and builder contracts.
- Use [references/model-configuration.md](references/model-configuration.md) for MPTConfig, MPTForCausalLM, ComposerMPTCausalLM, ComposerHFCausalLM, and ComposerHFT5 configuration rules.
- Use [references/registry-and-extension.md](references/registry-and-extension.md) for `llmfoundry registry`, Python entry points, `code_paths`, `import_file`, and `construct_from_registry` patterns.
- Use [references/mcli-platform.md](references/mcli-platform.md) for adapting LLM Foundry YAMLs to MosaicML platform/MCLI jobs.
- Use [references/troubleshooting.md](references/troubleshooting.md) when imports, registry construction, optional packages, CUDA-only components, credentials, or HF remote-code loads fail.
- Run [scripts/llmfoundry_api_probe.py](scripts/llmfoundry_api_probe.py) before deeper package work to print package version, registry entries, a tiny MPTConfig check, CUDA availability, and optional dependency status without downloads or training.

Operating rules:

1. Prefer registry and signature inspection before instantiating models. `build_tokenizer` and Hugging Face model wrappers can download remote assets; do not call them unless the task explicitly allows network/model access.
2. For CPU-only or quick API checks, override MPT attention to `attn_impl: torch` and ComposerMPT loss to `loss_fn: torch_crossentropy`; defaults favor GPU/flash-attention paths.
3. Treat registry names as exact keys. If a key is unknown, first confirm the package import completed, then check `llmfoundry registry get <group>` or direct `registry.<group>.get_all()`.
4. For custom code, prefer a bounded `code_paths` import file for one run and Python entry points for reusable packages. The imported code must register into the appropriate `llmfoundry.registry` object before builders run.
5. Preserve constructor keyword boundaries: remove `name` before passing kwargs to constructors, do not pass optimizer `params` through YAML, and only pass callback `train_config` through `build_callback`'s `train_config` argument.
6. Route full data preparation, training, evaluation, generation, and checkpoint conversion workflows to their owning sub-skills. This sub-skill only covers package APIs/configuration and platform adaptation surfaces.
7. Exclude maintenance-only CI, lint, release, and packaging-policy tasks unless they directly affect runtime package import or registry behavior.
