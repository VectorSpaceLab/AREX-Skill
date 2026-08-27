---
name: training-and-generation
description: "Inspect and operate OpenPrompt training, evaluation, generation,
  runner selection, device placement, checkpointing, few-shot, zero-shot,
  LM-BFF, and ProtoVerb workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Training and Generation

Use this sub-skill when the task asks how to run, inspect, resume, test, or debug OpenPrompt training/generation jobs after the dataset, template, verbalizer, and package environment choices are known.

Start here:

- Use [references/api-reference.md](references/api-reference.md) for runner APIs, device placement, config keys, checkpoint/logging semantics, and generation contracts.
- Use [references/workflows.md](references/workflows.md) for safe dry-runs, classification, generation, LM-BFF, ProtoVerb, few-shot, zero-shot, resume, and test recipes.
- Use [references/troubleshooting.md](references/troubleshooting.md) when CUDA, model cache, dataset, checkpoint, generation length, teacher-forcing, few-shot sampling, LM-BFF, or ProtoVerb behavior fails.
- Use [scripts/inspect_training_config.py](scripts/inspect_training_config.py) to summarize a YAML config without loading models, loading datasets, or starting training.

Operating rules:

1. Dry-run first. Inspect `experiments/*.yaml` with `scripts/inspect_training_config.py` before running `experiments/cli.py` or a tutorial script.
2. Runner selection follows `experiments/cli.py`: classification with `classification.auto_t` or `classification.auto_v` uses `LMBFFClassificationRunner`; classification with `verbalizer: proto_verbalizer` uses `ProtoVerbClassificationRunner`; other classification uses `ClassificationRunner`; `task: generation` uses `GenerationRunner`.
3. Treat `environment.num_gpus > 0` as a real CUDA request. OpenPrompt calls `model.cuda()` or wraps `DataParallel`; it does not automatically fall back to CPU when CUDA is unavailable.
4. `BaseRunner` writes TensorBoard and checkpoints under `config.logging.path` unless `train.clean: True`. The code writes `checkpoints/last.ckpt` and copies to `best.ckpt` on improved validation; the declared `checkpoint.save_latest` and `checkpoint.save_best` flags are not enforced by `BaseRunner`.
5. Generation training requires batches with `tgt_text` and correct `teacher_forcing`/`predict_eos_token` behavior. For evaluation/generation, pass generation kwargs deliberately; `generation.max_length` includes prompt/input tokens in the native generation API.
6. Few-shot and zero-shot behavior is owned by `experiments/cli.py`: few-shot loops over `sampling_from_train.seed`; zero-shot calls `runner.test()` without fitting.
7. Route dataset layout/config merging details to `../data-and-config-workflows/`, prompt grammar/verbalizer design to `../template-verbalizer-design/`, and top-level import/loading quickstarts to `../pipeline-basics/`.
8. Large-model CUDA, UltraChat/`accelerate`, and PaddlePaddle tutorial variants are optional workflows. The minimum verified scope is CPU package/config/API inspection, not GPU training throughput or benchmark reproduction.
