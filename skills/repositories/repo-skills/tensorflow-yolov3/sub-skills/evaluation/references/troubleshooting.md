# Troubleshooting

## 1) `evaluate.py` removed my output directory

Cause: the script calls `shutil.rmtree` on `./mAP/predicted`, `./mAP/ground-truth`, and `cfg.TEST.WRITE_IMAGE_PATH` before recreating them.

Fix: point `cfg.TEST.WRITE_IMAGE_PATH` at a scratch directory and do not keep anything important in the mAP output folders.

## 2) `cv2.imread(...)` returns `None`

Cause: the image path in `cfg.TEST.ANNOT_PATH` is wrong or the file is not readable from the current working directory.

Fix: confirm each annotation row starts with a real image path and that the file exists.

## 3) Predictions look plausible but the class names are wrong

Cause: `cfg.YOLO.CLASSES` does not match the class order used when the checkpoint was trained.

Fix: restore the same class-name file that was used during training, then rerun evaluation.

## 4) `mAP/main.py` says `No ground-truth files found!` or `File not found: predicted/<id>.txt`

Cause: you ran the evaluator from the wrong directory, or the file stems do not match.

Fix:

- run `cd mAP && python main.py ...`, and
- if the stems are inconsistent, use `intersect-gt-and-pred.py` or regenerate the pair with `evaluate.py`.

## 5) `File ... in the wrong format`

Cause: the line token count does not match the parser contract.

Fix:

- ground-truth: `class left top right bottom` or `class left top right bottom difficult`
- predicted: `class confidence left top right bottom`
- normalize multi-word class names before evaluation
- remove custom delimiters before evaluation

## 6) `--set-class-iou` fails

Cause: the flag must be written as alternating class / IoU pairs, and each IoU value must be strictly between `0.0` and `1.0`.

Fix:

```bash
python main.py -na -np -q --set-class-iou person 0.75 bicycle 0.60
```

## 7) Headless environment failures

Cause: animation or plotting dependencies are missing.

Fix: keep `-na -np` enabled so `mAP/main.py` stays in text-only mode.

## 8) `map_fixture_check.py` fails its perfect-match case

Cause: the text schema or AP expectation changed.

Fix: inspect the fixture output first; the checker is designed to be self-contained and should not depend on the repo's source checkout.

## 9) `results/` or `tmp_files/` disappeared after a run

Cause: that is normal. `mAP/main.py` recreates `results/` and removes `tmp_files/` at the end.

Fix: copy the files you need before starting another evaluation.
