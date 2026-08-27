# Classification model overview

## Standalone-project rule

`image_classification/` is a collection of model projects rather than an
installable `paddlevit` package. A selected directory normally owns its own
`config.py`, model module, `datasets.py`, utility modules, YAML configs, and
single- or multi-GPU main script. Each can reuse bare import names such as
`config`, `datasets`, and `utils`; run from the selected directory or put that
one directory first on `PYTHONPATH`. Do not import several model directories
into one process.

The common operating lifecycle is: obtain defaults from `config.py`, merge a
matching YAML (including its `BASE` values), apply supported CLI overrides,
build the model with the family builder, create that directory's dataset and
loader, then evaluate/fine-tune/train using its own main script.

## Family map

| Directory or group | Typical model module/builder | Operating distinction |
|---|---|---|
| `ViT` | `vit.build_vit(config)` | Reference baseline. The inspected default builder returned `[1, 1000]` on `gpu:0`. |
| `DeiT` | `deit.build_deit(config)` / `build_vit(config)` | Distilled and non-distilled main scripts are distinct. |
| `SwinTransformer` | `swin.build_swin(config)` | Image/window geometry and positional adaptation matter. |
| `VOLO` | `volo.build_volo(config)` | Family-specific attention/output configuration. |
| `CSwin` | `cswin.build_cswin(config)` | Cross-shaped window settings are architecture-specific. |
| `PVTv2` | `pvtv2.build_pvtv2(config)` | Pyramid stages are config-bound. |
| `BEiT` | `beit.build_beit(config)` | Extra relative-position, augmentation, EMA, and optional VAE-related fields; export is elsewhere. |
| `MobileViT` | `mobilevit.build_mobilevit(config)` | Mobile-oriented image/patch settings; repository includes a multi-scale sampler test. |
| `ViP` | `vip.build_vip(config)` | Permutator/MLP-like family. |
| `XCiT` | `xcit.build_xcit(config)` | Distilled/non-distilled entry points. |
| `PiT` | `pit.build_pit(config)` | Pooling transformer; distilled variants differ. |
| `HaloNet` | `halonet.build_halonet(config)` | Local-attention resolution/window constraints. |
| `PoolFormer` | `poolformer.build_poolformer(config)` | MetaFormer/pooling family. |
| `BoTNet` | `botnet.build_botnet50(config)` | ResNet/BoTNet-specific backbone construction. |
| `CvT` | `cvt.build_cvt(config)` | Convolutional embedding and stage configuration. |
| `HVT` | `hvt.build_hvt(config)` | Hierarchical pooling transformer. |
| `TopFormer` | `topformer.build_topformer(config)` | Classification directory only; a similarly named segmentation route is separate. |
| `ConvNeXt` | `convnext.build_convnext(config)` | Convolutional baseline; use its config, not a ViT config. |
| `CoaT` | `coat.build_coat(config)` | Co-scale convolutional attention. |
| `ResT` | `rest.build_rest(config)` / `rest_v2.build_restv2(config)` | Select ResT versus ResTV2 deliberately. |
| `MLP-Mixer`, `ResMLP`, `gMLP`, `FF_Only` | `build_mlp_mixer`, `build_resmlp`, `build_gmlp`, `build_ffonly` | MLP classifier families with non-interchangeable schemas. |
| `RepMLP`, `CycleMLP`, `ConvMixer`, `ConvMLP`, `RepLKNet` | family `build_*` functions | Reparameterization or convolutional/MLP family semantics; use directory docs before train/deploy transitions. |
| `MobileOne` | `mobileone.build_mobileone(config)` | Reparameterized mobile model; deployment graph conversion is outside this skill. |
| `MAE` | `transformer.build_mae_finetune(config)` / `build_mae_pretrain(config)` | Fine-tuning and masked pretraining are separate workflows. |

The source tree additionally advertises folders such as CaiT, Shuffle
Transformer, T2T-ViT, CrossViT, Focal Transformer, LeViT, and MobileFormer.
They use the same standalone-project rule but must be verified from their own
README/module before a builder or CLI is stated. The smoke script discovers a
`build_*` function when no explicit mapping is bundled, but a successful import
still does not prove the model recipe is compatible with a checkpoint.

## Input and output contract

Most supervised folders expect an NCHW float tensor `[batch, 3, H, W]` after
that folder's transform pipeline and produce class logits, commonly
`[batch, MODEL.NUM_CLASSES]`. Do not hard-code 224, 1000, or `[0.5]*3`
normalization: those are common/default values, not universal contracts.

Changing image size can invalidate patch counts, positional embeddings, window
partitioning, or downsampling stages. Changing class count invalidates the
classifier head. A checkpoint only belongs to a model after model family,
variant, resolution, preprocessing, and head width are all checked.

## Facial-expression Swin

`facial_expression/` is a separate Swin-based classification project. It uses
aligned 224x224 face frames and ABAW annotation folders, not ImageNet list
files. Its dataset supports three label modes:

- `all`: eight original labels — Neutral, Anger, Disgust, Fear, Happiness,
  Sadness, Surprise, Other;
- `coarse`: five labels — Neutral, Happiness, Surprise, Other, Negative;
- `negative`: four labels — Anger, Disgust, Fear, Sadness; other labels are
  excluded from this branch.

The published coarse-to-fine workflow combines coarse and negative models.
Do not represent the accuracy of either branch as the cascade's final result.

## Evidence basis

This reference distills the classification and root READMEs, representative
ViT/DeiT/Swin/BEiT/MobileViT/MobileOne/MAE source/config files, the
facial-expression source, MAE tests, and the MobileViT multi-scale sampler
test from the pinned PaddleViT source snapshot.
