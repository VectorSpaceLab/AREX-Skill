# Task API And Loss Wrappers

## Why Tasks Matter

The task-era training stack wraps model and loss in a `TrainingTask` subclass. The wrapper owns training forward, eval forward, batch preparation, DDP/FSDP setup, optional EMA state, checkpoint state-dict shape reconciliation, dummy batches, and `torch.compile` targets.

Code that previously passed separate `model` and `loss` objects to a loop should usually switch to:

```python
task = open_clip.create_task(args, model=model, dist_model=dist_model, naflex_data_config=naflex_data_config)
```

`open_clip.create_loss(args)` still exists for standalone custom loops, but the repository's training pipeline uses `create_task()`.

## Task Selection

`create_task()` chooses the wrapper from model type and args:

| Selector | Task | Objective |
| --- | --- | --- |
| Plain image/text model | `CLIPTask` | `ClipLoss` contrastive loss |
| `--siglip` | `SigLIPTask` | `SigLipLoss` sigmoid contrastive loss |
| model name contains `coca` | `CoCaTask` | `CoCaLoss` contrastive + caption loss |
| `--distill-model` and `--distill-pretrained` | `DistillCLIPTask` | student/teacher contrastive + distill loss |
| model is CLAP | `CLAPTask` | audio/text `ClipLoss` |
| model name contains `genlip` | `GenLipTask` | generative image-caption LM loss |
| model name contains `genlap` | `GenLapTask` | generative audio-caption LM loss |

`create_task()` rejects CLAP distillation. Distillation also asserts `--accum-freq 1` and is not supported with CoCa.

## Common Batch Conventions

Image/text tasks own this contract:

```python
batch = {"image": image_tensor_or_patch_dict, "text": text_tensor}
```

They also support legacy call shapes:

```python
task(batch)
task(images, texts)
task(image=images, text=texts)
task(images, text=texts)
```

CLAP uses:

```python
batch = {"audio": audio_tensor_or_patch_dict, "text": text_tensor}
```

When variable-length text is enabled, data loaders may include `text_valid`. Tasks select the keys they consume; do not assume tuple batches when debugging modern dataloaders.

## Batch Preparation

`TrainingTask.prepare_batch(batch, device, input_dtype)` recursively moves tensor values to the device.

Rules:

- Floating tensors are cast to `input_dtype` when one is provided.
- Integer and boolean tensors keep their dtype.
- Nested dicts such as NaFlex `image`/`audio` patch dictionaries are handled recursively.
- Non-tensor values pass through unchanged.

This is why custom data adapters should emit dicts of tensors rather than custom objects.

## Dummy Batches

Tasks provide `create_dummy_batch()` for FSDP eval scaffolding and smoke tests.

Image/text dummy batch without NaFlex:

```python
{
    "image": zeros[B, 3, H, W],
    "text": zeros[B, context_length],
}
```

Image/text dummy batch with a NaFlex data config:

```python
{
    "image": {
        "patches": zeros[B, max_seq_len, patch_dim],
        "patch_coord": long[B, max_seq_len, 2],
        "patch_valid": bool[B, max_seq_len],
        "seq_len": max_seq_len,
    },
    "text": zeros[B, context_length],
}
```

CLAP dummy batches use `audio` as the primary key; fixed CLAP produces waveform-style audio dicts, while NaFlex audio tasks produce patch dictionaries. Use the audio sub-skill for audio-specific fields.

## `CLIPTask`

`CLIPTask` calls the model with the batch dict, passes model outputs to `ClipLoss`, sums keys ending in `_loss`, and writes the total as `loss`.

Useful args:

- `--local-loss` to compute loss with local features against global features.
- `--gather-with-grad` to gather distributed features with gradients.
- Distributed rank/world size are plumbed into the loss.
- `logit_scale` and optional `logit_bias` are reported separately for logging, not included as loss terms.

## `SigLIPTask`

`SigLIPTask` inherits the CLIP task forward shape but constructs `SigLipLoss`.

Useful args:

- `--siglip` selects the task.
- `--loss-dist-impl gather` can choose a distributed implementation.
- Task/step compile disables loss label caching to avoid mutable state inside compiled regions.

`logit_bias` can be present for SigLIP models and is reported for logging.

## `CoCaTask`

`CoCaTask` handles the autoregressive caption label shift in the task layer rather than in the model:

```python
labels = batch["text"][:, 1:]
logits = model_out["logits"][:, :-1]
```

Useful args:

- `--coca-caption-loss-weight`, default `2.0`.
- `--coca-contrastive-loss-weight`, default `1.0`.
- Set contrastive weight to `0` and caption weight to `1` for caption-only fine-tuning.

With gradient accumulation, `CoCaTask.compute_accum_loss()` concatenates accumulated text labels correctly; do not reimplement the shift in an external loop unless you also mirror this behavior.

## `DistillCLIPTask`

`DistillCLIPTask` owns both student and teacher forward paths. The teacher runs without gradients. Loss inputs include student and teacher logits/features expected by `DistillClipLoss`.

Command constraints:

- Provide both `--distill-model` and `--distill-pretrained`.
- Keep `--accum-freq 1`.
- Do not combine with CoCa.
- CLAP distillation is not supported by `create_task()`.

## `CLAPTask`

`CLAPTask` maps audio model outputs to `ClipLoss`-style inputs:

- `audio_features` becomes the primary modality feature.
- `text_features` remains the text side.
- `logit_scale` and optional `logit_bias` are reported for logging.

Batch key is `audio`, not `image`. Route CLAP transform/data/eval details to `../audio-clap/SKILL.md`; keep generic optimizer/checkpoint/distributed decisions here.

## `GenLipTask` And `GenLapTask`

`GenLipTask` and `GenLapTask` are generative tasks over `[media ; text]` rows. They use fused model-computed autoregressive loss by default and hold no separate loss module in the fused path. External loss can be supplied for custom loops, but the default training path is the fused loss for memory efficiency.

Parser side effects:

- Model names containing `genlip` or `genlap` set `args.use_naflex=True`.
- `--accum-freq > 1` is rejected because generative tasks do not support contrastive feature caching.
- `GenLAP` uses the audio NaFlex data pipeline, usually `--dataset-type webdataset-audio`.

Route detailed NaFlex and generative model decisions to `../naflex-generative/SKILL.md`.

## EMA And Eval Forward

`TrainingTask.setup_ema()` can create a `ModelEmaV3` copy before FSDP is prepared. EMA is not compatible with FSDP2 sharded parameters after sharding. Eval forward uses `get_trainable_module(use_ema=True)`, so an initialized EMA module is preferred for eval and inference state dicts.

The default CLI path does not expose a user-facing `--model-ema` flag in the parser. Treat EMA as a task API capability for custom loops or future CLI extensions, not a default command-line behavior.

## Writing Custom Training Loops

For a custom loop, mirror the repository order:

1. Build model and preprocess/tokenizer.
2. Resolve NaFlex data config if needed.
3. Create task with `open_clip.create_task()`.
4. Apply locking, gradient checkpointing, compile, DDP/FSDP, and optimizer in the same ordering as task-era `main`.
5. Build data loaders that emit dict batches with task-owned keys.
6. Call `task.prepare_batch()` before `task(batch)`.
7. Backpropagate `losses["loss"]`, log report fields separately, and clamp logit scale through the task when relevant.
8. Use task checkpoint utilities rather than raw `model.state_dict()` when saving training state.
