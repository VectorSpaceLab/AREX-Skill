# Self-Training Troubleshooting

Use this guide when TLLib self-training components import but a training loop fails, produces no pseudo labels, or behaves unstably. For dataset/model loader issues, route to [vision-data-models](../../vision-data-models/SKILL.md). For fine-tuning/checkpoint choices, route to [task-generalization](../../task-generalization/SKILL.md). For domain-adaptation MCC usage, route to [domain-adaptation](../../domain-adaptation/SKILL.md).

## Quick triage

1. Run `scripts/tllib_self_training_smoke.py` in the same Python environment.
2. Print shapes and dtypes for every batch: labeled images/labels, weak unlabeled images, strong unlabeled images, unlabeled indices, and logits.
3. Confirm logits are `(N, C)` and labels are integer class IDs in `[0, C - 1]`.
4. Log pseudo-label mask ratio and predicted class histogram every few iterations.
5. Run one batch on CPU or a single GPU before scaling to full training.

## Logits vs probabilities mistakes

| API | Expects logits? | Expects probabilities? | Common mistake |
| --- | --- | --- | --- |
| `ConfidenceBasedSelfTrainingLoss` | `y`, `y_target` are logits | no | Passing softmax probabilities into `F.cross_entropy`, causing weaker gradients or invalid assumptions. |
| `StrongWeakConsistencyLoss` | `y_strong`, `y` are logits | no | Passing probabilities, then the module applies softmax/log-softmax again. |
| `MinimumClassConfusionLoss` | logits | no | Passing already-softmaxed probabilities and changing the temperature effect. |
| `ClassBalanceLoss` | no | `p` must be probabilities in `[0, 1]` | Passing logits into binary cross entropy. |
| `L2ConsistencyLoss` | not required | usually probabilities/normalized predictions | Passing class indices or mismatched shapes. |

Sanity snippet:

```python
assert logits.dim() == 2
assert logits.size(1) == num_classes
prob = torch.softmax(logits, dim=1)
assert torch.allclose(prob.sum(dim=1), torch.ones(prob.size(0), device=prob.device), atol=1e-5)
```

## Shape and target errors

**Symptoms**

- `Expected input batch_size ... to match target batch_size ...`
- `Target ... is out of bounds`
- `mat1 and mat2 shapes cannot be multiplied`
- `too many values to unpack` from a classifier forward.

**Causes and fixes**

- Labeled and unlabeled batches have different batch sizes but are combined without separate accounting. Compute each loss on its own batch and scale by explicit trade-offs.
- Labels are one-hot but cross entropy expects integer class IDs. Convert with `labels.argmax(dim=1)` only if one-hot encoding is intentional.
- `num_classes` in the classifier does not match dataset labels. Confirm class ordering in the dataset loader.
- `DSTImageClassifier` returns three outputs in train mode and one output in eval mode. Write mode-specific unpacking.
- Self-Tuning classifier returns `(h, y)` in train mode and `y` in eval mode.

## Empty pseudo-label masks

**Symptoms**

- Unsupervised loss is zero or nearly zero.
- `mask.mean()` stays at 0.
- FlexMatch history remains mostly `-1`.
- Validation matches ERM despite adding SSL.

**Causes**

- Confidence threshold is too high for the current model stage.
- The model is uncalibrated because training just started or checkpoint/domain is mismatched.
- Weak augmentation is too destructive, so teacher/weak predictions are not confident.
- Class count/order is wrong, making confidence meaningless.
- For FlexMatch, unlabeled indices are missing or unstable, so history does not update.

**Fixes**

1. Log `confidence.max()`, `confidence.mean()`, and a histogram of pseudo labels.
2. Try a short diagnostic run with a lower threshold (for example 0.7) before returning to the intended threshold.
3. Warm up with ERM or ramp the SSL trade-off.
4. Ensure weak augmentation is weaker than strong augmentation.
5. For FlexMatch, verify `idxes.min() >= 0`, `idxes.max() < n_unlabeled_samples`, and that the same sample keeps the same index.

## NaN or exploding losses

**Likely causes**

- Temperature is zero or too small in UDA/MCC/Self-Tuning.
- Learning rate is too high when adding a large unsupervised trade-off.
- Probabilities contain exact zeros before a log operation in custom consistency code.
- Mixed precision or GPU training magnifies unstable augmentations/loss scaling.

