# Segmentation Config Catalog

This catalog distills public InternImage semantic segmentation config evidence from source labels under `segmentation/configs/**` and the segmentation README. Use these names as command arguments; do not reopen the original config files for operating instructions.

## Quick selection rules

- Use ADE20K for general 150-class scene parsing demos/evaluation. Palette: `ade20k`.
- Use Cityscapes for street-scene segmentation. Palette: `cityscapes`.
- Use COCO-Stuff configs for COCO-Stuff semantic labels. Palette: `cocostuff`.
- Mapillary, NYU-Depth-V2, and Pascal-Context are supported by configs and custom datasets, but the bundled image-demo palette choices inherited from the source parser are limited to `ade20k`, `cityscapes`, and `cocostuff`.
- Prefer smaller UperNet T/S/B configs when proving wiring. InternImage-L/XL/H/G and Mask2Former configs require substantially more memory and the DCNv3 CUDA runtime.
- A checkpoint should match the config family, dataset, resolution, head, and backbone size. Some Mask2Former single-scale/multi-scale config variants share one checkpoint name.

## Released config families

| Dataset | Config keys / relative config names | Head/backbone choices | Resolution / schedule | Reported signal from repo evidence | Notes |
| --- | --- | --- | --- | --- | --- |
| ADE20K | `ade20k/upernet_internimage_t_512_160k_ade20k` -> `configs/ade20k/upernet_internimage_t_512_160k_ade20k.py`<br>`ade20k/upernet_internimage_s_512_160k_ade20k` -> `configs/ade20k/upernet_internimage_s_512_160k_ade20k.py`<br>`ade20k/upernet_internimage_b_512_160k_ade20k` -> `configs/ade20k/upernet_internimage_b_512_160k_ade20k.py`<br>`ade20k/upernet_internimage_l_640_160k_ade20k` -> `configs/ade20k/upernet_internimage_l_640_160k_ade20k.py`<br>`ade20k/upernet_internimage_xl_640_160k_ade20k` -> `configs/ade20k/upernet_internimage_xl_640_160k_ade20k.py`<br>`ade20k/upernet_internimage_h_896_160k_ade20k` -> `configs/ade20k/upernet_internimage_h_896_160k_ade20k.py`<br>`ade20k/upernet_internimage_g_896_160k_ade20k` -> `configs/ade20k/upernet_internimage_g_896_160k_ade20k.py`<br>`ade20k/mask2former_internimage_h_896_80k_cocostuff2ade20k_ss` -> `configs/ade20k/mask2former_internimage_h_896_80k_cocostuff2ade20k_ss.py`<br>`ade20k/mask2former_internimage_h_896_80k_cocostuff2ade20k_ms` -> `configs/ade20k/mask2former_internimage_h_896_80k_cocostuff2ade20k_ms.py` | UperNet + InternImage T/S/B/L/XL/H/G; Mask2Former + InternImage-H | UperNet 512, 640, or 896 crop; 160k. Mask2Former 896 crop; 80k. | UperNet T through H: 47.9/48.1 to 59.9/60.3 mIoU ss/ms. Mask2Former-H: 62.6/62.9 mIoU ss/ms. | `upernet_internimage_g_896_160k_ade20k.py` exists in configs but was not in the main README release table. InternImage-G enables `with_cp=True` in evidence. |
| Cityscapes | `cityscapes/upernet_internimage_t_512x1024_160k_cityscapes` -> `configs/cityscapes/upernet_internimage_t_512x1024_160k_cityscapes.py`<br>`cityscapes/upernet_internimage_s_512x1024_160k_cityscapes` -> `configs/cityscapes/upernet_internimage_s_512x1024_160k_cityscapes.py`<br>`cityscapes/upernet_internimage_b_512x1024_160k_cityscapes` -> `configs/cityscapes/upernet_internimage_b_512x1024_160k_cityscapes.py`<br>`cityscapes/upernet_internimage_l_512x1024_160k_cityscapes` -> `configs/cityscapes/upernet_internimage_l_512x1024_160k_cityscapes.py`<br>`cityscapes/upernet_internimage_xl_512x1024_160k_cityscapes` -> `configs/cityscapes/upernet_internimage_xl_512x1024_160k_cityscapes.py`<br>`cityscapes/upernet_internimage_l_512x1024_160k_mapillary2cityscapes` -> `configs/cityscapes/upernet_internimage_l_512x1024_160k_mapillary2cityscapes.py`<br>`cityscapes/upernet_internimage_xl_512x1024_160k_mapillary2cityscapes` -> `configs/cityscapes/upernet_internimage_xl_512x1024_160k_mapillary2cityscapes.py`<br>`cityscapes/segformer_internimage_l_512x1024_160k_mapillary2cityscapes` -> `configs/cityscapes/segformer_internimage_l_512x1024_160k_mapillary2cityscapes.py`<br>`cityscapes/segformer_internimage_xl_512x1024_160k_mapillary2cityscapes` -> `configs/cityscapes/segformer_internimage_xl_512x1024_160k_mapillary2cityscapes.py`<br>`cityscapes/mask2former_internimage_h_1024x1024_80k_mapillary2cityscapes` -> `configs/cityscapes/mask2former_internimage_h_1024x1024_80k_mapillary2cityscapes.py` | UperNet T/S/B/L/XL; UperNet/SegFormer/Mask2Former variants trained with extra Mapillary data | 512x1024 160k for UperNet/SegFormer; 1024x1024 80k for Mask2Former-H | Direct Cityscapes UperNet: 82.58/83.40 to 83.68/84.41 mIoU ss/ms. Extra Mapillary variants: up to 86.37/86.96 mIoU ss/ms. | Extra-data configs have `mapillary2cityscapes` in the name; disclose this when comparing results. |
| COCO-Stuff-164K | `coco_stuff164k/mask2former_internimage_h_896_80k_cocostuff164k` -> `configs/coco_stuff164k/mask2former_internimage_h_896_80k_cocostuff164k.py` | Mask2Former + InternImage-H | 896 crop; 80k | 52.6/52.8 mIoU ss/ms | Use `cocostuff` palette for demo; checkpoint name matches the config stem. |
| COCO-Stuff-10K | `coco_stuff10k/mask2former_internimage_h_512_40k_cocostuff164k_to_10k` -> `configs/coco_stuff10k/mask2former_internimage_h_512_40k_cocostuff164k_to_10k.py` | Mask2Former + InternImage-H | 512 crop; 40k | 59.2/59.6 mIoU ss/ms | Name indicates COCO-Stuff-164K to 10K adaptation. |
| Mapillary | `mapillary/upernet_internimage_l_512x1024_80k_mapillary` -> `configs/mapillary/upernet_internimage_l_512x1024_80k_mapillary.py`<br>`mapillary/upernet_internimage_xl_512x1024_80k_mapillary` -> `configs/mapillary/upernet_internimage_xl_512x1024_80k_mapillary.py`<br>`mapillary/segformer_internimage_l_512x1024_80k_mapillary` -> `configs/mapillary/segformer_internimage_l_512x1024_80k_mapillary.py`<br>`mapillary/segformer_internimage_xl_512x1024_80k_mapillary` -> `configs/mapillary/segformer_internimage_xl_512x1024_80k_mapillary.py`<br>`mapillary/mask2former_internimage_h_896x896_80k_mapillary` -> `configs/mapillary/mask2former_internimage_h_896x896_80k_mapillary.py` | UperNet L/XL; SegFormer L/XL; Mask2Former-H | 512x1024 or 896x896; 80k | Released table gives parameters/FLOPs and training speed/time, not mIoU in the inspected README segment. | Uses custom `MapillaryDataset` with 66 classes and a repo-registered palette. Native `image_demo.py` cannot select `mapillary` as a palette choice. |
| NYU-Depth-V2 | `nyu_depth_v2/mask2former_internimage_h_480_40k_nyu` -> `configs/nyu_depth_v2/mask2former_internimage_h_480_40k_nyu.py` | Mask2Former + InternImage-H | 480 crop; 40k | 67.1/68.1 mIoU ss/ms | Uses custom `NYUDepthV2Dataset`, 40 classes, `reduce_zero_label=True`; native demo palette choices do not include NYU. |
| Pascal-Context-59 | `pascal_context/mask2former_internimage_h_480_40k_pascal_context_59` -> `configs/pascal_context/mask2former_internimage_h_480_40k_pascal_context_59.py` | Mask2Former + InternImage-H | 480 crop; 40k | 69.7/70.3 mIoU ss/ms | Uses `PascalContextDataset59` base config. Native demo palette choices do not include Pascal-Context. |

