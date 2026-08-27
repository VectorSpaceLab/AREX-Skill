# Pretraining and Adaptation Troubleshooting

## First triage step

Run the bundled helper before debugging a full training loop:

```bash
python sub-skills/pretraining-and-adaptation/scripts/smoke_pretraining_wrappers.py --json
```

A tiny random-tensor failure is cheaper and more informative than a failed
multi-hour run. Treat `version_fragile` as a compatibility warning, not as a
user data problem.

## MAE and SimMIM positional-embedding mismatch

**Symptoms**

- `MAE` or `SimMIM` fails on the first forward pass with an error like:
  `The size of tensor a (...) must match the size of tensor b (...) at
  non-singleton dimension ...`.
- The failure happens before optimizer logic and does not depend on labels.

**Likely cause**

The wrappers index the encoder positional embedding as if it had a batched
layout. The current base `ViT` exposes a 2-D positional embedding, so slicing
and broadcasting can place the embedding dimension where the token dimension is
expected.

**Recovery**

1. Run `--case mae --case simmim` with the smoke helper in the user runtime.
2. If the helper reports `version_fragile`, do not claim the wrapper is
   verified for that package version.
3. Use a compatible encoder/version, or patch and validate the wrapper locally
   only after a one-step `loss.backward()` passes.
4. If an upgraded package reports `verified`, update the user-facing guidance to
   say the installed version has fixed the shape issue; keep the smoke as the
   proof.

## MPP encoder and token-shape expectations

**Symptoms**

- `MPP` fails around `cls_token` repeat, patch embedding, or transformer token
  shapes; common fragments include `EinopsError` and repeat pattern errors.
- The failure occurs with a normal base `ViT` before a scalar loss is produced.

**Likely cause**

`MPP` assumes a transformer object with class-token and patch-embedding layouts
that differ from the current base `ViT`. It also expects the transformer to
accept and return a patch-token sequence compatible with the masked patch
prediction head.

**Recovery**

1. Run `--case mpp` before using MPP in training.
2. If it is `version_fragile`, prefer `MP3` for a currently verified masked
   position objective or provide a transformer wrapper that exactly matches
   `MPP` expectations.
3. When adapting an encoder, verify all of these before training: patch count,
   `cls_token` shape, `pos_embedding` shape, `to_patch_embedding` output shape,
   and final logits shape from `to_bits`.

## DINO, EsViT, and LeJEPA hook registration

**Symptoms**

- Constructor or first forward fails with `hidden layer (...) not found`.
- Forward fails with `hidden layer ... never emitted an output`.
- EsViT region loss fails because the hidden layer emits pooled vectors instead
  of feature maps.

**Likely cause**

These wrappers register a forward hook on `hidden_layer`. For DINO and LeJEPA,
a flattened embedding can work. For EsViT, the hidden layer must emit regional
features shaped like `(batch, channels, height, width)` before global pooling.

**Recovery**

1. Inspect `dict(model.named_modules()).keys()` in the user runtime to choose a
   real module name; do not guess from a paper diagram.
2. For a top-level `ViT` DINO/LeJEPA smoke, start with `hidden_layer='to_latent'`.
3. For EsViT, choose a multistage backbone layer that emits spatial maps; if it
   emits logits or flattened tokens, pick an earlier layer or use a different
   backbone.
4. Re-run the smoke helper after changing `hidden_layer`.

## DINO, EsViT, and LeJEPA augmentation prerequisites

**Symptoms**

- Import errors mention `torchvision`.
- First forward fails inside `RandomResizedCrop`, color jitter, grayscale,
  Gaussian blur, or normalization.
- Loss is not finite only when real augmentations are enabled.

**Likely cause**

These learners import `torchvision.transforms` and run augmentation/crop logic
inside `forward`. Real training images must be tensor batches with the expected
channels, image size, dtype/range, and normalization assumptions.

**Recovery**

1. Install or repair `torchvision` only if the selected workflow requires these
   learners.
2. For wiring checks, pass `augment_fn=torch.nn.Identity()` and
   `augment_fn2=torch.nn.Identity()` to isolate hook/model issues from data
   augmentation issues.
3. For real training, restore stochastic augmentations and validate image range
   and normalization separately from the wrapper smoke.
4. For DINO and EsViT, call `update_moving_average()` after each optimizer step,
   but only after the first forward has created the teacher encoder.

## Optional dependency gaps

