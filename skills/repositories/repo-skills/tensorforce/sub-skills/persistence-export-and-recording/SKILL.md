---
name: persistence-export-and-recording
description: "Save, load, checkpoint, summarize, record, pretrain, track, and
  export Tensorforce agents and models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Persistence, Export, and Recording

Use this sub-skill when the task involves Tensorforce checkpoints, NumPy/HDF5 weight saves, `Agent.load`, `Agent.save`, `saver`, `summarizer`, tracked tensors, recorder/pretraining, `Runner.save_best_agent`, or TensorFlow SavedModel export.

## Route by task

- Read [save/load/export](references/save-load-export.md) for checkpoint, NumPy/HDF5, SavedModel, and load patterns.
- Read [recording and pretraining](references/recording-and-pretraining.md) for recorder traces, `Agent.pretrain`, and tracking/summaries.
- Run [scripts/save_load_smoke.py](scripts/save_load_smoke.py) to verify a small save/load cycle.
- Run [scripts/export_saved_model_smoke.py](scripts/export_saved_model_smoke.py) only when TensorFlow SavedModel export is needed.
- Use [troubleshooting](references/troubleshooting.md) for ambiguous formats, changed environment spaces, HDF5/TensorFlow issues, or SavedModel misuse.

## Boundaries

This sub-skill assumes an agent/environment workflow already exists. Use [agents-and-specifications](../agents-and-specifications/SKILL.md) for `Agent.create` arguments and [runner-and-cli-workflows](../runner-and-cli-workflows/SKILL.md) for training/evaluation loops before persistence. Use this sub-skill once the question is about keeping, restoring, inspecting, recording, or exporting agent state.
