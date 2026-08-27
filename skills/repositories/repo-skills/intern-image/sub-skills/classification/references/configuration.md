# Classification configuration and model-selection guide

Evidence labels distilled into this reference: `classification/config.py`, `classification/configs/**`, `classification/models/build.py`, `classification/models/intern_image.py`, `classification/models/intern_image_meta_former.py`, `classification/dataset/build.py`, and classification launch scripts.

## YACS merge and override behavior

The classification code uses a YACS `CfgNode` with these merge stages:

1. Load the requested `--cfg` YAML, recursively merging any non-empty `BASE` entries first.
2. Merge `--opts KEY VALUE ...` from the command line.
3. Apply explicit parser arguments such as `--batch-size`, `--dataset`, `--data-path`, `--zip`, `--cache-mode`, `--pretrained`, `--resume`, `--accumulation-steps`, `--use-checkpoint`, `--amp-opt-level`, `--output`, `--tag`, `--eval`, `--throughput`, `--save-ckpt-num`, and `--use-zero`.
4. Set `MODEL.NAME` from the config filename and set `OUTPUT` to `<output>/<model_name>`. Although the parser help mentions `<output>/<model_name>/<tag>`, the source code no longer appends `TAG` to the output path.

Because explicit parser flags are applied after `--opts`, a flag like `--batch-size 16` wins over an option such as `--opts DATA.BATCH_SIZE 32`.

The bundled command builder accepts repeated `--cfg-option KEY=VALUE` entries and converts them to `--opts KEY VALUE`.

## Core default groups

| Group | Important keys | Source default or behavior |
| --- | --- | --- |
| `DATA` | `BATCH_SIZE`, `DATA_PATH`, `DATASET`, `IMG_SIZE`, `INTERPOLATION`, `ZIP_MODE`, `CACHE_MODE`, `PIN_MEMORY`, `NUM_WORKERS`, `IMG_ON_MEMORY` | defaults are ImageNet, 224 px, batch size 128/GPU, bicubic interpolation, zip off, cache mode `part`, 8 workers |
| `MODEL` | `TYPE`, `NAME`, `PRETRAINED`, `RESUME`, `NUM_CLASSES`, `DROP_RATE`, `DROP_PATH_RATE`, `LABEL_SMOOTHING` | shipped YAML configs set `TYPE` to lowercase `intern_image` or `intern_image_meta_former`; using only the uppercase base default would not match the model builder |
| `MODEL.INTERN_IMAGE` | `DEPTHS`, `GROUPS`, `CHANNELS`, `LAYER_SCALE`, `OFFSET_SCALE`, `MLP_RATIO`, `CORE_OP`, `POST_NORM`, H/G special flags | most shipped configs use `CORE_OP: DCNv3`; H/G use clip-projector and post-norm variants |
| `TRAIN` | epochs, warmup, `BASE_LR`, `WEIGHT_DECAY`, `CLIP_GRAD`, `AUTO_RESUME`, `ACCUMULATION_STEPS`, `USE_CHECKPOINT`, optimizer, EMA, layer decay | main training scales LR by global batch size and accumulation; 22K-to-1K configs commonly use 20 epochs and checkpointing |
| `AUG` | color jitter, RandAugment, random erase, mixup/cutmix, mean/std | defaults are strong ImageNet augmentation with mixup 0.8 and cutmix 1.0 |
| `TEST` | `CROP`, `SEQUENTIAL` | center crop on by default; sequential sampler off by default |
| misc | `AMP_OPT_LEVEL`, `EVAL_MODE`, `THROUGHPUT_MODE`, `LOCAL_RANK`, `EVAL_22K_TO_1K`, `AMP_TYPE` | `main.py` asserts native AMP support when `AMP_OPT_LEVEL` is not `O0` |

## Config family catalog

Use this table to select a starting config label. File labels are provenance names, not instructions to open the source files.

| Config label | Intended model | Resolution | Key model settings | Training notes |
| --- | --- | --- | --- | --- |
| `configs/internimage_t_1k_224.yaml` | InternImage-T, IN-1K | 224 | channels 64, depths `[4,4,18,4]`, groups `[4,8,16,32]`, drop path 0.1 | base LR `5e-4`; default 300-epoch ImageNet setup |
| `configs/internimage_s_1k_224.yaml` | InternImage-S, IN-1K | 224 | channels 80, depths `[4,4,21,4]`, groups `[5,10,20,40]`, layer scale `1e-5`, post norm | base LR `5e-4` |
| `configs/internimage_b_1k_224.yaml` | InternImage-B, IN-1K | 224 | channels 112, depths `[4,4,21,4]`, groups `[7,14,28,56]`, layer scale `1e-5`, post norm | base LR `5e-4`; released top-1 source claim 84.9 |
| `configs/internimage_l_22kto1k_384.yaml` | InternImage-L fine-tuned from IN-22K | 384 | channels 160, depths `[5,5,22,5]`, groups `[10,20,40,80]`, offset scale 2.0, post norm | 20 epochs, checkpointing, layer decay 0.9 in the non-`without_lr_decay` family |
| `configs/internimage_xl_22kto1k_384.yaml` | InternImage-XL fine-tuned from IN-22K | 384 | channels 192, depths `[5,5,24,5]`, groups `[12,24,48,96]`, offset scale 2.0, post norm | 20 epochs, checkpointing; larger memory requirement |
| `configs/internimage_h_22kto1k_384.yaml` | InternImage-H fine-tuned from joint/22K | 384 | channels 320, depths `[6,6,32,6]`, groups `[10,20,40,80]`, `RES_POST_NORM`, `DW_KERNEL_SIZE: 5`, clip projector, level-2 post norm | 20 epochs, checkpointing, layer decay; use DeepSpeed/Accelerate for memory |
| `configs/internimage_h_22kto1k_640.yaml` | InternImage-H high-res IN-1K | 640 | same H backbone with 640 input | very memory-heavy; source memory table uses 8 GPUs with accumulation |
| `configs/internimage_g_22kto1k_512.yaml` | InternImage-G IN-1K | 512 | channels 512, depths `[2,2,48,4]`, groups `[16,32,64,128]`, clip projector, level-2 post norm block ids through 47 | extremely memory-heavy; source examples use 64 GPUs for training |
| `configs/inaturalist2018/internimage_h_22ktoinat18_384.yaml` | iNaturalist 2018 MetaFormer variant | 384 | `MODEL.TYPE: intern_image_meta_former`, H-like backbone, temporal/spatial metadata heads, `RAND_INIT_FT_HEAD` | dataset `inat18`, 100 epochs, 8,142 classes, checkpointing |
| `configs/without_lr_decay/*.yaml` | paper-reproduction ImageNet configs without LR layer decay | varies | mirrors corresponding non-subdirectory models | README states paper results used these configs; select these when reproducing released ImageNet claims |

