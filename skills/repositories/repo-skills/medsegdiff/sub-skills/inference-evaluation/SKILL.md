---
name: inference-evaluation
description: "Operate MedSegDiff checkpoint inference and image-based
  segmentation evaluation for ISIC, BRATS, and bounded custom-data workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Inference and evaluation

Use this sub-skill when a prepared MedSegDiff runtime must sample masks from a
compatible checkpoint or score already-written prediction images. Keep the
sampling and scoring decisions separate:

1. Use [`references/workflows.md`](references/workflows.md) to inspect the
   sampler flags, effective input channels, version and solver behavior,
   dataset branch contracts, checkpoint compatibility, ensemble aggregation,
   and output names.
2. Use [`references/metrics-and-output.md`](references/metrics-and-output.md)
   before interpreting ISIC IoU/Dice or per-class results. Its filename and
   threshold rules deliberately document brittle source behavior.
3. Run [`scripts/inspect_sample_cli.py`](scripts/inspect_sample_cli.py) for a
   no-GPU parser/default/effective-plan check. It does not import the project,
   open a checkpoint, or touch data.
4. Run [`scripts/evaluate_isic.py`](scripts/evaluate_isic.py) for deterministic
   ISIC-style ensemble-image scoring, or
   [`scripts/evaluate_per_class.py`](scripts/evaluate_per_class.py) for a
   bounded binary two-class report. These scripts are self-contained and do
   not import the original repository.
5. Only perform real diffusion sampling in an explicitly prepared runtime
   with a compatible CUDA device, trained checkpoint, dataset, and approved
   output directory. Parser checks and image evaluators do not prove that
   sampling works.

Do not use this sub-skill for the training loop or primary dataset preparation.
Do not treat the repository's original sampling/evaluation scripts as safe
CPU smoke tests; the known failure modes and required patches are recorded in
[`references/troubleshooting.md`](references/troubleshooting.md).
