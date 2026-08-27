# TinyCLIP Workflows

## Zero-shot evaluation

Use the `main_for_test.py` path with a downloaded checkpoint and an ImageNet-1k validation root:

```bash
python -m torch.distributed.launch --use_env --nproc_per_node 8 src/training/main_for_test.py \
  --imagenet-val <imagenet-root> --model <TinyCLIP-model-name> --eval --resume <checkpoint>
```

For auto-weight-inheritance checkpoints, keep `--model ViT-B-32` and add the pruning flags documented in the repo:

```bash
python -m torch.distributed.launch --use_env --nproc_per_node 8 src/training/main_for_test.py \
  --imagenet-val <imagenet-root> --model ViT-B-32 --prune-image --prune-text \
  --eval --resume <checkpoint>
```

## Inference

The repository's `inference.py` is the user-facing inference entry point.
Use the bundled command builder to print a safe launcher string instead of opening the source file.

## Pretraining stages

TinyCLIP training is stage-based:

- auto weight inheritance: 100→75, 75→50, 50→25
- manual weight inheritance: 100→75, 75→50

Each stage is multi-node and expects the larger OpenCLIP training data pipeline.
The generated skill keeps those stage scripts as distilled command templates, not as hard runtime dependencies.

## Input assumptions

- ImageNet-1k validation is needed for zero-shot evaluation.
- Pretraining expects the large-scale OpenCLIP data setup described in the repo docs.
- Checkpoints can come from the model zoo or a user-provided path.
