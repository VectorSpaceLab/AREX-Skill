# Dataset Troubleshooting

## Purpose

Use this reference when a dataset reader cannot find the source files or the
transform command fails on layout or annotation issues.

| Symptom or error fragment | Likely cause | Recovery |
| --- | --- | --- |
| `InvalidDataDirectory` or `"..." does not exist` | The `--data-dir` path is wrong or the split directory is missing | Verify the dataset root and split names before rerunning the transform. |
| `CSV annotation file not found` | A CSV reader is pointed at a layout that does not have `{split}.csv` | Create the expected CSV file or switch to the correct reader type. |
| `Image directory not found` | A CSV reader cannot find the `{split}/` image folder | Move the images under the split folder or change the source layout. |
| `Columns missing from CSV` | The CSV header or override columns do not match the expected schema | Fix the header or pass `--override headers=false --override columns=image_id,xmin,ymin,xmax,ymax,label`. |
| `Could not find any annotations` | The split directory is empty or the annotation suffix is wrong | Confirm that the split folder contains annotation files with the expected extension. |
| `Record should have at least one \`gt_boxes\`` | The source annotation file parsed, but it produced no valid boxes | Check the label whitelist, coordinate names, and class filtering options. |
| OpenImages label or annotation files are missing | The OpenImages metadata CSVs are not in the expected place | Download the required CSV metadata and confirm the split directory names. |
| The class counts are not exact when using `--class-examples` | The reader stops heuristically, not by exact count | Use `--limit-examples` for exact truncation or inspect the output counts after transform. |

## Recovery workflow

1. Run `python scripts/validate_dataset_layout.py ...` against the candidate
   layout.
2. Fix the directory or annotation schema until the checker reports success.
3. Re-run `lumi dataset transform` with the same `--type`, `--split`, and any
   needed `--override` values.
4. If the problem is not layout-related, route the next step to training,
   checkpoints, or prediction instead of continuing to tweak the reader.

## Useful reminders

- `--only-classes` expects a comma-separated list.
- `--split` may be passed more than once.
- `openimages` is the most environment-sensitive reader because it depends on
  the external OpenImages metadata and access to the image bucket.
