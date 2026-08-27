# Supervised model and tensor overview

This catalog is the operating contract, not a copy of model source. The
runtime dispatch uses the exact values in the first column.

| `MODEL.NAME` | Trainer/model | Input at model boundary | Output | Key geometry |
| --- | --- | --- | --- | --- |
| `Physnet` | `PhysnetTrainer` / PhysNet | `N,C,T,H,W` | rPPG plus visual feature tensors | `PHYSNET.FRAME_NUM`, commonly 128; `NCDHW`, `DiffNormalized` |
| `iBVPNet` | `iBVPNetTrainer` / iBVPNet | `N,C,T,H,W` | rPPG, length `T-1` | `iBVPNet.FRAME_NUM`, commonly 160; channels 1, 3, or 4 |
| `FactorizePhys` | `FactorizePhysTrainer` / standard or big variant | `N,C,T,H,W` | rPPG plus voxel embeddings; FSAM adds factorized data and approximation error | `FactorizePhys.FRAME_NUM`, commonly 160; standard 72px, big 128px intent |
| `Tscan` | `TscanTrainer` / class `TSCAN` | flattened `N*T,C,H,W` | one scalar per flattened frame | `TSCAN.FRAME_DEPTH`, commonly 10; `NDCHW`, usually 6 channels |
| `EfficientPhys` | `EfficientPhysTrainer` / EfficientPhys | flattened `N*T,C,H,W` plus one repeated frame | one scalar per usable frame | `EFFICIENTPHYS.FRAME_DEPTH`, commonly 10; usually 3 raw channels |
| `DeepPhys` | `DeepPhysTrainer` / DeepPhys | flattened `N*T,C,H,W` | one scalar per frame | spatial size 36, 72, or 96; usually 6 channels |
| `BigSmall` | `BigSmallTrainer` / BigSmall | `(big, small)`, each flattened `N*T,C,H,W` | `(AU logits, BVP, respiration)` | fixed segment 3; common big/small sizes 144/9 |
| `PhysFormer` | `PhysFormerTrainer` / `ViT_ST_ST_Compact3_TDC_gra_sharp` | `N,C,T,H,W`, with `gra_sharp` supplied by trainer | `(rPPG, score1, score2, score3)` | common `T=160`, spatial 128, patch 4 |
| `PhysMamba` | `PhysMambaTrainer` / PhysMamba | `N,C,T,H,W` | rPPG, length `T` | common `T=128`, spatial 128; CUDA Mamba backend required |
| `RhythmFormer` | `RhythmFormerTrainer` / RhythmFormer | `N,T,C,H,W` | rPPG, length `T` | common `T=160`, spatial 128; `NDCHW` |

The loader's on-disk array is normally `D,H,W,C`. `DATA_FORMAT` changes the
individual tensor returned by the loader:

- `NDCHW` returns `D,C,H,W`. The frame-wise TSCAN, EfficientPhys, and DeepPhys
  trainers flatten the batch to `N*D,C,H,W`; their TSM groups require enough
  frames and truncate an incomplete group.
- `NCDHW` returns `C,D,H,W`, which collates to `N,C,D,H,W`. PhysNet,
  iBVPNet, FactorizePhys, PhysFormer, and PhysMamba consume this directly.
- `NDCHW` is also used by RhythmFormer because its forward begins with
  `N,D,C,H,W` and performs its own fusion/permute. BigSmall receives two
  streams from its specialized loader, not a normal single array.
- `NDHWC` is the preserved array layout used by unsupervised processing and is
  not a default for these neural trainers. Route that use case to the sibling
  skill instead of adding a silent transpose here.

## Model-specific facts

### PhysNet

The class is constructed with `MODEL.PHYSNET.FRAME_NUM` and returns the rPPG
trace plus three visual tensors; the trainer uses only the first output for the
loss and evaluation. Its temporal pooling/upsampling path is conventionally
used with a 128-frame chunk. Use a 3-D input with three video channels and keep
`DATA_TYPE`/`LABEL_TYPE` aligned with the checkpoint (the supplied examples use
`DiffNormalized`).

### iBVPNet

iBVPNet takes `frames` and `in_channels`. Its forward first differences time,
so the trainer appends a copy of the final frame before calling it. A normal
`T`-frame label therefore pairs with a `T+1` input and a `T`-sample output.
`CHANNELS: 1`, `3`, and `4` are implemented; 4 means RGB plus thermal, and the
loader's `IBVP.DATA_MODE` must agree (`RGB`, `RGBT`, or thermal-only as
supported by the selected cache). The representative configuration uses raw
input, not a precomputed diff channel.

### Tscan, EfficientPhys, and DeepPhys

