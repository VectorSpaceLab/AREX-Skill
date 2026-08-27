# Checkpoint Loading

## `--resume` versus `--pretrained`

| Flag | Source field | Intended use | Loads optimizer/scheduler? |
| --- | --- | --- | --- |
| `--resume <checkpoint>` | `MODEL.RESUME` | Resume training or evaluate an already trained checkpoint | Yes, when present and not evaluation-only |
| `--pretrained <checkpoint>` | `MODEL.PRETRAINED` | Fine-tune from backbone/classification weights | No |

`--resume` expects a checkpoint dictionary with at least a `model` key. If optimizer, scheduler, epoch, max accuracy, or scaler keys are present, training resumes from that state.

`--pretrained` loads `checkpoint['model']`, deletes/reinitializes position-index and attention-mask buffers, interpolates position-bias tables when needed, and handles classifier-head mismatches.

## 22K-to-1K head remap

If a checkpoint has 21841 classifier classes and the current model has 1000 classes, the repo remaps the head using the 22K-to-1K map bundled with the repository. Other class-count mismatches cause the classifier head to be zero-initialized and skipped from the loaded state dict.

## SimMIM remap behavior

SimMIM fine-tuning has a separate utility that removes encoder prefixes, interpolates relative position bias tables, and remaps absolute position embeddings when image/window settings differ. Use `simmim-workflows` when the checkpoint comes from masked pretraining.

## Safe checks

Do not load large checkpoints merely to inspect a command. First verify:

- The file exists and is a PyTorch checkpoint.
- The intended flag is correct (`--resume` for evaluation/resume, `--pretrained` for fine-tuning).
- The config model family and class count match the checkpoint source.
- Any 22K-to-1K transfer is intentional.
