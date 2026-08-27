---
name: translation
description: "Operate TLLib image/domain translation and style-transfer
  components: CycleGAN, FDA, CyCADA, and SPGAN."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Translation Sub-skill

Use this sub-skill when a task involves TLLib image/domain translation or style transfer components rather than classifier-only adaptation: CycleGAN generators/discriminators/losses, the `Translation` transform, FDA/Fourier amplitude transfer, CyCADA semantic consistency, or SPGAN Siamese/contrastive components.

## Route first

- Need unsupervised or supervised domain adaptation training after translated images/features exist? Route to [`../domain-adaptation/SKILL.md`](../domain-adaptation/SKILL.md).
- Need image-list formats, dataset roots, segmentation/re-id/detection dataset conventions, transforms, model factories, or metrics? Route to [`../vision-data-models/SKILL.md`](../vision-data-models/SKILL.md).
- Need only component API signatures, tensor shapes, and checkpoint-safe loading? Use [`references/api-reference.md`](references/api-reference.md).
- Need a safe workflow for choosing CycleGAN vs FDA vs CyCADA vs SPGAN? Use [`references/translation-workflows.md`](references/translation-workflows.md).
- Need to debug amplitude caches, PIL/tensor ranges, generator checkpoints, full-training side effects, or GPU/data requirements? Use [`references/troubleshooting.md`](references/troubleshooting.md).

## Safe operating sequence

1. Confirm `tllib` imports successfully in an environment compatible with TLLib 0.4-era PyTorch/TorchVision.
2. Run the bundled component smoke before editing a user workflow:

   ```bash
   python scripts/tllib_translation_smoke.py
   ```

   It uses tiny synthetic tensors/images, creates only temporary files, and does not download data.
3. Choose the smallest translation mechanism:
   - FDA for lightweight target-style amplitude transfer, especially segmentation preprocessing.
   - CycleGAN `Translation` for applying an already trained generator to PIL images or dataset items.
   - CyCADA `SemanticConsistency` when semantic labels/predictions must constrain image translation.
   - SPGAN Siamese/contrastive pieces when preserving person re-id identity similarity matters.
4. Keep benchmark-scale CycleGAN/FDA/SPGAN training as optional, data/GPU-heavy work. Do not imply it was verified by the smoke script.

## What this sub-skill does not claim

- It does not provide dataset download instructions or benchmark reproduction guarantees.
- It does not validate Detectron2/MMCV object-detection stacks, segmentation datasets, re-id datasets, or CUDA training throughput.
- It does not require opening the original repository examples at runtime; the references here are self-contained distilled usage notes.
