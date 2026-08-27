---
name: data-preparation
description: "Validate and prepare XTuner SFT, MLLM, pretraining, and RL JSONL
  data, tokenizer/chat-template configuration, caching, packing, and local
  conversion workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# XTuner data-preparation operating skill

Use this sub-skill when the task is about XTuner V1 dataset records, JSONL validation, tokenizer/chat-template selection, dataset caching, packing, or safe local data conversion before training.

## Route here

- Validate OpenAI-style SFT JSONL, including bare message-list lines and object lines with `messages` or `dialogs`.
- Validate multimodal SFT/pretraining JSONL with image/video references, `media_root`, and `class_name="VLMJsonlDataset"`.
- Validate RL/GSM8K-style reward JSONL with `prompt`, `data_source`, and `reward_model.ground_truth`.
- Choose or document `DatasetConfig`, `DataloaderConfig`, `OpenaiTokenizeFunctionConfig`, and `FTDPTokenizeFnConfig` fields.
- Explain dataset cache behavior (`cache_dir`, `cache_tag`) and packing choices (`pack_level`, preset pack/sampler files).
- Convert local GSM8K `question`/`answer` files into XTuner RL JSONL without network access.

## Route elsewhere

- Training launch commands, torchrun resources, FSDP/checkpoint/resume, and training logs belong to the training sub-skill.
- RL trainer, rollout, Ray, judger service, advantage, replay buffer, and inference-backend configuration belong to the reinforcement-learning sub-skill.
- Model family, tokenizer/model path validity, dense/MoE/VLM backend, attention, FP8, or optional accelerator choices belong to the model-backends sub-skill.
- Legacy preprocess CLI usage belongs to the cli-and-tools sub-skill unless only schema context is needed here.

## Start with the safe local helpers

```bash
python ./scripts/validate_xtuner_jsonl.py ./data/openai_sft.jsonl --mode sft
python ./scripts/validate_xtuner_jsonl.py ./data/mllm.jsonl --mode mllm --media-root ./media
python ./scripts/convert_gsm8k_jsonl.py --input-dir ./gsm8k_raw --out-dir ./gsm8k_xtuner
python ./scripts/validate_xtuner_jsonl.py ./gsm8k_xtuner/train.jsonl --mode rl
```

The bundled scripts use only the Python standard library. They do not import XTuner, a tokenizer, PyTorch, image libraries, or any original repository checkout.

## References to load

- [`references/data-formats.md`](references/data-formats.md): SFT, MLLM, pretraining, RL/GSM8K JSONL schemas and config snippets.
- [`references/tokenization-and-packing.md`](references/tokenization-and-packing.md): chat templates, tokenization configs, cache invalidation, and packing/sampler options.
- [`references/troubleshooting.md`](references/troubleshooting.md): failure signatures and fixes for JSONL, media, truncation, cache, preset packing, and RL reward fields.

## Operating rules

1. Validate JSONL before proposing a training launch.
2. For multimodal data, always resolve local image/video references with an explicit `media_root` and fail fast on missing files.
3. Treat the validator's `--max-length` output as an approximation only; real truncation depends on the selected tokenizer and chat template.
4. When `pack_level="preset"`, ensure both `pack_config_path` and `sampler_config_path` are set before handing off to training.
5. For RL data, `reward_model.ground_truth` is required for GSM8K-style rule reward; do not hand off RL data with missing or empty ground truth.