| Symptom | Likely missing or incompatible dependency | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'torchvision'` while importing DINO, EsViT, LeJEPA, torchvision teachers, or dataset recipes | `torchvision` | Install a torch/torchvision pair compatible with the runtime PyTorch build. Use identity augmentations for smoke, then validate real transforms. |
| `ModuleNotFoundError: No module named 'torchaudio'` while importing VAAT | `torchaudio` | Treat VAAT as optional until torchaudio is installed. Match torchaudio to the runtime PyTorch version before constructing audio spectrogram flows. |
| Full decorrelation training script asks for `accelerate` or `wandb` | heavyweight training dependencies | Do not install them for one-step smoke. Install only for intentional full training and decide W&B online/offline mode explicitly. |
| `SigLIPVAT.load_siglip()` asks for checkpoint/loading libraries | `huggingface_hub`, `safetensors`, storage/network for the checkpoint | Keep pretrained checkpoint loading separate from random-tensor smoke. Approve network/storage first and validate the checkpoint path. |
| README distillation example imports `torchvision.models.resnet50` | `torchvision` and pretrained teacher weights if `pretrained=True` / weights are requested | Use a tiny local teacher for wrapper smoke; use real ResNet only for a real distillation recipe with approved weights/downloads. |

## Long training, download, and checkpoint assumptions

**Symptoms**

- A user expects the bundled helper to reproduce CIFAR, ImageNet, DINO, EsViT,
  or checkpointed SigLIP results.
- The environment tries to download CIFAR100, pretrained teacher weights, or
  SigLIP weights during a “smoke” check.
- W&B, Accelerate, Kaggle, or dataset paths become the main failure instead of
  wrapper construction.

**Recovery**

1. Separate one-step wrapper smoke from full training. The bundled helper uses
   random tensors only and performs no downloads.
2. For full training, ask for dataset location, preprocessing, batch size,
   optimizer, checkpoint path, logging mode, and runtime budget.
3. Do not convert reference-only training scripts into default executable runs;
   distill their model/loss wiring into a tiny local smoke first.
4. If a pretrained checkpoint is needed, verify the file exists or obtain
   approval for network download before calling checkpoint loaders.

## VAT, SigLIP-VAT, and VAAT shape errors

**Symptoms**

- Assertions fail around input rank or `time_seq_len`.
- Predicted action shape does not match target action shape.
- Passing a plain 4-D image tensor behaves unexpectedly in current VAT code.

**Likely cause**

The action wrappers pack view/time/image representations before cross-attending
from action tokens. Rank and constructor settings must match exactly.

**Recovery**

1. For image-only VAT smoke, pass `(batch, views, channels, height, width)` even
   when `views == 1`.
2. For video/time variants, pass `(batch, views, channels, time, height, width)`
   and set `time_seq_len=time`.
3. Ensure `actions.shape[1] == action_chunk_len` and `actions.shape[2] ==
   dim_action` when asking for a supervised loss.
4. Enable optional conditioning at construction time before passing it at
   forward time: `num_tasks` for `tasks`, `dim_extra_token` for `extra`, and
   `num_advantage_bins` for `advantages`.
5. Route questions that are only about video/variable input shapes, not action
   adaptation, to the variable-shapes/video sub-skill.

## WWT hierarchy and return-structure surprises

**Symptoms**

- Constructor asserts that slots must be strictly decreasing.
- Training code assumes a tensor but `forward` returns a tuple.

**Likely cause**

WWT builds a part-whole slot hierarchy and can include extra task heads,
`return_tokens`, and SigReg losses.

**Recovery**

1. Use a strictly decreasing `num_slots` tuple, such as `(4, 2)` in a smoke.
2. Inspect the one-step return structure before writing optimizer code.
3. If `sigreg_slots` is enabled, add the returned SigReg loss to the training
   objective with an explicit weight.
4. If `return_tokens=True`, unpack slot logits and token logits deliberately.

## vit_with_decorr unpacking and auxiliary-loss weighting

**Symptoms**

- Code written for a normal classifier crashes because it receives a tuple.
- The decorrelation auxiliary loss dominates the supervised task loss.

**Likely cause**

`vit_with_decorr.ViT` returns `(logits, decorr_aux_loss)`, and the full training
script weights the auxiliary term separately.

**Recovery**

1. Always unpack `logits, decorr_aux_loss = model(images)`.
2. Start with a small explicit weight, for example `total = ce_loss + 0.1 *
   decorr_aux_loss`, then tune for the real dataset.
3. Do not run dataset-downloading training recipes as smoke checks; use the
   bundled no-download helper first.
