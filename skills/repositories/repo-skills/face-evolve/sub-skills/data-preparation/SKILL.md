---
name: data-preparation
description: "Prepare and validate face.evoLVe identity-folder datasets,
  low-shot balancing, augmentation notes, and validation bcolz layouts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# data-preparation

Use this sub-skill when the request is about preparing or checking face.evoLVe
training data in identity folders, pruning low-shot classes safely, or
understanding validation pair files and public dataset/model-zoo artifacts.

## Use this sub-skill for

- ImageFolder-style identity folders for PyTorch training.
- PaddlePaddle `NormalDataset` / balancing datasets that read identity folders
  directly.
- Hidden-file cleanup and class-count validation.
- Low-shot removal with a dry-run first.
- RandAugment-style augmentation notes.
- Validation `bcolz` carray folders plus matching `_list.npy` files.
- Public data/model-zoo naming, downloads, and licensing cautions.

## Route elsewhere when needed

- Need MTCNN detection, landmarks, alignment, or resize preprocessing ->
  `face-alignment`.
- Need PyTorch config editing, model construction, or training loops ->
  `pytorch-training`.
- Need checkpoint feature extraction or verification metrics ->
  `feature-extraction-verification`.
- Need PaddlePaddle training, quantization, or deployment -> `paddle-workflows`.

## Read or run

- Read `references/data-preparation.md` for folder rules, low-shot handling,
  augmentation notes, and validation-pair layout.
- Read `references/data-and-model-zoo.md` before choosing a public dataset or
  model artifact.
- Read `references/troubleshooting.md` when class folders, hidden files,
  `bcolz`, or downloads fail.
- Run `scripts/check_image_folder.py` to validate a tiny fixture or a real
  identity-folder root before training or pruning.
- Run `scripts/remove_lowshot_safe.py` to report or prune classes below a
  threshold without mutating the source tree by default.

## Typical decisions

- Validate first, prune second, and re-validate after any change.
- Prefer weighted sampling in training when the user wants imbalance handling
  without deleting identities.
- Treat validation pair files as a separate artifact family from ImageFolder
  training data.
- Treat public downloads as external, optional artifacts, not bundled files.

## Guardrails

- Keep the dataset root flat at the identity-folder level; do not mix in
  alignment or checkpoint logic here.
- Remove or report hidden files such as `.DS_Store` before pruning or training.
- Count only real image files when deciding whether a class is low-shot.
- Do not assume the repo checkout includes large datasets, pair archives, or
  model weights.
