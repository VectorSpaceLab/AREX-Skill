# Data Preparation Workflows

## When to Read

Read this when preparing benchmark data, training data, JSON indexes, or heavy crop preprocessing for SiamMask.

## General Order

1. Confirm the environment and build extensions from the root skill.
2. Obtain raw data only after network/disk approval.
3. Run layout checks before preprocessing to avoid long jobs with wrong paths.
4. Generate crops and JSON indexes.
5. Re-run layout checks and only then launch tracking or training workflows.

## Benchmark Data Preparation

### VOT

- Obtain VOT dataset directories with `list.txt`, per-video `groundtruth.txt`, and frames.
- Generate metadata JSON when needed:

  ```bash
  python scripts/generate_vot_json.py \
    --dataset-root <siammask-checkout>/data/VOT2019 \
    --dataset-name VOT2019 \
    --output <siammask-checkout>/data/VOT2019.json
  ```

- Validate:

  ```bash
  python scripts/check_dataset_layout.py --data-root <siammask-checkout>/data --dataset vot --strict
  ```

### DAVIS and YouTube-VOS

- DAVIS needs the shared `DAVIS` directory with `ImageSets`, `JPEGImages`, and `Annotations`.
- YouTube-VOS benchmark evaluation needs the validation `meta.json`, images, and masks.
- Validate with `--dataset davis` or `--dataset ytb_vos` before tracking.

## Training Data Preparation Order

Training configs require COCO, DET, VID, and YouTube-VOS crop/index outputs. The original preprocessing is expensive and dataset-specific. Use the dry-run launcher to audit commands first:

```bash
python scripts/run_data_prep.py --repo-root <siammask-checkout> --list
python scripts/run_data_prep.py --repo-root <siammask-checkout> coco-crop -- --enable_mask --num_threads 24
python scripts/run_data_prep.py --repo-root <siammask-checkout> coco-json
```

Add `--run` before the entry name only after confirming raw data exists and runtime is approved:

```bash
python scripts/run_data_prep.py --repo-root <siammask-checkout> --run coco-crop -- --enable_mask --num_threads 24
```

Recommended training-data sequence:

1. COCO: build pycocotools, crop image/mask samples, generate train/val JSON indexes.
2. ImageNet DET: unpack raw DET data, crop detection images, generate `train.json`.
3. ImageNet VID: parse raw VID annotations to `vid.json`, crop video frames, generate `train.json` and `val.json`.
4. YouTube-VOS: parse annotations to instance JSONs, crop frames/masks, generate `train.json`.
5. Run `check_dataset_layout.py --dataset training` and inspect missing paths.

## Source-Workflow Safety Classification

- Download helpers and raw-dataset acquisition: network and large-disk side effects; do not run without approval.
- Crop helpers: local CPU/multiprocessing workloads; can run for minutes to hours and generate large `crop511` trees.
- JSON generators: local deterministic file writes; safer, but still use explicit output locations or dry-run launcher.
- Visualization helpers: OpenCV GUI; avoid on headless machines.

## Handoff to Other Sub-Skills

- After VOT/DAVIS/YouTube-VOS benchmark data is ready, use the tracking sub-skill to compose test/eval/tune runs.
- After all training data checks pass, use the training sub-skill to dry-run CUDA training commands.
