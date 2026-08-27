# Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ROOT_PATH` or `REPO_ROOT_PATH` still appears in a list file | Placeholder paths were copied from the example tree | Rewrite the paths to real dataset locations or rerun the TFRecord wrapper with a real `--data-dir`. |
| `Source image data is not complete` | One of `gt_image/`, `gt_binary_image/`, or `gt_instance_image/` is missing | Stage the prepared dataset so the three `gt_*` folders sit beside the list files. If you started from the shipped example tree, rename or restage `image/` to `gt_image/`. |
| `train.txt`, `val.txt`, or `test.txt` is missing | The producer has not generated the split files yet | If all three `gt_*` folders exist, rerun TFRecord generation and let `LaneNetDataProducer` auto-split. |
| Only some list files exist | A partial custom split is being reused | Delete the stale list trio first if you want the producer to regenerate all three files together. |
| A list row has the wrong number of columns or mismatched basenames | The list was edited by hand or generated from the wrong folder | Regenerate the lists from the prepared `gt_image/` tree and keep every row in `<image> <binary> <instance>` order. |
| `cv2.imread(...)` returns `None` or `cv2.imwrite(...)` fails | Corrupt input, missing raw frame, or unwritable output directory | Fix the offending PNG/JPG, verify the `raw_file` path, and confirm the destination directory is writable. |
| TensorFlow writer/import errors | Wrong TensorFlow/protobuf combo or running outside the repo-root config context | Use TensorFlow 1.15 with `protobuf<=3.20.x`, run from the repository root, and keep `PYTHONPATH` pointed at the repo when validating with repo modules. |
| TFRecord decode/shape problems | Stale TFRecords, bad crop size assumptions, or inconsistent list contents | Delete old `tfrecords/` outputs, confirm the intermediate resize is `544 x 288`, and rebuild the split files from the prepared dataset root. |
| Feeder returns no useful batches | Dataset is too small for the default batch size | Reduce `TRAIN.BATCH_SIZE` and `VAL_BATCH_SIZE`, or expand the dataset before generating TFRecords. |

## Fast recovery checklist

1. Confirm the dataset root contains `gt_image/`, `gt_binary_image/`, and `gt_instance_image/`.
2. Confirm the three list files are either all present or all absent.
3. Confirm no placeholder strings remain in the list rows.
4. Rebuild TFRecords after deleting stale output files if the layout changed.
