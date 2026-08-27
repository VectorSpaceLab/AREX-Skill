# Data-preparation workflows

## File / OSS helpers

The public `easycv.file.io` helpers cover the common data-moving operations:

- `access_oss(...)`
- `open(...)`
- `exists(...)`
- `move(...)`
- `copy(...)`
- `copytree(...)`
- `listdir(...)`
- `remove(...)`

Use them when a workflow needs to work on both local and OSS paths.

## Repo-maintained preparation helpers

The installed package includes the `tools/prepare_data` module tree. Common helpers include:

- `prepare_nuscenes.py`
- `prepare_market1501.py`
- `crowdhuman2coco.py`
- `mot2coco.py`
- `convert_det_itag2raw.py`
- `create_voc_data_files.py`
- `create_voc_low_shot_challenge_samples.py`
- `coco_stuff164k.py`

## When to use each helper

| Helper | Typical use |
| --- | --- |
| `prepare_nuscenes.py` | Generate nuScenes info files and related annotation metadata. |
| `prepare_market1501.py` | Build the standard ReID splits. |
| `crowdhuman2coco.py` | Convert CrowdHuman annotations into COCO-style data. |
| `mot2coco.py` | Convert MOT-style annotations into COCO-style data. |
| `convert_det_itag2raw.py` | Convert iTAG detection annotations into raw labels. |
| `create_voc_data_files.py` | Build VOC file lists and split files. |
| `create_voc_low_shot_challenge_samples.py` | Produce low-shot VOC samples. |
| `coco_stuff164k.py` | Convert COCO-Stuff masks into training-ready format. |

## Preparation workflow

1. Pick the dataset family and its expected layout.
2. Decide whether you need conversion, split generation, or OSS path setup.
3. Run the smallest helper that produces the exact missing artifact.
4. Validate the output files before launching training or prediction.

## Good practice

Keep conversion helpers separate from training configs. A prepared dataset should be reusable by multiple configs without rewriting the helper.

