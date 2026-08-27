---
name: image-training
description: "Routes Lumina image-model training, finetuning, data preparation,
  resume, and DreamBooth-style adaptation tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Image Training

Use this subskill when the user wants to train, finetune, resume, or prepare data for the Lumina image branches.
It covers the Lumina-T2I, Lumina-Next-T2I, and Lumina-Next-T2I-Mini training entry points and the DreamBooth-style SD3 adaptation path.

## Include here

- Lumina-T2I training from JourneyDB-style image/caption manifests.
- Lumina-Next-T2I training and the mini training route.
- Resume and initialization behavior for checkpoint-based training.
- DreamBooth-style SD3 adaptation in the mini branch.
- Data-cache and local-diffusers/offline preparation for training runs.

## Exclude or route elsewhere

- Pure inference, demo launch, or checkpoint conversion: use `image-generation`.
- Audio/music demos: use `audio-music`.
- Visual anagrams: use `visual-anagrams`.
- ImageNet benchmark training and sampling: use `imagenet-training`.

## Read first

- `references/workflows.md` for the canonical training routes and launch patterns.
- `references/data-formats.md` for JourneyDB manifests and other training data layouts.
- `references/troubleshooting.md` for training-specific backend and resume failures.
- `scripts/check_training_data.py` before launching if the manifest or config is uncertain.

## Fast routing hints

- If the user says `torchrun`, `srun`, `resume`, `cache_data_on_disk`, `JourneyDB`, or `DreamBooth`, use this subskill.
- If the user only needs inference from a checkpoint, stay in `image-generation`.
