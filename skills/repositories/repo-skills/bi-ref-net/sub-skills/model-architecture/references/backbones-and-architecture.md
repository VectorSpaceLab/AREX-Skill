# Backbones and architecture notes

## Default model identity

The verified default `Config()` facts for this source snapshot are:

- `task='DIS5K'`, `testsets='DIS-VD'`, `training_set='DIS-TR'`
- `model='BiRefNet'`, `size=(1024, 1024)`, `device=0`
- `bb='swin_v1_l'`
- `mixed_precision='bf16'`, `compile=True`, `SDPA_enabled=True`
- `ms_supervision=True`, `out_ref=True`, `dec_ipt=True`, `dec_ipt_split=True`
- `cxt_num=3`, `mul_scl_ipt='cat'`, `dec_att='ASPPDeformable'`
- `squeeze_block='BasicDecBlk_x1'`, `dec_blk='BasicDecBlk'`
- `optimizer='AdamW'`, with default DIS losses including `bce=30`, `iou=0.5`, `ssim=10`

Do not assume these are universal defaults for every released checkpoint. Treat them as the active source defaults for constructing a model from this code snapshot.

## Backbone keys and weight matching

`build_backbone(bb_name, pretrained=True, params_settings='')` supports these backbone families:

| Code key | Family | Channels before multi-scale concatenation | Pretrained-loading behavior |
|---|---|---:|---|
| `vgg16`, `vgg16bn` | torchvision VGG features split into `conv1`-`conv4` | `[512, 512, 256, 128]` | Uses torchvision default weights when `pretrained=True`. May download or use the torchvision cache depending on environment. |
| `resnet50` | torchvision ResNet stages split into `conv1`-`conv4` | `[2048, 1024, 512, 256]` | Uses torchvision default weights when `pretrained=True`. May download or use the torchvision cache depending on environment. |
| `swin_v1_l` | Swin v1 large | `[1536, 768, 384, 192]` | Loads the configured Swin-L backbone checkpoint file when `pretrained=True`. |
| `swin_v1_b` | Swin v1 base | `[1024, 512, 256, 128]` | Loads the configured Swin-B backbone checkpoint file when `pretrained=True`. |
| `swin_v1_s` | Swin v1 small | `[768, 384, 192, 96]` | Loads the configured Swin-S backbone checkpoint file when `pretrained=True`. |
| `swin_v1_t` | Swin v1 tiny | `[768, 384, 192, 96]` | Loads the configured Swin-T backbone checkpoint file when `pretrained=True`. This is the current code key for model-zoo entries often described as `swin_v1_tiny`. |
| `pvt_v2_b5`, `pvt_v2_b2` | PVT v2 | `[512, 320, 128, 64]` | Loads the configured PVT checkpoint file when `pretrained=True`. |
| `pvt_v2_b1` | PVT v2 | `[512, 320, 128, 64]` | Loads the configured PVT checkpoint file when `pretrained=True`. |
| `pvt_v2_b0` | PVT v2 | `[256, 160, 64, 32]` | Loads the configured PVT checkpoint file when `pretrained=True`. |
| `dino_v3_7b` | DINOv3 ViT via `timm` | `[4096, 4096, 4096, 4096]` | Constructs a `timm.create_model(..., features_only=True, dynamic_img_size=True, out_indices=...)`; source config points to a DINOv3 checkpoint filename for explicit loading. |
| `dino_v3_h_plus` | DINOv3 ViT via `timm` | `[1280, 1280, 1280, 1280]` | Same DINOv3 pattern. |
| `dino_v3_l` | DINOv3 ViT via `timm` | `[1024, 1024, 1024, 1024]` | Same DINOv3 pattern. |
| `dino_v3_b` | DINOv3 ViT via `timm` | `[768, 768, 768, 768]` | Same DINOv3 pattern. |
| `dino_v3_s_plus`, `dino_v3_s` | DINOv3 ViT via `timm` | `[384, 384, 384, 384]` | Same DINOv3 pattern. |

When `mul_scl_ipt='cat'` (the default), `Config` doubles the lateral channel list because the encoder concatenates full-resolution and half-resolution pyramid features. Changing `mul_scl_ipt` after training changes tensor shapes and usually invalidates checkpoint compatibility.

## `bb_pretrained=True` versus `False`

- `BiRefNet(bb_pretrained=True)` is for new-model initialization with backbone weights. It calls `build_backbone(..., pretrained=True)` and can fail if local backbone checkpoint files are absent or if torchvision/timm cannot provide the requested weights.
- `BiRefNet(bb_pretrained=False)` is the correct default for loading a full BiRefNet `.pth` or Hugging Face checkpoint because the full checkpoint should already include backbone parameters.
- Training resume code uses the same idea: it only requests backbone pretraining when not resuming from a local checkpoint file.
- If `pretrained=True` returns `None` from backbone loading after a state-dict mismatch, later model construction will fail because the backbone object is missing. The immediate fix is to supply the correct backbone weight file or construct with `bb_pretrained=False` when a full model checkpoint will be loaded.

