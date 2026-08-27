---
name: "experiments"
description: "Routes PFLlib federated-learning runs, CLI tuning, privacy
  evaluation, GPU smoke checks, and result summarization."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Experiments

Use this route when you want to launch, tune, or summarize a PFLlib federated
learning run.

## Use this when

- You need to run FedAvg, FedProx, FedPAC, FedCP, GPFL, FedDBE, or any other
  built-in algorithm on a prepared dataset split.
- You need to pick a model for a dataset family, adjust rounds or client ratios,
  or switch between CPU and CUDA execution.
- You need privacy evaluation (`-dlg` / DLG) or system-condition knobs such as
  client dropout, slow trainers, slow senders, or network TTL.
- You need to understand where results and model checkpoints are written.
- You want to summarize a run from an `.h5` result file or a `.out` log.

## Read these references

- `references/cli-reference.md` for the main launch flags and the common option
  groups.
- `references/model-overview.md` for dataset-to-model compatibility.
- `references/results-and-logs.md` for saved outputs and summary formats.
- `references/workflows.md` for quickstart, privacy, and text-task recipes.
- `references/troubleshooting.md` for CUDA, cvxpy, layout, and log-path issues.

## Run these helpers

- `scripts/run_experiment.py` to launch `system/main.py` from a checkout without
  hard-coding the source path.
- `scripts/summarize_results.py` to read h5 or text-log outputs and print best
  accuracy summaries.
- `scripts/check_install.py` from the root route before the first run or after
  any dependency change.
- `scripts/scan_registry.py` from the root route when you need to inspect the
  supported dataset, model, and algorithm registry.

## What belongs here

Include existing experiment workflows, evaluation settings, and result-reading
workflows:

- dataset + model + algorithm selection
- CUDA / CPU execution choice
- multi-GPU selection via `-did`
- privacy evaluation and DLG settings
- client dropout, slow trainer, slow sender, and TTL settings
- checkpoint and h5 result inspection
- log summarization and run comparison

## What does not belong here

- Creating or validating the dataset splits themselves; route that to
  `data-preparation`.
- Adding a new algorithm, model, or dataset; route that to `extension`.
- Host install / package resolution failures before PyTorch imports work; read
  the root troubleshooting and check-install helper first.

## Common workflow

1. Confirm that the dataset split exists and matches the intended scenario.
2. Confirm the runtime stack with the install checker.
3. Launch the experiment through the bundled wrapper.
4. Summarize the output with the bundled result helper.
5. Move to extension guidance only if you need to add new code paths.
