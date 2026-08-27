---
name: training-and-evaluation
description: "Train, finetune, resume, and evaluate CVNets models."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Training and Evaluation

Use this sub-skill when the user wants to train, finetune, resume, or evaluate a CVNets model, including the repo's classification, detection, segmentation, CLIP, ByteFormer, and RangeAugment-flavored training flows.

This sub-skill owns the orchestration path around `main_train.py`, `main_eval.py`, the distributed setup, checkpoint handling, optimizer/scheduler/loss assembly, and the task-specific evaluation branches for detection and segmentation. It does not own model-family selection details, dataset-layout deep dives, or export/profiling commands.

## Read these first

- `../../references/api-reference.md` — verified public entry points and signatures.
- `../../references/configuration.md` — dotted keys, override rules, and common config sections.
- `../../references/model-overview.md` — model-family selection and registry notes.
- `references/workflows.md` — command patterns for train, eval, resume, finetune, and DDP.
- `references/troubleshooting.md` — training-specific failures and recovery steps.
- `scripts/cvnets_train.py` — bundled training wrapper.
- `scripts/cvnets_eval.py` — bundled generic evaluation wrapper.
- `scripts/cvnets_eval_det.py` — bundled detection-evaluation wrapper.
- `scripts/cvnets_eval_seg.py` — bundled segmentation-evaluation wrapper.

## Owns

- Single-node and distributed training runs.
- Resume, auto-resume, and finetuning flows.
- Generic evaluation and task-specific evaluation for detection and segmentation.
- Device setup, DDP launch behavior, batch-size adjustments, EMA, and checkpoint save/load.
- Loss, optimizer, and scheduler creation from a parsed config.

## Excludes

- Choosing which architecture family to use; route to `models-and-architectures`.
- Editing YAML keys, dataset roots, sampler names, tokenizer settings, or modality layouts; route to `data-and-config`.
- CoreML conversion, benchmark throughput, or loss-landscape generation; route to `conversion-and-profiling`.

## Workflow

1. Inspect the config with `scripts/inspect_config.py` if the run depends on a specific YAML file or override.
2. Decide whether the user needs training, evaluation, resume, or finetuning.
3. Run the matching wrapper with `--repo-root <repo-root>` so the checkout is added to `sys.path` and relative config paths resolve against the repo root.
4. For training, make sure `dataset.category`, `model.<category>.name`, `dataset.root_*`, `sampler.name`, and the optimizer/scheduler sections are consistent.
5. For evaluation, confirm the correct specialization: `cvnets_eval.py` for generic runs, `cvnets_eval_det.py` for detection, and `cvnets_eval_seg.py` for segmentation.
6. If the run fails, check the training-specific troubleshooting file before guessing at model or data problems.

## Common signals

- `main_train.py` prints the parsed options and creates an experiment directory under `common.results_loc/common.run_label`.
- `Trainer` owns the epoch/iteration loop and the main training metrics.
- `main_eval.py` routes detection and segmentation through specialized engine helpers because those tasks save outputs differently.
- `common.override-kwargs` is the fast path for one-off overrides such as `dataset.root_val=...` or `model.classification.finetune_pretrained_model=false`.

## When to switch away

- If the user is asking which encoder/head family to pick, switch to `models-and-architectures`.
- If the issue is actually a missing dataset root, a wrong sampler, or a tokenizer/video-reader layout, switch to `data-and-config`.
- If the issue is CoreML, JIT, benchmarking, or loss-landscape generation, switch to `conversion-and-profiling`.
