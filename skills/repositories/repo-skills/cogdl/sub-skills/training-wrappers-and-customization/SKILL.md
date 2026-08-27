---
name: training-wrappers-and-customization
description: "Routes CogDL Trainer, wrapper matching, configuration, and
  checkpoint/logging workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# CogDL Training Wrappers and Customization

Use this sub-skill when the task is about CogDL's unified trainer, model/data
wrappers, default wrapper matching, best-config handling, or checkpoint/logging
behavior.

Typical triggers:
- "Why does CogDL ask for mw and dw?"
- "How do I resume a CogDL checkpoint?"
- "What wrapper does this model use by default?"
- "How does `use_best_config` change the run?"

Read `references/trainer-and-wrappers.md` for the verified `Trainer`
signature, wrapper families, and the default mapping table.
Read `references/configuration-and-best-configs.md` for `BEST_CONFIGS`, the
dataset-specific overrides, and the role of `use_best_config`.
Read `references/troubleshooting.md` when wrapper mismatches, checkpoint
writes, logger selection, or distributed/device issues appear.

Run `scripts/inspect_wrapper_match.py` to print the wrapper pair for one or
more models without launching a run.
Run `scripts/trainer_config_template.py` when you want a reusable config
skeleton for `experiment(...)` and `Trainer(...)` arguments.

Route these elsewhere:
- `../experiments-and-cli/SKILL.md` for `experiment(...)`, CLI flags, and
  AutoML orchestration.
- `../graph-data-and-datasets/SKILL.md` for graph schemas, masks, and custom
  fixture creation.
- `../models-layers-and-operators/SKILL.md` for model and layer code.
- `../pipelines-and-applications/SKILL.md` for `pipeline()` apps.

## What this sub-skill covers

- `Trainer` construction and the major training-mode flags.
- `fetch_model_wrapper`, `fetch_data_wrapper`, `get_wrappers_name`, and the
  default wrapper configuration map.
- Wrapper families such as node classification, graph classification,
  network embedding, heterogeneous tasks, triple link prediction, traffic,
  and pretraining.
- `set_best_config(args)` and the `BEST_CONFIGS` dataset/model overrides.
- Checkpoint, embedding, logging, device, CPU/inference, and distributed
  settings that affect the training loop.

## Decision rules

- Pick the wrapper pair before tuning the model itself.
- If the user only needs to know the right wrapper names, use the inspection
  script instead of explaining the whole trainer.
- If a model is supported but does not have a special wrapper, fall back to
  the default wrapper table or route back to the experiment/CLI sub-skill for
  the exact command.
- Treat checkpoint/resume paths as file-write surfaces and make the location
  explicit.
