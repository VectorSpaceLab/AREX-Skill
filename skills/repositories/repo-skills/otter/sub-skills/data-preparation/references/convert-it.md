# Convert-It adapter reference

Convert-It is the image-source conversion layer behind MIMIC-IT. It converts public image/video sources into an image JSON mapping image id to base64 image bytes. The JSON should then be converted to parquet before large Otter training jobs.

This reference captures adapter ids, expected inputs, and output filenames so a future agent can plan a conversion without opening source files.

## Adapter table

| Adapter id | Source task | Required input path(s) | Expected output JSON |
|---|---|---|---|
| `2d.Llava` | LLaVA-In-Context / COCO images | `image_path`: metadata JSON whose keys are COCO image ids; `image_root`: COCO train image folder containing `<id>.jpg` | `output/LA.json` |
| `video.DenseCaptions` | Dense Captions / ActivityNet videos | `image_path`: directory containing many `.mp4` files | `output/DC.json` |
| `video.VisualStoryTelling` | Visual Storytelling | `image_path`: `train.story-in-sequence.json` style metadata | `output/VST.json` |
| `video.TVCaptions` | TV Captions frames | `image_path`: extracted frame root with show subfolders such as `bbt_frames`, `castle_frames`, `house_frames`, `met_frames` | `output/TVC.json` |
| `3d.SceneNavigation` | ScanNet scene navigation | `image_path`: ScanNet/scannet-frames style directory with scene folders and color frames | `output/SN.json` |
| `change.SpotTheDifference` | Spot-the-Difference subtle difference | `image_path`: directory of paired images, e.g. `<id>.jpg` and `<id>_2.jpg` | `output/SD.json` |
| `change.CocoGeneralDifference` | COCO general-difference images | `image_path`: COCO image directory | `output/CGD.json` |
| `fpv.EGO4D` | EGO4D egocentric videos | `image_path`: directory of video files | `output/E4D.json` |

Note: older documentation may refer to TV Captions output as `TV.json`; the adapter short name in the inspected code path is `TVC`, so current output should be treated as `output/TVC.json` unless a wrapper reports otherwise.

## Output contract

The converter emits one JSON object:

```json
{
  "IMAGE_ID_000001": "base64-encoded-image-bytes",
  "IMAGE_ID_000002": "base64-encoded-image-bytes"
}
```

The instruction JSON for the matching task must use the same ids in each record's `image_ids` list. For training, prefer converting this image JSON to parquet:

```bash
python ../scripts/convert_base64_json_to_parquet.py output/LA.json output/LA.parquet --validate-sample 8
```

Then point the MIMIC-IT YAML `images_path` at the parquet output.

## Planning checklist

1. Confirm that the user has rights to access and process the source dataset.
2. Confirm the input layout for the chosen adapter. Many adapters assume a very specific folder structure.
3. Estimate disk usage. Video adapters extract or encode many frames; outputs can be much larger than metadata files.
4. Use a bounded `num_threads` value. Very high thread counts can exhaust memory or file descriptors when videos/images are large.
5. Treat the generated JSON as an intermediate. Convert to parquet and validate id linkage before training.
6. Keep logs for missing media. The Spot-the-Difference adapter records missing pairs; other adapters may print and continue on bad items.

## Adapter-specific notes

### `2d.Llava`

- Reads image ids from a metadata JSON.
- Opens `${image_root}/${image_id}.jpg` for every key.
- Requires both metadata and image root; missing image files fail conversion.

### `video.DenseCaptions`

- Scans `.mp4` files and frames each video.
- Expects more than 100 videos; a small fixture may be rejected by the adapter's dataset-size guard.
- Image ids are generated from video name plus zero-padded frame index.

### `video.VisualStoryTelling`

- Reads story metadata and downloads or resolves image entries through the adapter utility.
- Requires network or pre-accessible images depending on how the metadata is populated.

### `video.TVCaptions`

- Samples frames from extracted TVQA frame directories.
- Current output short name is `TVC`.

### `3d.SceneNavigation`

- Uses scene-navigation utilities to process ScanNet-style scene folders.
- Validate that scene folder names and color frame subfolders match the expected layout before a full run.

### `change.SpotTheDifference`

- Pairs each base id with a second image suffixed `_2`.
- Writes a missing-file log when pairs are incomplete.

### `change.CocoGeneralDifference`

- Reads all files in an image directory and uses each basename as the image id.
- Useful for generated general-difference instruction tasks where image ids match COCO basenames.

### `fpv.EGO4D`

- Frames every video in the supplied directory.
- Outputs ids using video basename and zero-padded frame index.

## Handoff to MIMIC-IT YAML

After conversion:

1. Convert image JSON to parquet.
2. Put the instruction JSON and optional train config JSON in stable locations.
3. Add a dataset entry under the correct group.
4. Run [validate_mimicit_yaml.py](../scripts/validate_mimicit_yaml.py) with `--check-records` and, for multimodal groups, `--check-image-links`.
5. Route actual training to [training](../../training/SKILL.md).