All three use 2-D convolutions over a flattened temporal batch. TSCAN separates
six channels into first-three difference and last-three appearance inputs, then
uses temporal shift groups of `FRAME_DEPTH`. DeepPhys uses the same six-channel
motion/appearance convention but has no TSM group parameter. EfficientPhys
accepts a three-channel stream, computes a difference across the flattened
frame axis itself, and the trainer repeats one last frame to restore the label
length. Keep the spatial size among the implemented dense-layer sizes; TSCAN
also has a 128px branch, while EfficientPhys and DeepPhys do not have a 128px
branch in their constructors. Use complete temporal groups (commonly 10) and
verify that train and test chunk lengths produce the intended slicing.

### FactorizePhys

The trainer reads `FRAME_NUM`, `CHANNELS`, `TYPE`, `MD_FSAM`, `MD_TYPE`,
`MD_TRANSFORM`, `MD_S`, `MD_R`, `MD_STEPS`, `MD_INFERENCE`, and `MD_RESIDUAL`.
`TYPE` is `Standard` by default and selects `FactorizePhys`; `Big` selects
`FactorizePhysBig` and is intended for larger spatial inputs. The network also
differences time, so the trainer repeats the final frame. With `CHANNELS: 4`,
normalization splits RGB and thermal channels. `MD_TYPE: NMF` shifts features
nonnegative before factorization. When FSAM is enabled, training always returns
auxiliary factorization values; inference returns them when `MD_INFERENCE` is
true. Preserve matching FSAM flags between checkpoint creation and loading.

The current trainer contains a source-level caveat: it accesses
`FactorizePhys.TYPE`, `MD_TRANSFORM`, and other keys that older templates may
omit. The config defaults fill these keys, but a custom YAML should state them
explicitly. Do not “fix” shape errors by setting `strict=False`; it is used by
this trainer for some FactorizePhys loads and still requires an architecture
that is semantically compatible.

### BigSmall

BigSmall is the only listed multi-task model. Its specialized loader supplies a
large and a small stream. The current model is hard-coded around three-frame
segments, 12 AU outputs, one BVP output, and one respiration output. The common
preprocessing contract is big `144x144`, small `9x9`, `CHUNK_LENGTH: 3`, and
pseudo-PPG enabled with the exact misspelled key
`PREPROCESS.USE_PSUEDO_PPG_LABEL: true`. The trainer uses BCE-with-logits for
12 AUs and MSE for BVP/respiration, then applies sigmoid to AU logits at test.
It evaluates the BP4D+ AU subset and three folds; use the sibling data skill for
fold files and cache details.

Two current implementation hazards must be surfaced before a training run:
`BigSmallTrainer` calls `self.scheduler.get_last_lr()` but does not initialize a
scheduler, and its validation branch refers to `self.model_to_use` without
initializing it. Thus stock `train_and_test` can fail even when the model
constructs; repair this in a user-owned checkout by defining the intended
scheduler/model-selection policy, or use a known compatible checkpoint with
`only_test`. Do not silently claim that a source edit was made.

### PhysFormer and RhythmFormer

PhysFormer uses a 3-D stem, temporal center-difference layers, and a transformer
whose token reshape assumes spatial patching. The trainer constructs it from
`PATCH_SIZE`, `DIM`, `FF_DIM`, `NUM_HEADS`, `NUM_LAYERS`, `THETA`, chunk length,
and resize geometry. Representative defaults are patch 4, dim 96, FF dim 144,
4 heads, 12 layers, theta 0.7, 160 frames, and 128px input. It calls forward
with `gra_sharp=2.0` and combines Pearson and frequency-distribution losses.
Keep frame length divisible by the temporal patch and spatial dimensions
compatible with the three pooling stages and patch size.

RhythmFormer begins with a fusion stem that expects `N,D,C,H,W`, creates
spatio-temporal regions, and returns one rPPG trace. The model defaults are
frame 160 and image size `(160,128,128)`; its regional routing uses fixed
region divisibility and `attn_backend='torch'`. Its loss combines temporal
Pearson and frequency/heart-rate terms and receives the configured frame rate.
Do not feed it the `N,C,T,H,W` layout used by PhysFormer without intentionally
permuting the batch at the data boundary.

### PhysMamba

PhysMamba is a slow/fast 3-D temporal-difference network with `Mamba` blocks.
It imports `mamba_ssm` and `timm` at model import time and is not a CPU-safe
variant. Follow [mamba-backend.md](mamba-backend.md) before constructing it.
The regular input contract is three channels, `N,C,T,H,W`, commonly 128 frames
and 128px crops. Its trainer normalizes prediction and label signals before a
Pearson loss and does not provide a CPU substitute when the extension is absent.
