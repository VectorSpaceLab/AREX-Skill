---
name: training
summary: Work on FastVideo training, fine-tuning, distillation, datasets, and
  trainer tests while preserving the legacy and modular training stacks.
description: "Use when a task touches fastvideo/training, fastvideo/train,
  training examples/scripts, dataset preprocessing, LoRA extraction,
  distillation, attention-QAT training, or training-specific tests."
license: Apache 2.0
metadata:
  disco-role: operating
disable-model-invocation: true
---

# FastVideo Training

## Activate this subskill for

- Fine-tuning, distillation, data preprocessing, dataset format, LoRA extraction,
  or training launch scripts.
- Legacy training code under `fastvideo/training/`.
- Modular training code under `fastvideo/train/`.
- Training examples under `examples/train/`, `examples/training/`, `scripts/train/`,
  `scripts/preprocess/`, `scripts/distill/`, `scripts/lora_extraction/`, or
  `scripts/dataset_preparation/`.
- Training tests under `fastvideo/tests/train/`, `fastvideo/tests/training/`,
  `fastvideo/tests/distributed/`, `fastvideo/tests/dataset/`,
  `fastvideo/tests/encoders/`, `fastvideo/tests/vaes/`, or
  `fastvideo/tests/workflow/`.

## Non-negotiable stack boundary

FastVideo has two training stacks:

- `fastvideo/training/`: legacy, monolithic per-model training and distillation
  pipelines; still authoritative for shipped legacy models.
- `fastvideo/train/`: newer modular framework composed from methods, models,
  callbacks, YAML configs, and launch entrypoints.

Pick the stack that matches the requested file/workflow. Do not migrate behavior
between stacks or consolidate them unless the user explicitly asks for that
migration.

## Read first

- `fastvideo/AGENTS.md`
- `fastvideo/training/AGENTS.md` when editing legacy pipelines
- `fastvideo/train/AGENTS.md` when editing the modular trainer
- `fastvideo/tests/AGENTS.md`
- any nearest `AGENTS.md` under edited script/example directories

Relevant docs:

- `docs/training/overview.md`
- `docs/training/finetune.md`
- `docs/training/data_preprocess.md`
- `docs/training/attn_qat.md`
- `examples/train/README.md`
- `fastvideo/train/README.md`
- `docs/contributing/testing.md`

## Code map

Legacy stack:

- `fastvideo/training/*_training_pipeline.py`
- `fastvideo/training/*_distillation_pipeline.py`
- legacy dataset/model helpers under `fastvideo/training/`

Modular stack:

- `fastvideo/train/entrypoint/`
- `fastvideo/train/methods/`
- `fastvideo/train/models/`
- `fastvideo/train/callbacks/`
- `fastvideo/train/data/`
- YAML/config surfaces referenced by `fastvideo/train/README.md` and examples

Scripts and examples:

- `examples/train/README.md`, `examples/train/run.sh`, `examples/train/run_slurm.sh`
- `examples/training/`
- `scripts/train/`
- `scripts/preprocess/`
- `scripts/distill/`
- `scripts/lora_extraction/`
- `scripts/dataset_preparation/prepare_json_file.py`

## Operating workflow

1. Identify the training stack and model family. If ambiguous, inspect the
   existing example/script the user referenced and choose the matching stack.
2. Read the stack-specific `AGENTS.md` and docs before editing.
3. Identify runtime requirements: GPU count, distributed launcher, dataset path,
   checkpoint path, attention backend, LoRA/adapters, and external credentials.
4. For modular trainer work, preserve method × model × callback composition and
   YAML-driven configuration. Add new behavior at the narrow extension point
   rather than hard-coding it into the entrypoint.
5. For legacy pipeline work, follow nearby model-specific pipeline patterns.
   Avoid broad refactors; legacy code is intentionally monolithic for shipped
   models.
6. For data preprocessing, verify JSON/path schema with small synthetic inputs
   before requiring real datasets.
7. For attention-QAT or backend-specific training, set backend env/config before
   constructing components and record hardware/package assumptions.
8. Avoid launching long training or distributed jobs as a first test. Start with
   import/config/unit tests, then a tiny smoke only if the task requires it.

## Suggested verification ladder

Safe checks:

```bash
python -m pip check
python skills/disco/fastvideo/scripts/verify_fastvideo_runtime.py --cuda
pytest fastvideo/tests/train/methods/test_wan_finetune.py -q
pytest fastvideo/tests/train/ -q
pytest fastvideo/tests/dataset/ -q
```

Choose additional checks by touched area:

```bash
pytest fastvideo/tests/training/ -q
pytest fastvideo/tests/distributed/ -q
pytest fastvideo/tests/encoders/ -q
pytest fastvideo/tests/vaes/ -q
pytest fastvideo/tests/workflow/ -q
```

For examples/scripts, prefer `--help`, config parsing, or a tiny synthetic input
before real training. Read the script first; some shell scripts assume multiple
GPUs, Slurm, model downloads, or environment variables.

Escalate only with explicit budget:

```bash
bash examples/train/run.sh
bash examples/train/run_slurm.sh
# or the exact docs command for the selected model/dataset/backend
```

Before escalation, confirm:

- checkpoint/model path;
- dataset path and size;
- GPU type/count/memory;
- distributed launcher assumptions;
- max runtime and expected success signal;
- output/checkpoint directory and whether overwriting is safe.

## Common pitfalls

- Passing a modular trainer YAML to a legacy script, or vice versa.
- Treating a CPU import as proof that a CUDA/distributed training path works.
- Running Slurm scripts on a non-Slurm host.
- Starting full training without confirming dataset/checkpoint availability.
- Editing generated examples without updating the source docs or config schema.
- Bypassing pre-commit guidance for excluded test paths.

## Handoff checklist

Report:

- selected stack (`fastvideo/training` legacy or `fastvideo/train` modular);
- model/method/dataset/backend involved;
- config files and scripts changed;
- exact tests/smokes run;
- heavy training/distributed tests skipped and why;
- follow-up command to run on the target hardware if not run locally.
