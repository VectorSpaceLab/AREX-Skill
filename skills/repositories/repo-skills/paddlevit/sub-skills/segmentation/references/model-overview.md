# Segmentation model overview

This reference is a compatibility map for the source registry. Choose a
complete family YAML under `semantic_segmentation/configs/`; do not transplant
only `MODEL.NAME` into an unrelated config. The source factory is
`semantic_segmentation/src/models/__init__.py` and uses substring dispatch.

## Registry and heads

| `MODEL.NAME` match | Class | Backbone/head contract |
|---|---|---|
| `SETR` | `SETR` | `ViT_MLA` or `ViT`; `VIT_MLAHead`, `PUP_VisionTransformerUpHead`, or `Naive_VisionTransformerUpHead` |
| `UperNet` | `UperNet` | `SwinTransformer`, `CSwinTransformer`, or `FocalTransformer`; `UperHead` |
| `DPT` | `DPTSeg` | `VisualTransformer` plus `DPTHead` |
| `Segmenter` | `Segmentor` | `ViT`/`DeiT`; `MaskTransformer` or `LinearDecoder` |
| `Trans2Seg` | `Trans2Seg` | CNN segmentation backbone plus transformer encoder/decoder and CNN head |
| `Segformer` | `Segformer` | `MixVisionTransformer` plus `SegformerHead` |
| `TopFomer` | `TopFormer` | usually `TopTransformer` plus `SimpleHead`, `MaskTransformer`, or `LinearDecoder` |

### TopFormer spelling

The factory checks `"TopFomer"`, with the `r` missing, while the architecture
class and human-facing docs say TopFormer. Existing YAMLs use
`MODEL.NAME: "TopFomer"`. A config with the natural spelling `TopFormer` may
leave `get_model` without a model. Preserve the source spelling unless an
approved, tested source fix changes both factory and configs.

## Family contracts

### SETR

SETR is a ViT sequence-to-sequence model with three decoder variants:

- **MLA:** `ENCODER.TYPE: ViT_MLA`, `DECODER_TYPE: VIT_MLAHead`; the encoder
  supplies four features and the `MODEL.MLA` channels/index settings must
  match the selected base/large/huge ViT.
- **PUP:** `ENCODER.TYPE: ViT`,
  `DECODER_TYPE: PUP_VisionTransformerUpHead`; `MODEL.PUP` controls convolution
  and upsample layers.
- **Naive:** the same up-head family with
  `DECODER_TYPE: Naive_VisionTransformerUpHead`.

Auxiliary outputs are enabled by `MODEL.AUX.AUXIHEAD` and change the output
list and loss behavior. Keep hidden size, layer count, patch size, decoder
channels, class count, and crop geometry aligned. Existing configs cover
Pascal-Context, ADE20K, and Cityscapes. README model-zoo scores are historical
references, not a guarantee for a new checkpoint or data split.

### UperNet

UperNet combines a hierarchical transformer with `UperHead`. The supported
encoder types are `SwinTransformer`, `CSwinTransformer`, and
`FocalTransformer`; the implementation asserts `DECODER_TYPE == "UperHead"`.

The current `forward` implementation calls `self.aux_decoder` unconditionally,
while that layer is only created when `MODEL.AUX.AUXIHEAD` is true. Treat a
false auxiliary flag as unverified for this checkout; start with a known YAML
that enables the auxiliary FCN head and supplies `AUXFCN.IN_CHANNELS` and
`UP_RATIO`, or patch/test the source explicitly. For Swin, align stage depths,
window size, output indices, UperHead input channels, and pool scales. CSwin
and Focal require their family-specific split/focal lists too.

### DPT

DPT (`DPTSeg`) uses `VisualTransformer` and `DPTHead`. The representative large
ADE20K YAML uses patch size 16, hidden size 1024, 24 layers, hidden features
`[256, 512, 1024, 1024]`, `FEATURES: 256`, and `READOUT_PROCESS: project`.
Patch-grid geometry, crop size, feature widths, and `DATA.NUM_CLASSES` must
agree; YAML parsing does not catch every reshape incompatibility.

