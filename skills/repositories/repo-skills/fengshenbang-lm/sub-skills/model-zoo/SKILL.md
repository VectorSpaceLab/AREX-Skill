---
name: model-zoo
description: "Guide selection, import, and compatibility of Fengshen
  model/config/tokenizer families and top-level exports."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Fengshenbang-LM Model Zoo

Use this sub-skill when a task is about choosing, importing, or troubleshooting Fengshen model, config, tokenizer, and generation-helper families. Keep this file as a router; use the bundled references for tables and details.

## Load order

1. Read [references/model-overview.md](references/model-overview.md) to choose the model family and decide whether the package surface, a pipeline surface, or an example/conversion recipe is the right owner.
2. Read [references/api-reference.md](references/api-reference.md) for top-level exports, direct import paths, generation-helper routes, and the `fengshen_model_type` pipeline mapping.
3. Read [references/auto-and-tokenizers.md](references/auto-and-tokenizers.md) before using Fengshen auto factories, custom config keys, `AutoTokenizer`, or tokenizer-specific files.
4. Read [references/compatibility.md](references/compatibility.md) before installing or repairing dependencies, especially Transformers compatibility.
5. Read [references/troubleshooting.md](references/troubleshooting.md) when imports, tokenizers, offline caches, CUDA size limits, or optional DeepSpeed/Megatron paths fail.

## Choose this sub-skill for

- Top-level imports from `fengshen`, especially `LongformerConfig`, `LongformerModel`, `RoFormerConfig`, `RoFormerModel`, `T5Config`, `T5EncoderModel`, `UbertPipelines`, and `UbertModel`.
- Custom model families: Longformer, RoFormer, Megatron-T5, ZEN1/ZEN2, DeBERTa-v2, DeltaLM, LLaMA/Ziya, Taiyi CLIP, Transformer-XL denoise/paraphrase/reasoning, BART, ALBERT, UniMC/UniEX/TCBert/Ubert, and VAE variants.
- Fengshen auto factories (`fengshen.models.auto`), custom model/tokenizer keys (`fengshen_model_type`, `fengshen_tokenizer_type`), and deciding whether direct imports are safer than auto factories.
- Safe installed-package import checks that do not download models or mutate checkpoints: run `python scripts/check_model_imports.py --help` from this sub-skill directory.
- Diagnosing errors such as missing `cached_path`, missing `softmax_backward_data`, absent SentencePiece/tokenizer files, unsupported custom config keys, model downloads in offline mode, model size on CPU, or optional DeepSpeed imports.

## Route elsewhere

- Training loops, dataloaders, metrics, optimizer/scheduler arguments, checkpoints, and distributed/Megatron training go to `../data-training/SKILL.md`.
- Example recipes, model-family command conversion, Ziya conversion, Taiyi diffusion recipes, and checkpoint mutation/conversion planning go to `../examples-conversion/SKILL.md`.
- `fengshen-pipeline` CLI invocation, public pipeline data schemas, and CLI parser behavior go to `../pipelines-cli/SKILL.md`.

## Safety rules

- Do not instantiate `from_pretrained` on remote model IDs unless the task explicitly authorizes downloads and cache use.
- Prefer import-only, config-only, or `local_files_only=True` checks for diagnosis.
- Treat CUDA, DeepSpeed, Megatron fused kernels, Taiyi diffusion, Ziya large-model inference, and full checkpoint conversion as optional/heavy paths unless a separate verification plan requires them.
- Do not depend on the original repository checkout. Use only this skill tree, the installed `fengshen` package, user-provided model directories, and user-authorized caches.
