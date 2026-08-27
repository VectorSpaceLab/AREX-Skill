# CVAT data preparation

## Input source types

| Source type | CLI/SDK value | Use when | Validation |
|---|---|---|---|
| Local | `local` / `ResourceType.LOCAL` | The client machine has files to upload. | Paths exist locally; archive/images are readable; upload size is acceptable. |
| Remote | `remote` / `ResourceType.REMOTE` | CVAT server should download URLs. | URLs must be reachable from the CVAT server, not just from the client. |
| Share | `share` / `ResourceType.SHARE` | Files are mounted in the CVAT server's share directory. | Paths are visible inside the CVAT deployment; use `copy_data` if needed. |
| Cloud storage | data params such as `cloud_storage_id` | Data lives in configured S3/Azure/GCS-like storage. | Storage belongs to the correct organization/workspace and credentials work. |

Task creation example:

```bash
cvat-cli --profile prod task create "images" --labels labels.json local image1.jpg image2.jpg
```

Python equivalent:

```python
from cvat_sdk.core.proxies.tasks import ResourceType

task = client.tasks.create_from_data(
    spec=task_spec,
    resource_type=ResourceType.LOCAL,
    resources=["image1.jpg", "image2.jpg"],
    data_params={"sorting_method": "natural", "image_quality": 70},
)
```

## Advanced data parameters

Common task data parameters include:

- `image_quality`: default compression quality for uploaded/processed images.
- `sorting_method`: `lexicographical`, `natural`, `predefined`, or `random`.
- `frame_step`: frame sampling step, converted to a server frame filter.
- `start_frame`, `stop_frame`: video frame range.
- `chunk_size`, `use_cache`, `use_zip_chunks`: chunk/cache behavior.
- `copy_data`: important for `share` resources.
- `filename_pattern`: filter data from a manifest or source pattern.
- `cloud_storage_id`: attach data from a configured cloud storage.
- `server_files_exclude`, `validation_params`, `job_file_mapping`: advanced server-side selection/validation.

## Manifests

CVAT manifests help with large image/video data, related images, deterministic sorting, and efficient data handling. The repo's utility can create manifests for image directories/globs or video files. In this generated skill, use the bundled `scripts/manifest_command_builder.py` to build the command safely:

```bash
python scripts/manifest_command_builder.py images ./images --output-dir ./manifest --sorting natural
python scripts/manifest_command_builder.py video ./video.mp4 --output-dir ./manifest --force
```

The builder prints a command shape. Execute the real manifest utility only in an environment where the manifest package dependencies and media codecs are installed. For video, `--force` may be needed when the video has too few keyframes for smooth decoding.

## DICOM and medical-image preparation

CVAT task uploads generally need ordinary image files. The source repository includes a DICOM-to-PNG conversion utility that recursively converts `.dcm` files to PNG and preserves relative directory structure. Treat this as a preprocessing step:

1. Install DICOM conversion dependencies in a separate data-preparation environment (`pydicom`, NumPy, Pillow, tqdm).
2. Convert a tiny representative sample first.
3. Check bit depth, photometric interpretation, multi-frame output naming, and whether normalization is clinically meaningful for the annotation task.
4. Upload the resulting PNG files to CVAT.

Do not run DICOM conversion blindly on sensitive medical data. Confirm de-identification, storage location, and audit requirements before creating derived images.

## Frame extraction

For targeted QA or debugging, use:

```bash
cvat-cli --profile prod task frames --outdir frames --quality compressed 42 0 10 20
```

SDK equivalent:

```python
task.download_frames([0, 10, 20], outdir="frames", quality="compressed")
```

Use `quality="original"` for pixel-sensitive ML checks; use `compressed` for lightweight visual review.

## Backup versus dataset export

- Use backups (`task backup`, `project backup`) for CVAT-to-CVAT restore.
- Use dataset exports (`COCO`, `YOLO`, `CVAT`, `Datumaro`, etc.) for ML training, external labeling tools, or cross-system conversion.
- Backups are not a substitute for a documented, model-compatible training dataset format.

## Pre-upload validation checklist

- Labels JSON is valid and contains expected names/types/attributes.
- Files exist and are not zero bytes.
- Videos use supported codecs and the desired frame range/step.
- Remote/share/cloud paths are reachable from the server side.
- Large uploads have an explicit chunk/cache plan.
- If related images are needed, manifest metadata contains those relationships.
- If annotations are imported, the archive layout and format name match exactly.
