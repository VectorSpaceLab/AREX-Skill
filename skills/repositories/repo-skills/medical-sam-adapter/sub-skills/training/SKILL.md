---
name: training
description: "Operate CUDA-based train.py adaptation runs for Medical SAM
  Adapter across SAM, EfficientSAM, MobileSAM, Adapter, LoRA, AdaLoRA, 2D, 3D,
  and multi-class configurations."
metadata:
  disco-role: operating
disable-model-invocation: true
license: GPL 3.0
---

# Training

Use this route to construct and diagnose the repository's `train.py`
adaptation workflow. It is a self-contained operating guide, not a copied
launcher: it never downloads weights or data and never requires the source
checkout at runtime.

## Route gate

1. If the question is about dataset names, file layouts, sample dictionaries,
   prompts, tensor shapes, or whether a checkpoint is a base model, start with
   [data preparation](../data-preparation/SKILL.md).
2. Read the [exact parser reference](references/cli-reference.md). In
   particular, inspect the effective values of the `type=bool` options instead
   of trusting their spelling.
3. Select a network/encoder pair from
   [model variants](references/model-variants.md), then run the static helper
   before importing model code. It supports `--help`, `--list`, and an object
   or file supplied through `--json`:

   ```bash
   python scripts/inspect_model_registry.py --net sam --encoder vit_b --mod sam_adpt
   python scripts/inspect_model_registry.py --json '{"net":"mobile_sam","encoder":"tiny_vit","mod":"sam_lora"}' --output json
   ```

4. Check that `-sam_ckpt` is an existing local base-model checkpoint for the
   selected builder. A `-weights` file is a different training-wrapper
   checkpoint; do not substitute one for the other.
5. Confirm a CUDA-capable PyTorch environment, the visible device, data
   contract, output destination, positive `-vis`, and a unique `-exp_name`.
   Use the [workflow patterns](references/workflows.md) without adding any
   download step.

## What the route covers

- Original SAM registry keys are `default`, `vit_b`, `vit_h`, and `vit_l`.
- EfficientSAM keys are `default`, `vit_s`, and `vit_t`.
- The MobileSAM package registry has additional image-encoder and decoder
  entries; only full model-shaped entries are suitable for ordinary
  `train.py` calls. The compatibility warnings are in
  [model variants](references/model-variants.md).
- `sam_adpt`, `sam_lora`, and `sam_adalora` change image-encoder construction
  and/or trainable parameters. Their behavior is network-specific; do not
  assume that an AdaLoRA or LoRA mode creates LoRA layers for every MobileSAM
  entry. See [adapter mechanics](references/adapter-mechanics.md).
- `-thd True` is the source's 3D slice/chunk path. `-chunk` controls the
  training crop/depth path, `-evl_chunk` controls validation windows, and
  `-num_sample`/`-roi_size` affect MONAI sampling. Dataset ownership remains
  with data preparation.
- Original SAM is the only training branch that honors
  `-multimask_output > 1`; EfficientSAM and MobileSAM pass
  `multimask_output=False` in the training loop. Independent scores belong to
  [evaluation](../evaluation/SKILL.md), while detector/box inference belongs
  to [mobile inference](../mobile-inference/SKILL.md).

## Hard execution boundary

The actual training path creates `cuda:<gpu_device>` tensors, initializes CUDA
AMP, and moves the network and data to CUDA. `-gpu False` does not make it CPU
safe. CPU parser/help checks are diagnostics only, not successful training.
`-distributed` is an opt-in `DataParallel` path and still needs all listed
CUDA devices. Do not claim a run succeeded without a real CUDA execution.

## Handoff and shared routing

Preserve the exact command, effective parser values, network/encoder, mode,
checkpoint provenance, data root, device, and output paths in any handoff.
For root-level routing and shared failures, use the
[Medical SAM Adapter root skill](../../SKILL.md) and its shared troubleshooting
when present. For input preparation use
[data preparation](../data-preparation/SKILL.md); for checkpoint scoring use
[evaluation](../evaluation/SKILL.md); for the separate object-aware route use
[mobile inference](../mobile-inference/SKILL.md).

Read the detailed [CLI reference](references/cli-reference.md),
[model variants](references/model-variants.md),
[adapter mechanics](references/adapter-mechanics.md),
[workflow patterns](references/workflows.md), and
[troubleshooting](references/troubleshooting.md) before a long run.