## Dataset base facts

| Dataset config label | Dataset type | Expected data root in config evidence | Crop size evidence | Demo palette choice |
| --- | --- | --- | --- | --- |
| `configs/_base_/datasets/ade20k.py` | `ADE20KDataset` | `data/ADEChallengeData2016` | `(512, 512)` | `ade20k` |
| `configs/_base_/datasets/cityscapes.py` | `CityscapesDataset` | `data/cityscapes/` | `(512, 1024)` | `cityscapes` |
| `configs/_base_/datasets/coco-stuff164k.py` | `COCOStuffDataset` | `data/coco_stuff164k` | `(512, 512)` | `cocostuff` |
| `configs/_base_/datasets/coco-stuff10k.py` | `COCOStuffDataset` | `data/coco_stuff10k` | `(512, 512)` | `cocostuff` |
| `configs/_base_/datasets/mapillary.py` | `MapillaryDataset` | `data/Mapillary/` | `(512, 1024)` | no native demo choice |
| `configs/_base_/datasets/mapillary_896x896.py` | `MapillaryDataset` | `data/Mapillary/` | `(896, 896)` | no native demo choice |
| `configs/_base_/datasets/nyu_depth_v2.py` | `NYUDepthV2Dataset` | `data/nyu_depth_v2/` | `(480, 480)` | no native demo choice |
| `configs/_base_/datasets/pascal_context_59.py` | `PascalContextDataset59` | `data/VOCdevkit/VOC2010/` | `(480, 480)` | no native demo choice |