**Fixes**

- Ensure temperatures are positive and start from documented-style values (`0.85` for UDA-like, `2.0` for MCC-like, `0.07` for contrastive Self-Tuning) before tuning.
- Check every scalar loss with `torch.isfinite(loss)`.
- Ramp up consistency/self-training weights.
- Disable mixed precision until a full-precision one-batch run is stable.

## Teacher EMA update order

**Wrong pattern**

```python
teacher.update()     # stale: updates before student changed
loss.backward()
optimizer.step()
```

**Preferred pattern**

```python
loss.backward()
optimizer.step()
teacher.update()
```

Additional cautions:

- Wrap teacher prediction in `torch.no_grad()`.
- Keep teacher mode intentional (`eval()` for stable inference; `train()` only if the method intentionally tracks train-mode behavior).
- If using BatchNorm, decide whether to sync running statistics with `update_bn`; do not do it accidentally every batch without understanding the effect.

## Labeled/unlabeled loader imbalance

**Symptoms**

- One iterator exhausts early.
- Effective labeled samples repeat too often.
- Unsupervised loss dominates because unlabeled batch size is much larger.
- FlexMatch dynamic thresholds update only a small subset of unlabeled indices.

**Fixes**

- Use separate labeled and unlabeled iterators and define `iters_per_epoch` explicitly.
- Track actual batch sizes for both branches instead of assuming one global batch size.
- Scale `lambda_u`, `lambda_balance`, and other trade-offs by intent, not by accidental loader lengths.
- For class-balanced labeled subsets, confirm each class has the requested labeled samples; if not, reduce `num_samples_per_class` or create an explicit split.
- For distributed/multi-worker loaders, ensure unlabeled indices remain global dataset indices.

## Weak/strong augmentation problems

**Symptoms**

- Pseudo labels become confidently wrong.
- Strong branch loss is much larger than labeled loss.
- Validation degrades after enabling SSL.

**Fixes**

- Verify weak and strong transforms preserve image size and normalization expected by the model.
- Weak augmentation should usually be mild enough for reliable pseudo labels.
- Strong augmentation can include RandAugment-like policies, but it must preserve class identity.
- For small images such as CIFAR-style data, use resizing/crop policies appropriate for that resolution; do not blindly use large-image settings.

## Checkpoint conversion failures

See [checkpoint conversion](checkpoint-conversion.md) for the conversion recipe. Common fixes:

- Always load external checkpoints with `map_location="cpu"` first.
- Confirm keys begin with the expected MoCo-style prefix before stripping.
- Split `fc.*` keys from backbone keys; target SSL classifier heads usually need new randomly initialized weights.
- Use `strict=False` for the first load and review `missing`/`unexpected` keys.
- Confirm the backbone architecture exposes `out_features` before wrapping it with Self-Tuning or DST classifiers.

## GPU/data/runtime requirements

Component-level checks can run on CPU. Full SSL training is different:

- Real image classification training is normally CUDA-heavy and dataset-heavy.
- Optional model libraries may be needed for user-selected architectures.
- External dataset links can be unavailable, slow, license-restricted, or already expected in a local layout.
- Pretrained checkpoints are external artifacts; record their source and architecture.
- Multi-GPU behavior is not validated by the bundled smoke script.

If the user asks for benchmark-scale training, first confirm dataset availability, checkpoint paths, GPU device plan, expected runtime, and whether optional packages are installed.

## Import/version compatibility

TLLib 0.4 is an older PyTorch/TorchVision-era package. If imports fail around torchvision model internals or NumPy aliases:

- Prefer a Python/PyTorch/TorchVision stack compatible with older TLLib APIs.
- Avoid assuming newest TorchVision model factories work unchanged.
- Keep package import checks separate from benchmark training checks.
- Use the bundled smoke script as the minimum self-training API readiness check, not as proof that all image model factories or training examples work.

## Reporting checklist for a failed user run

Ask the user for:

- Method name and loss components used.
- `tllib`, Python, PyTorch, and TorchVision versions.
- Shapes of labeled/unlabeled images, labels, indices, and logits.
- Threshold, temperature, SSL trade-off weights, EMA alpha, queue size, and batch sizes.
- Mask ratio and pseudo-label class histogram.
- Whether the failure happens before forward, during loss computation, backward, optimizer step, teacher update, checkpoint load, or validation.
