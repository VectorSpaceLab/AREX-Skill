---
name: training-data
description: "Guide PySOT training setup, dataset preparation, training JSON and
  crop layouts, config preflight, distributed launch, and training failure
  recovery."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PySOT training-data operating sub-skill

Use this sub-skill when the user asks to train PySOT, prepare VID/YouTube-BB/DET/COCO training data, generate `train.json`, build a distributed launch command, debug `TrkDataset` data failures, or validate training config/data paths.

Do **not** treat this as proof that training can run on the current machine. Full PySOT training is a GPU, dataset, and pretrained-backbone workflow; safe checks here are parser/config/data-layout preflights only.

## Fast route

1. Identify the task type:
   - data preparation: read [references/data-preparation.md](references/data-preparation.md);
   - JSON/crop-layout debugging: read [references/data-formats.md](references/data-formats.md);
   - training command construction or resume/pretrain setup: read [references/training-workflow.md](references/training-workflow.md);
   - failures: read [references/troubleshooting.md](references/troubleshooting.md).
2. Collect concrete inputs before giving a runnable command: PySOT checkout root, experiment config path, requested dataset names, prepared crop roots, annotation JSON files, GPU count, pretrained backbone path, resume checkpoint if any, and intended launch directory.
3. Run the bundled safe validator before training:

   ```bash
   python scripts/validate_training_config.py \
     --repo-root <pysot-checkout> \
     --config <experiment-config.yaml> \
     --check-files
   ```

   Omit `--check-files` when only reviewing a config that intentionally points to unavailable external datasets.
4. Only after the validator passes and the user confirms external data/GPU availability, construct the `tools/train.py` distributed command from [references/training-workflow.md](references/training-workflow.md).
5. If the user asks for architecture/model-family explanations, route to the sibling `configuration-models` sub-skill. If the user asks for post-training demo/test, route to `tracking-inference`. If the user asks for metrics or result layouts, route to `evaluation-toolkit`.

## Safety rules

- Do not run dataset crop scripts unless the user explicitly authorizes large downloads and destructive/large side effects.
- Do not run full `tools/train.py` as a default check; it calls CUDA paths and expects distributed environment variables, datasets, and pretrained weights.
- Mention that PySOT's package setup installs the `toolkit` distribution; importing `pysot` normally depends on running from the checkout with `PYTHONPATH`/editable-development style setup.
- Keep user commands parameterized. Avoid assuming dataset paths exist just because defaults appear in `pysot.core.config`.
- If a legacy extension build fails, include the Cython `<3` guidance from [references/troubleshooting.md](references/troubleshooting.md).
