# API reference and validation recipes

## Constructors and output contracts

The following signatures are verified from source and, where the inspection
environment allowed, the isolated API probe. The current shell's generic
Python did not have `timm`/`addict`, so live constructor imports are an
environment-specific gate; the exact accepted signatures below are retained
from the verified inspection record and source.

```python
UNetFormer(
    decode_channels=64, dropout=0.1, backbone_name='swsl_resnet18',
    pretrained=True, window_size=8, num_classes=6,
)
ft_unetformer(
    pretrained=True, num_classes=6, freeze_stages=-1,
    decoder_channels=256, weight_path='pretrain_weights/stseg_base.pth',
)
dcswin_small(
    pretrained=True, num_classes=4,
    weight_path='pretrain_weights/stseg_small.pth',
)
py2cfg(file_path)
Evaluator(num_class)
```

Useful source-level signatures for less-common families are cataloged in
[model-overview.md](model-overview.md). The factory defaults are not dataset
aware. Pass `num_classes` explicitly and select `pretrained=False` for a
controlled no-checkpoint construction smoke test.

For a tensor input of shape `(N, 3, H, W)`, segmentation models should return
`(N, C, H, W)` logits, where `C=num_classes`. UNetFormer in training mode
returns `(main_logits, aux_logits)`; call `model.eval()` to validate the
single-tensor inference contract. Check both tensor shape and finite values,
not just that construction returned an object.

## `py2cfg` and static inspection

`py2cfg` accepts a string or `pathlib.Path` ending in `.py`, requires the file
to exist, imports it under its stem, and returns a `ConfigDict`. Expected
errors include `TypeError` for non-Python files, `FileExistsError` for a missing
path (despite the historical exception name), and `ValueError` if the stem
contains a dot. The import is not sandboxed and can execute arbitrary module
level code. Use the bundled `inspect_config.py` first; it is intentionally
static and will report imports, assignments, model/loss calls, and path-like
string literals without constructing datasets or models.

A true `py2cfg` validation should be performed only after:

1. the current working directory makes every relative `data/...`,
   `pretrain_weights/...`, and output directory resolve as intended;
2. dataset directory pairs and equal image/mask counts exist;
3. the timm cache/download or explicit local checkpoint is ready;
4. optional `mamba_ssm` is installed if a Mamba model is selected; and
5. the selected backend is available (the known CUDA smoke was on an A100,
   while CPU-only availability does not prove all attention/backbone paths).

## Loss API

The losses are regular `torch.nn.Module` objects and usually accept
`(logits, target)`:

- `SoftCrossEntropyLoss(reduction='mean', smooth_factor=0.0,
  ignore_index=-100, dim=1)` supports class-index targets and masks the ignore
  value.
- `DiceLoss(mode='multiclass', classes=None, log_loss=False, from_logits=True,
  smooth=0.0, eps=1e-7, ignore_index=None)` supports multiclass logits and
  masks the ignore value before one-hot conversion.
- `JointLoss(first, second, first_weight=1.0, second_weight=1.0)` sums the two
  modules.
- `UnetFormerLoss(ignore_index=255)` combines smoothed CE + Dice and, for a
  two-item prediction tuple, adds the auxiliary CE term at weight `0.4`.
- Other available modules include focal, Lovasz, Jaccard, balanced BCE,
  bitempered, soft F1, edge, OHEM CE, and wing losses. They are not a reason to
  change a checked-in config without verifying target shape, reduction, and
  ignore-index handling.

Check the target's dtype (`torch.long` for multiclass class indices), its
maximum valid label, and whether an ignore value can pass through every loss.
Some binary/one-hot losses have different target assumptions; do not swap one
into a multiclass config solely because it is exported by `geoseg.losses`.

## Exported loss catalog

`geoseg.losses.__init__` wildcard-imports the loss modules, so the following
public classes are available from that namespace. They are not interchangeable
without checking target semantics:

| Family | Public classes | Input/target caution |
| --- | --- | --- |
| Cross entropy | `SoftCrossEntropyLoss`, `SoftBCEWithLogitsLoss` | multiclass class-index targets versus binary/multilabel targets; both support an ignore value but with different shapes |
| Dice/Jaccard | `DiceLoss`, `JaccardLoss` | configure `mode`, logits/probability assumption, and ignored-pixel handling; the checked configs use multiclass Dice with raw logits |
| Focal | `FocalLoss`, `BinaryFocalLoss`, `FocalCosineLoss` | binary and multiclass focal variants have different target assumptions; `FocalCosineLoss` is classification-shaped and does not expose the config ignore-index contract |
| Lovasz | `LovaszLoss`, `BinaryLovaszLoss` | multiclass softmax versus binary hinge; pass the intended ignore argument (`ignore` versus `ignore_index`) |
| Region/compound | `CrossEntropyWithL1`, `CrossEntropyWithKL`, `CompoundLoss` | region-proportion regularizers; configure mode, alpha, and ignore index explicitly |
| Tempered | `BiTemperedLogisticLoss`, `BinaryBiTemperedLogisticLoss` | requires temperature parameters and matching multiclass/binary targets |
| Binary/imbalance | `BalancedBCEWithLogitsLoss`, `EdgeLoss`, `OHEM_CELoss` | binary logits, edge-aware segmentation, and hard-example CE are distinct contracts |
| Soft F1 | `SoftF1Loss`, `BinarySoftF1Loss` | probability/logit and one-hot requirements differ; verify ignored-pixel behavior on the selected version |
| Utility | `JointLoss`, `WeightedLoss`, `WingLoss` | composition wrappers or regression-style loss; not a replacement for multiclass CE/Dice by name alone |

Only `UnetFormerLoss` and the smoothed CE + Dice `JointLoss` combinations are
used by the checked-in dataset configs. Treat the other exports as extension
points and run a target-shape/ignore-index smoke before putting one in a
config.

## Evaluator API

`Evaluator(num_class)` allocates a `num_class x num_class` confusion matrix.
`add_batch(gt_image, pre_image)` requires equal-shaped arrays, counts only
`0 <= gt < num_class`, and exposes `Intersection_over_Union()`, `F1()`,
`OA()`, `Precision()`, `Recall()`, `Dice()`, and `reset()`. Predictions outside
the matrix range can make `np.bincount` reshape fail; validate argmax output
range before adding a batch. The training loop excludes the final class from
Potsdam/Vaihingen-style aggregate mIoU/F1, but not from the label catalog; this
is a workflow metric convention, not permission to reduce `num_classes`.

## Minimal shape/contract probe

Use a tiny synthetic tensor only after the environment has the selected model's
imports. A model-family probe should:

```python
model = UNetFormer(pretrained=False, num_classes=7)
model.train()
train_out = model(torch.randn(1, 3, 64, 64))
assert isinstance(train_out, tuple) and train_out[0].shape[1] == 7
model.eval()
eval_out = model(torch.randn(1, 3, 64, 64))
assert eval_out.shape == (1, 7, 64, 64)
```

For DCSwin/FTUNetFormer, use `pretrained=False` and assert a single tensor.
The exact spatial size may be constrained by the backbone/window settings, so
start with a size divisible by the largest downsampling/window requirement and
reduce only after a successful baseline. This is a constructor/output check,
not a substitute for data, training, or checkpoint validation.
