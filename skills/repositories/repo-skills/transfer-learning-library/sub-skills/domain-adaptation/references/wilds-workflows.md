# WILDS Workflows

This reference covers the WILDS-flavored domain-adaptation recipes that reuse the same TLLib loss families but sit on top of WILDS-specific dataset and training infrastructure.
It is reference-only guidance: do not treat these recipes as CPU-smoke coverage.

## Common stack

Depending on the modality, the WILDS examples may need:

- `wilds`,
- `apex` for AMP / distributed training patterns,
- `timm` for image backbones,
- `transformers` for text,
- `torch_sparse` and related graph tooling for the molecule branch,
- `tensorboard` for logging/inspection.

Use those as optional-stack notes unless the user explicitly has them installed.

## Image-classification WILDS

This branch covers fmow, iwildcam, camelyon17, DomainNet, and similar image classification tasks.

### The usual command shape

A typical recipe description should mention:

- a dataset root directory,
- `-d/--data` for the WILDS dataset name,
- `--unlabeled-list` and `--test-list`,
- `--metric` for the evaluation metric,
- image-size, crop, interpolation, flip, and augmentation flags,
- `--arch`, `--no-pool`, `--scratch`, `--smoothing`, `--bottleneck-dim`, `--trade-off`,
- optimization flags such as `--lr`, `--momentum`, `--weight-decay`, `--min-lr`, `--epochs`, `--batch-size`,
- training flags such as `--deterministic`, `--seed`, `--sync-bn`, `--opt-level`, `--keep-batchnorm-fp32`, `--loss-scale`, `--channels-last`, and `--phase`.

### Methods that show up here

- ERM
- DANN
- DAN
- JAN
- CDAN
- MDD
- FixMatch

The important point is that the WILDS wrapper changes the dataset and training infrastructure, not the underlying DA loss family.

## Text classification WILDS

This branch is the CivilComments / Amazon style setup.

### Tell users to expect

- token-length and text-preprocessing flags,
- group-by-field flags,
- an evaluation metric such as worst-group accuracy,
- a stronger dependency on transformer-style tooling than the image branch.

### Keep the description high level

The exact data-loading and tokenizer details are modality-specific and should stay in the workflow reference instead of the router.

## Poverty regression WILDS

This branch handles the image regression setting around PovertyMap.

### Tell users to expect

- the official split scheme,
- fold selection,
- a multispectral or regression-aware backbone,
- multi-value batch size arguments,
- AMP / distributed-training flags similar to the image-classification branch.

## Molecule classification WILDS

This branch is the OGB-MolPCBA-style graph setup.

### Tell users to expect

- graph-network tooling,
- sparse graph dependencies,
- large-batch training,
- a benchmark focus on average precision rather than classification accuracy.

## How to route questions safely

- If the user wants a quick DA explanation on WILDS, reuse the same loss family names as the image-classification branch.
- If the user wants the dataset or backbone choice, route to `../vision-data-models/SKILL.md`.
- If the user wants the actual benchmark reproduction recipe, keep this as reference-only guidance and do not claim the CPU smoke helper validates it.