## Weight/backbone matching from the model zoo

Use model-zoo names as compatibility hints, not as exact `Config.bb` strings:

- Original DIS/COD/HRSOD benchmark weights and most general-use/matting weights are Swin v1 large: set `config.bb='swin_v1_l'` before constructing the source model.
- Lite/tiny weights are Swin v1 tiny: set `config.bb='swin_v1_t'` in the current code. Some notebook text uses labels like `swin_v1_tiny`; translate that label to the current key.
- 2K/high-resolution weights may still use Swin v1 large but expect larger input sizes or more memory. Match both `config.bb` and the intended input resolution.
- If loading a local checkpoint gives `size mismatch` or large blocks of missing/unexpected keys, first confirm `config.bb`, `mul_scl_ipt`, decoder attention (`dec_att`), decoder block (`dec_blk`), input-decoder branch (`dec_ipt`, `dec_ipt_split`), context count (`cxt_num`), squeeze block, and multi-scale supervision flags.

## Encoder and decoder structure

Top-level `BiRefNet` contains:

1. `self.config = Config()` and `self.epoch = 1`.
2. `self.bb = build_backbone(self.config.bb, pretrained=bb_pretrained)`.
3. Optional auxiliary classifier when `auxiliary_classification=True`.
4. Optional `squeeze_module` when `squeeze_block` is not empty.
5. `self.decoder = Decoder(channels)`.
6. Backbone freezing for DINOv3 (`freeze_bb=True` when `'dino_v3' in config.bb`).

`forward_enc(x)` returns four feature maps plus optional classification predictions:

- VGG/ResNet backbones are treated as sequential `conv1`-`conv4` stages.
- Swin/PVT/DINO backbones return `(x1, x2, x3, x4)` directly.
- If `mul_scl_ipt='cat'`, the model runs the backbone on a half-resolution image pyramid and concatenates aligned features with the main features.
- If `mul_scl_ipt='add'`, the half-resolution features are interpolated and added instead.
- If `cxt_num>0`, selected shallower features are interpolated and concatenated into `x4` as context.

`forward_ori(x)` applies the optional squeeze module, then calls the decoder. During training with `out_ref=True`, it appends a Laplacian edge map of the input as gradient-reference supervision.

The public `forward(x)` returns:

- evaluation mode: `scaled_preds` list;
- training mode: `[scaled_preds, class_preds_lst]`, with decoder internals carrying gradient-reference outputs when active.

## Decoder flags that affect compatibility

| Flag | Default | Effect on architecture |
|---|---:|---|
| `dec_blk` | `BasicDecBlk` | Chooses decoder block class (`BasicDecBlk` or `ResBlk`). Changing it changes state-dict keys and residual behavior. |
| `dec_att` | `ASPPDeformable` | Adds `ASPP` or `ASPPDeformable` attention inside decoder blocks. Deformable mode uses `torchvision.ops.deform_conv2d`, which matters for ONNX export. |
| `dec_channels_inter` | `fixed` | Keeps decoder block intermediate channels at 64 unless set to adaptive. |
| `dec_ipt` | `True` | Adds image-input branches at decoder stages. |
| `dec_ipt_split` | `True` | Uses patch/channel-split input branches, changing expected input channels for decoder input blocks. |
| `ms_supervision` | `True` | Adds multi-scale side-output convolutions in training. |
| `out_ref` | `True` | Adds gradient-guided reference prediction/attention paths when training and gradient attention at decoder stages. |
| `squeeze_block` | `BasicDecBlk_x1` | Adds one squeeze block before the decoder; the block name and repeat count are parsed from the string. |
| `cxt_num` | `3` | Adds context channels into deepest features. |
| `mul_scl_ipt` | `cat` | Adds or concatenates half-resolution pyramid features; `cat` doubles configured lateral channels. |

A checkpoint trained with a different value for any of these flags may be unrecoverable with strict `load_state_dict` even if the backbone name is correct.

## SDPA and compile notes

- Swin v1 and PVT v2 attention paths use `Config.SDPA_enabled` to choose PyTorch scaled-dot-product attention when available.
- Source comments state that PyTorch `torch.compile` had version-sensitive behavior: old versions can have CPU memory leaks or compile failures, while newer versions were used for faster training.
- Compiled checkpoints may contain `_orig_mod.` prefixes. Use `check_state_dict` before loading into an uncompiled model.
- Do not use a successful CPU import as proof that GPU memory is sufficient for a full Swin-L model, high-resolution inputs, training, or ONNX conversion.