## Model builder contract

`build_model(config)` accepts these model types:

- `intern_image`: builds `InternImage`.
- `intern_image_meta_former`: builds `InternImageMetaFormer`, used by iNaturalist 2018.

Both constructors receive most arguments from `MODEL.INTERN_IMAGE` plus `TRAIN.USE_CHECKPOINT` and `MODEL.DROP_PATH_RATE`:

```text
core_op, num_classes, channels, depths, groups, layer_scale, offset_scale,
post_norm, mlp_ratio, with_cp, drop_path_rate, res_post_norm,
dw_kernel_size, use_clip_projector, level2_post_norm,
level2_post_norm_block_ids, center_feature_scale, remove_center
```

`InternImage` returns classifier logits from either a convolutional classification head (T/S/B/L/XL style) or a clip-projector head (H/G style). `InternImageMetaFormer` accepts a tuple/list `(image, temporal_info, spatial_info)`, encodes temporal and spatial metadata, adds the metadata head logits to the image logits, and is therefore tied to iNaturalist metadata-bearing samples.

## Dataset builder facts

- `imagenet`: train split uses image paths under `DATA_PATH/train` when not evaluating; validation uses `DATA_PATH/val`; class count is 1,000.
- `imagenet22K`: train split uses `DATA_PATH` and source metadata; class count is 21,841. Validation uses a 1K mapping path.
- `inat18`: uses iNaturalist JSON annotations and location metadata; class count is 8,142; samples include image, temporal info, spatial info, and target.
- `ZIP_MODE` changes sampler behavior when combined with `CACHE_MODE=part`; it does not eliminate the need for the package's expected map/metadata files.
- Validation/test transforms resize/crop according to `DATA.IMG_SIZE`, `TEST.CROP`, and `DATA.INTERPOLATION`, then normalize with ImageNet mean/std defaults.

## Practical override patterns

Use command-builder `--cfg-option KEY=VALUE` for YACS paths that do not have a dedicated parser flag:

```bash
python scripts/build_classification_command.py \
  --mode train \
  --config configs/internimage_l_22kto1k_384.yaml \
  --data-path CHANGE_ME/imagenet \
  --gpus 8 \
  --batch-size 8 \
  --cfg-option TRAIN.EPOCHS=1 \
  --cfg-option PRINT_FREQ=1
```

Common keys:

- Memory: `TRAIN.USE_CHECKPOINT=True`, lower `DATA.BATCH_SIZE`, lower `DATA.NUM_WORKERS`, or move to DeepSpeed/Accelerate.
- Dataset: `DATA.DATASET=imagenet`, `DATA.DATASET=inat18`, `DATA.IMG_SIZE=384`.
- Evaluation: `TEST.SEQUENTIAL=True` when deterministic validation ordering matters more than distributed sampler parity.
- Model class count: prefer dataset-specific config; override `MODEL.NUM_CLASSES` only when adapting to a custom dataset and after replacing the classification head/checkpoint logic appropriately.
- Core op fallback experiments: `MODEL.INTERN_IMAGE.CORE_OP=DCNv3_pytorch` can target the Python implementation exposed by the package, but shipped configs use `DCNv3`; expect speed/memory changes and verify correctness before relying on metrics.

## Version and backend caveats

- Source installation text expects PyTorch >= 1.10, torchvision >= 0.9, timm 0.6.11, mmcv-full 1.5.0, mmdet 2.28.1, mmsegmentation 0.27.0, numpy < 2.0, pydantic 1.10.13, and yacs/pyyaml/scipy/opencv/termcolor.
- Real `main.py`/feature extraction execution calls CUDA APIs and DistributedDataParallel; parser/help checks alone do not prove model execution.
- The generated CPU-safe inspection environment did not install PyTorch/OpenMMLab/DCNv3/DeepSpeed/Accelerate/TensorRT, so those workflows are documented but not runtime-verified by this skill.
