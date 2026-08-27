# SimpleDet data-preparation troubleshooting

This reference lists the failures that most often come from dataset layout or
annotation shape rather than from the detector graph.

## Missing annotations or images

### Symptom

- The converter asserts that an annotation file does not exist.
- The validator says `image_url` is missing on disk.
- A later loader cannot open the image path.

### Likely cause

- The directory tree does not match the converter's expected split naming.
- You are running from a different working directory than the paths stored in
  `image_url`.
- A symlink points to a missing target.

### Fix

- Re-check the split-specific layout in `references/data-formats.md`.
- Run the validator with `--check-images` from the same working directory used
  by the later training or evaluation command.
- Prefer absolute `image_url` values when the data will move between machines.

## Bad labels

### Symptom

- A class id is `0` or another unexpected negative value.
- A class name in VOC is not found in the label map.
- COCO category ids look shifted by one.

### Likely cause

- Background was written into `gt_class` instead of being reserved.
- CrowdHuman ignore boxes were remapped to another label.
- The label map does not match the annotation file.
- The COCO category order changed, so the contiguous train ids changed too.

### Fix

- Keep foreground classes 1-based and leave background at `0`.
- Keep CrowdHuman ignore boxes as `-2`.
- Verify the label map keys exactly match the XML class names.
- For COCO-like JSON, check the category list before conversion and keep the
  intended order stable.

## Malformed XML, JSON, or ODGT

### Symptom

- XML parsing fails.
- JSON loading fails or a record is not a dict.
- CrowdHuman line parsing fails on one record.

### Likely cause

- The file is truncated.
- A field is misspelled or missing.
- The source file is JSONL when the converter expects a JSON list.
- A CrowdHuman line is not valid JSON.

### Fix

- Inspect the offending record in a small fixture.
- Use the validator on the first few lines only if you are debugging a huge
  source file.
- Make the source format match the converter exactly before retrying.

## Empty records

### Symptom

- A record has no boxes.
- A whole split seems to contain only empty annotations.

### Likely cause

- The annotation filter was too aggressive.
- The source file contains only images but no valid boxes.
- Every box was clipped or dropped during conversion.

### Fix

- Check the source annotations before conversion.
- Use the validator summary to confirm whether the split has any valid boxes at
  all.
- If the dataset is meant to contain negative images, keep them; if not, fix the
  upstream annotation filter.

## Bbox clipping and invalid geometry

### Symptom

- Boxes are clipped to image borders.
- The validator reports `x2 < x1` or `y2 < y1`.
- The converter silently drops some COCO boxes.

### Likely cause

- The source annotation uses a different bbox convention.
- The source file contains zero-area or negative-area boxes.
- The original box extends beyond the image bounds.

### Fix

- Keep xyxy coordinates in the roidb, not xywh.
- Confirm that COCO xywh boxes are converted through the repo helper rather than
  manually reinterpreted.
- Fix degenerate boxes upstream if they should not exist.

## Symlink and layout issues

### Symptom

- An annotation file is readable, but every image lookup fails.
- A dataset works only when run from one specific directory.

### Likely cause

- A symlink target is broken.
- The converter stored relative paths that only resolve from a different working
  directory.
- The dataset root was copied without preserving symlinks.

### Fix

- Recreate the symlinks or switch to absolute paths.
- Run the validator from the same directory that later training will use.
- Avoid moving a prepared dataset tree without checking every `image_url`.

## COCO category mapping surprises

### Symptom

- The model trains, but the class ids do not line up with the labels you
  expected.

### Likely cause

- The converter remapped COCO categories to contiguous training ids.
- The original category ids were not the same as the train ids.

### Fix

- Check the categories in the source JSON before conversion.
- Treat the remapped train ids as the only ids the model sees.
- If you need a custom category order, make that order explicit in the source
  JSON and keep it stable.

## Mask polygon failures

### Symptom

- `PreprocessGtPoly` or `EncodeGtPoly` fails.
- A mask config complains about polygons.
- A COCO instance has segmentation data, but the mask path still breaks.

### Likely cause

- The segmentation is an RLE/dict rather than a polygon list.
- One polygon has an odd number of coordinates or fewer than 6 values.
- `gt_poly` length does not match `gt_class` length.
- `PadParam.max_len_gt_poly` is too small for the encoded representation.

### Fix

- Keep raw polygon lists for mask workflows.
- Convert or drop RLE-only instances before writing the roidb.
- Check the number of polygons and coordinates in one tiny fixture first.
- Increase the padding length only after you confirm the encoding size.

## Validator says NumPy is unavailable

### Symptom

- The validator refuses to open a pickle roidb.

### Likely cause

- Pickle loading needs NumPy to reconstruct stored arrays.

### Fix

- Install NumPy in the validation environment, or validate a JSON/JSONL record
  file instead.
- If the source is a pickle roidb, do not expect a pure-stdlib fallback to read
  NumPy arrays safely.

## Deferred loader smoke test fails

### Symptom

- A later loader smoke check fails after the data-prep checks pass.

### Likely cause

- The cache shape is valid, but the loader or aspect grouping still has a data
  edge case.

### Fix

- Keep the prepared tiny fixture and inspect the loader failure separately.
- Hand off to the detector workflow or the setup/operations workflow depending
  on whether the issue is data-shape or environment-related.

## When to stop here

If the cache is structurally valid but model execution still fails, the next
route is not more data-prep work. Move to the detector workflow for config and
launch handling, or to setup-and-operations for environment repair.
