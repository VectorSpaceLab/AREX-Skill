# Data Preparation Troubleshooting

## `list.txt` or `groundtruth.txt` missing for VOT

The VOT metadata generator requires a dataset directory with `list.txt`, per-video `groundtruth.txt`, and frame images.

Recovery:

- Validate with `check_dataset_layout.py --dataset vot`.
- Regenerate metadata only after raw VOT folders are complete.
- For VOT2018/2019 tags, missing tag files are tolerated and produce empty tag lists where absent.

## DAVIS paths are missing

SiamMask expects a shared `DAVIS` directory and year-specific `ImageSets` files.

Recovery:

- Confirm `DAVIS/ImageSets/2016/val.txt` and/or `DAVIS/ImageSets/2017/val.txt`.
- Confirm `JPEGImages/480p` and `Annotations/480p` match video names.
- Add compatibility symlinks only when the user approves filesystem mutation.

## YouTube-VOS parsing is slow or fails

Likely causes:

- Raw `meta.json`, images, or masks are incomplete.
- Google Drive/download permissions changed.
- OpenCV contour return signatures differ across versions.

Recovery:

- Validate raw layout before parsing.
- Treat network/download failures as data acquisition issues, not code failures.
- Keep parsed JSON generation separate from crop generation so partial progress can be inspected.

## COCO pycocotools cannot import `_mask`

Cause: local pycocotools extension was not built for the active Python.

Recovery:

```bash
bash ../../scripts/build_extensions.sh --repo-root <siammask-checkout> --python <python-in-your-env>
```

If building from the data-preparation sub-skill directory, adjust the helper path to the root skill's `scripts/build_extensions.sh`.

## Crop preprocessing runs too long or fills disk

Crop helpers create large `crop511` directories and may use many worker processes.

Recovery:

- Dry-run the command with `run_data_prep.py` first.
- Lower thread/worker counts.
- Ensure output paths are inside the intended data root.
- Stop and ask before deleting or overwriting existing generated crops.

## Training config reports missing `root` or `anno`

Cause: training configs reference generated crop/index outputs that do not yet exist.

Recovery:

1. Run `check_dataset_layout.py --dataset training`.
2. Prepare the missing dataset family from raw data.
3. Re-run the training helper dry-run and confirm all referenced roots/annotations exist.

## Exact original download script requires system packages or sudo

The original test-data acquisition used external tools and system dependencies. Do not run package-manager commands, sudo, git clone, or network downloads without explicit user approval. Prefer checking whether data already exists, then ask before acquisition.

## Visualization scripts do nothing or crash

Data visualization helpers use OpenCV GUI windows. On headless machines, rely on file/directory checks and small image-load probes instead of visualization.