### Segmenter

Segmenter uses ViT or DeiT token outputs, then `MaskTransformer` or
`LinearDecoder`. `ENCODER.OUT_INDICES` generally selects the final layer, such
as `[11]` for a 12-layer base model. Encoder type, `KEEP_CLS_TOKEN`, and token
count affect slicing. The model interpolates to `DATA.CROP_SIZE`, so fixed
input geometry must be intentional.

### Trans2Seg

Trans2Seg uses a CNN encoder, a transformer encoder/decoder with learned class
prototypes, and a small CNN head. Representative configurations use
`resnet50c`, `EMBED_DIM: 256`, `DEPTH: 4`, `NUM_HEADS: 8`, `MLP_RATIO: 3`, and
`HID_DIM: 64`. The decoder spatial token count is derived from
`DATA.CROP_SIZE[0] // 16`; changing the crop size changes a model construction
contract. Auxiliary output and `TRAIN.IGNORE_INDEX` must agree with the
selected loss and dataset.

### SegFormer

SegFormer uses `MixVisionTransformer` and `SegformerHead`. The B0 ADE20K
config contains four stages with:

```yaml
MODEL:
  NAME: Segformer
  ENCODER: {TYPE: MixVisionTransformer, OUT_INDICES: [0, 1, 2, 3]}
  SEGFORMER: {IN_CHANNELS: [32, 64, 160, 256], CHANNELS: 256}
  TRANS:
    IN_CHANNELS: 3
    EMBED_DIM: 32
    NUM_STAGES: 4
    NUM_LAYERS: [2, 2, 2, 2]
    NUM_HEADS: [1, 2, 5, 8]
    PATCH_SIZE: [7, 3, 3, 3]
    STRIDES: [4, 2, 2, 2]
    SR_RATIOS: [8, 4, 2, 1]
```

For B1--B5 update all stage widths, depths, heads, decoder input channels,
and compatible weights together. Segmentation heads consume `DATA.NUM_CLASSES`;
keep a duplicated `MODEL.NUM_CLASSES` consistent even where the implementation
ignores it.

### TopFormer

TopFormer uses a token-pyramid encoder and a lightweight head. Important lists
include `TRANS.INPUT_CHANNELS`, `OUT_CHANNELS`, `EMBED_OUT_INDICE`,
`DECODE_OUT_INDICES`, `CFGS`, `KEY_DIM`, `DEPTH`, and injection settings.
Representative configs use `VAL.IS_SLIDE: false` and `VAL.SIZE_DIVISOR: 32`.
Do not change encoder/decoder list lengths or output indices independently.

## Shared config map

- `DATA.DATASET`, `DATA.DATA_PATH`, `DATA.NUM_CLASSES`: exact dataset factory
  key, root, and output classes.
- `DATA.CROP_SIZE`, `BATCH_SIZE`, `BATCH_SIZE_VAL`, `NUM_WORKERS`: model/input
  geometry and per-process loader settings; source comments favor workers 0.
- `MODEL.NAME`, `ENCODER`, `DECODER_TYPE`, `PRETRAINED`, `RESUME`: registry,
  architecture, backbone initialization, and declared resume field. The
  actual training CLI uses `--resume`, not `MODEL.RESUME`.
- `TRAIN.LOSS`, `AUX`, `WEIGHTS`, `IGNORE_INDEX`, optimizer, scheduler, and
  `ITERS`: loss/checkpoint training behavior.
- `VAL.IS_SLIDE`, `IMAGE_BASE_SIZE`, `SIZE_DIVISOR`, `CROP_SIZE`,
  `STRIDE_SIZE`, `SCALE_RATIOS`, `MEAN`, `STD`: preprocessing/inference
  geometry and normalization.
- `SAVE_DIR`, `SAVE_FREQ_CHECKPOINT`, `KEEP_CHECKPOINT_MAX`: outputs and
  retention.

YACS recursively merges `BASE` files relative to the including YAML. Inspect
those inherited files before assuming a visible value is the final value.
