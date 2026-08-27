# Losses and metrics troubleshooting

Start with the shape and return tables in [api-reference.md](api-reference.md). The items below are the high-frequency failure modes for `lib.losses3D`.

## Symptom-to-fix matrix

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `RuntimeError: Unsupported loss function: ...` from `create_loss` | Loss name is misspelled, wrong case, or the class is not factory-backed. | Use one of the exact factory names in the API reference. Instantiate manual-only APIs such as `ContrastiveLoss`, `DiceLoss2D`, or `loss_vae` directly. |
| `AssertionError: 'input' and 'target' must have the same shape` in Dice-style loss | `classes` does not match logits channels, target was expanded with the wrong channel count, or `skip_index_after` slices target channels without matching model output channels. | For 3D semantic segmentation, use logits `[N, C, D, H, W]`, labels `[N, D, H, W]`, and construct `DiceLoss(classes=C)` or equivalent. If using `skip_index_after=k`, model output must have `k` channels. |
| `scatter` index error during one-hot expansion | Target labels are not integer class indices in the range `0..C-1`, or sparse instance ids were used with `ContrastiveLoss`. | Convert targets to `long`, clamp/remap only if semantically correct, and remap sparse instance ids to contiguous `0..num_instances-1` before `ContrastiveLoss`. |
| Default 3D `Trainer` fails with `cannot unpack non-iterable Tensor` or similar | The selected criterion returns a scalar tensor, but the trainer expects `(loss, per_channel_score)`. | Use a tuple-returning Dice-family criterion, or route the training-loop adaptation to [segmentation-workflows](../../segmentation-workflows/) so logging/backprop are changed consistently. |
| Writer/channel logging fails after `GeneralizedDiceLoss` | `GeneralizedDiceLoss` returns a tuple, but its side value is a scalar generalized Dice, not a per-class vector. | Either log it as a scalar metric or use `DiceLoss`/`BCEDiceLoss` when per-channel scores are required. |
| `PixelWiseCrossEntropyLoss.forward()` missing `weights` | Pixel-wise CE is not a two-argument criterion. | Call `criterion(output, target, weights)` with `weights.shape == target.shape == [N, D, H, W]`. It is not a drop-in for loops that call only `criterion(output, target)`. |
| Class-weight tensor device mismatch on CUDA | Criterion weight buffers or pixel class weights stayed on CPU while logits/targets moved to CUDA. | Construct weights on the target device or call `criterion.to(device)` after construction. Keep logits and targets on the same device. |
| Cross entropy fails on ignore labels | Direct `WeightedCrossEntropyLoss()` uses `ignore_index=-1`, while `create_loss('WeightedCrossEntropyLoss')` uses `-100` when no value is supplied. | Pass the ignore value explicitly and ensure targets use that exact value. |
| `BCEDiceLoss` breaks when changing `beta` | The implementation multiplies `beta` by the returned Dice tuple rather than only the scalar Dice loss. | Leave `beta=1` in unpatched MedicalZooPytorch, or patch the class before relying on non-default weighting. |
| `BCEWithLogitsLoss` shape mismatch | The factory returns raw PyTorch BCE, not `BCEDiceLoss`. It does not expand class-index labels. | Use float targets with exactly the same shape as logits, or use `BCEDiceLoss(classes=C)` for class-index segmentation labels. |
| `DiceLoss2D` fails only when batch size is one | `DiceLoss2D.expand_as_one_hot()` ends with `.squeeze(0)`, which removes a singleton batch dimension. | For singleton synthetic checks, pass input `[C, H, W]` and target `[1, H, W]`. For training, verify batch behavior and avoid untested singleton batches unless you adapt the loss. |
| `TagsAngularLoss` assertion on lengths | Inputs, targets, and `tags_coefficients` lengths differ. | Pass `inputs` as a list. With multiple heads, pass a target list of the same length and use matching `tags_coefficients`. |
| `TagsAngularLoss` shape assertion | Tag head channels do not match the configured `classes` after target one-hot expansion. | Set `classes` equal to the tag head channel count or produce tag heads with the expected channel count. |
| `ContrastiveLoss` index error for labels like `{0, 5}` | The loss counts unique labels but uses those labels directly as one-hot scatter indices. | Remap instance ids to contiguous labels `{0, 1, ...}` within each target volume before calling. |
| `loss_vae(type='L2')` gives non-finite values | The L2 branch computes a square root of `recon_x^2 - x^2`, which can be negative. | Prefer validated `BCE` or `L1` reconstruction branches, or patch and test the L2 formula before use. |

## Negative unsupported-loss guidance

`create_loss` is intentionally narrow and case-sensitive. Treat this as a validation gate rather than trying to coerce names.

```python
from lib.losses3D import create_loss

try:
    create_loss("ContrastiveLoss")
except RuntimeError as exc:
    print(exc)  # factory rejected it; instantiate ContrastiveLoss directly instead
```

Use direct construction when the factory cannot express the needed contract:

```python
from lib.losses3D import ContrastiveLoss, DiceLoss2D

embedding_loss = ContrastiveLoss()
dice_2d = DiceLoss2D(classes=7)
```

## Pre-flight checklist before a training run

1. Confirm the model output channel count `C` and the label vocabulary maximum both match the selected `classes` value.
2. Run [scripts/smoke_losses.py](../scripts/smoke_losses.py) on CPU in the same environment where `lib.losses3D` imports.
3. If CUDA is required, run the smoke check with `--cuda` and ensure custom class-weight tensors are created on, or moved to, the selected device.
4. For the stock 3D trainer, confirm the selected criterion returns a tuple and that the side metric has the shape your writer expects.
5. For scalar-only, pixel-wise, contrastive, angular, or VAE losses, move the training-loop question to [segmentation-workflows](../../segmentation-workflows/) so the loop owns the custom call signature and logging.
