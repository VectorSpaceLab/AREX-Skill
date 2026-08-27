# GeoSeg model and label catalog

## Dataset labels

The dataset modules define the authoritative class order and visualization
palette. `num_classes` must be the length of `CLASSES`; the output head must
have that many channels. Palette entries are RGB triples indexed by the integer
mask label.

| Dataset | Classes in mask order | Count | Palette (same order) | Config ignore index |
| --- | --- | ---: | --- | ---: |
| LoveDA | `background`, `building`, `road`, `water`, `barren`, `forest`, `agricultural` | 7 | `[[255,255,255],[255,0,0],[255,255,0],[0,0,255],[159,129,183],[0,255,0],[255,195,128]]` | 7 |
| Potsdam | `ImSurf`, `Building`, `LowVeg`, `Tree`, `Car`, `Clutter` | 6 | `[[255,255,255],[0,0,255],[0,255,255],[0,255,0],[255,204,0],[255,0,0]]` | 6 |
| Vaihingen | `ImSurf`, `Building`, `LowVeg`, `Tree`, `Car`, `Clutter` | 6 | `[[255,255,255],[0,0,255],[0,255,255],[0,255,0],[255,204,0],[255,0,0]]` | 6 |
| UAVID | `Building`, `Road`, `Tree`, `LowVeg`, `Moving_Car`, `Static_Car`, `Human`, `Clutter` | 8 | `[[128,0,0],[128,64,128],[0,128,0],[128,128,0],[64,0,128],[192,0,192],[64,64,0],[0,0,0]]` | 255 |

A mask passed to a multiclass head must contain only `0..num_classes-1` and the
configured ignore value. LoveDA, Potsdam, and Vaihingen use the class-count
value as the void/padding label in their checked-in configs. UAVID uses 255.
Do not silently turn an ignore value into an additional prediction class: the
head remains 7, 6, 6, or 8 channels respectively. `tools.metric.Evaluator`
ignores ground-truth values outside `0..num_class-1` when building its
confusion matrix, but the losses and crops still need a consistently configured
ignore value.

The dataset module defaults are not identical to the configs. For example,
`SmartCropV1` has a generic default of 12, and LoveDA's shared `train_aug`
passes 255, while the per-config LoveDA crop passes `ignore_index` (7). Use the
selected config's value for the actual run and inspect any custom transform.

## Model families

### Primary configured families

- **UNetFormer** (`geoseg.models.UNetFormer.UNetFormer`) is the usual
  supervision model. Its checked signature is
  `UNetFormer(decode_channels=64, dropout=0.1,
  backbone_name='swsl_resnet18', pretrained=True, window_size=8,
  num_classes=6)`. The timm backbone is created with `features_only=True` and
  four feature stages. In `train()` the forward result is `(main_logits,
  aux_logits)`; in `eval()` it is only `main_logits`. The checked-in LoveDA,
  Potsdam, UAVID, and Vaihingen UNetFormer configs set `use_aux_loss=True` and
  use `UnetFormerLoss`.
- **DC-Swin / DCSwin** exposes `dcswin_small`, `dcswin_base`, and
  `dcswin_tiny`. The verified small factory signature is
  `dcswin_small(pretrained=True, num_classes=4,
  weight_path='pretrain_weights/stseg_small.pth')`; the base and tiny factories
  follow the same three arguments with base/tiny default filenames. These
  factories filter loaded checkpoint keys to keys present in the constructed
  model. Their output is a single tensor and the checked-in DCSwin configs use
  `use_aux_loss=False`.
- **FTUNetFormer** has verified factory signature
  `ft_unetformer(pretrained=True, num_classes=6, freeze_stages=-1,
  decoder_channels=256, weight_path='pretrain_weights/stseg_base.pth')`.
  The factory constructs a larger Swin variant (`embed_dim=128`, depths
  `(2,2,18,2)`, heads `(4,8,16,32)`) and filters matching checkpoint keys.
  Its forward returns one logits tensor; the checked configs disable auxiliary
  loss.

The factory defaults of 4 or 6 classes are examples, not dataset discovery.
Always pass `num_classes=len(CLASSES)` explicitly when adapting a family to a
new dataset.

### Additional source families

These models are present in `geoseg/models/` but are not selected by the nine
checked-in dataset configs and were not runtime-smoke-verified in this
checkout. Treat their signatures as source-level guidance and run a small
constructor/shape probe before relying on them:

- `MANet(num_channels=3, num_classes=5, backbone_name='resnet50', pretrained=True)`
  uses timm feature stages and returns one logits tensor.
- `ABCNet(band=3, n_classes=8, pretrained=True)` uses a timm
  `swsl_resnet18` context path. In training mode its source returns
  `(main, aux16, aux32)`; in eval mode it returns main logits. It is not wired
  into the checked configs, so do not infer a compatible loss from its tuple.
- `BANet(num_classes=6, weight_path='pretrain_weights/rest_lite.pth')` uses a
  ResT-lite dependency path and returns one logits tensor. Its `weight_path`
  is loaded with `torch.load` when the path is non-null.
- `A2FPN(band=3, class_num=6, encoder_channels=[512,256,128,64],
  pyramid_channels=64, segmentation_channels=64, dropout=0.2)` uses a
  torchvision ResNet-18 created with pretrained weights and returns one logits
  tensor. The source's legacy `resnet18(pretrained=True)` behavior depends on
  the installed torchvision version.
- `PyramidMamba` and `EfficientPyramidMamba` use timm feature backbones and
  `mamba_ssm.Mamba`; their source import is optional and was not verified in the
  inspection environment. `PyramidMamba` defaults to a Swin backbone and
  `img_size=1024`, while `EfficientPyramidMamba` defaults to
  `swsl_resnet18`. Do not describe either as available until `mamba_ssm`, its
  CUDA-compatible dependencies, and the selected timm backbone are probed.

## Pretrained behavior

There are two different meanings of `pretrained=True` in this repository:

1. UNetFormer, MANet, ABCNet, and the Mamba wrappers pass `pretrained=True` to
   `timm.create_model`. This may need a cached/downloadable timm checkpoint;
   it is not the same as a local `pretrain_weights/*.pth` file.
2. DCSwin, FTUNetFormer, and BANet explicitly call `torch.load(weight_path)`
   when `pretrained` is true and `weight_path` is not `None`, then copy only
   matching keys. A missing path fails during construction. Pass
   `pretrained=False` or `weight_path=None` for an intentional random-init
   smoke test; do not claim pretrained initialization in that case.

A training checkpoint is a separate artifact from a backbone pretraining file:
`pretrained_ckpt_path` loads a Lightning checkpoint before `fit`, while
`resume_ckpt_path` is passed to `trainer.fit`. `weights_path` and
`test_weights_name` identify saved run checkpoints for test scripts. Keep these
roles distinct when diagnosing a missing file.