Other inherited base dataset configs are present for medical, remote-sensing, and Pascal VOC variants, but they are not released InternImage segmentation model families in the inspected plan. Treat them as config inheritance evidence rather than primary operating targets unless the user explicitly asks for one.

## Architecture and optimizer facts that affect config choice

- UperNet configs replace the base backbone with `type='InternImage'` and set `decode_head` / `auxiliary_head` `num_classes` and `in_channels` to match the backbone width.
- Mask2Former configs use repo custom `EncoderDecoderMask2Former`, custom Mask2Former heads/losses/assigners, and pixel decoders; they are not plain MMSeg 0.27 components without `mmseg_custom` registration.
- Most released configs use AdamW with poly learning-rate policy and by-iteration checkpoints. Large configs often use gradient clipping with `max_norm=0.1`.
- Config comments explicitly recommend setting `with_cp=True` to save memory in large Mask2Former blocks. InternImage-G ADE20K evidence sets `with_cp=True` already.
- Pretraining is represented in configs through `init_cfg=dict(type='Pretrained', checkpoint=...)`; use `--load-from` or config edits carefully so it does not conflict with a task checkpoint used for evaluation.

## Checkpoint naming notes

- Released checkpoints are named after the model/config family in the `OpenGVLab/InternImage` release area. The command builder intentionally requires an explicit `--checkpoint` for test and demo to avoid guessing remote or local cache state.
- ADE20K Mask2Former single-scale and multi-scale configs have `_ss` and `_ms` suffixes, while the released checkpoint name observed in source evidence omits the scale suffix: `mask2former_internimage_h_896_80k_cocostuff2ade20k.pth`.
- For output comparisons, distinguish single-scale (`ss`) and multi-scale (`ms`) mIoU. `test.py --aug-test` turns on a fixed multi-scale/flip test pipeline for supported configs.
