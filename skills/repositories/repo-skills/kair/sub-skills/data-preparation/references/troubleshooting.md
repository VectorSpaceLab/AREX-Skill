# KAIR data-preparation troubleshooting

Use this when a KAIR training or testing workflow cannot find data, pairs do not align, meta-info fails, or preparation scripts refuse to run.

## Empty dataset or no images found

Symptoms:

- A test script reports no dataset, no images, or produces zero folders.
- A dataset length is zero.
- `main_test_vrt.py` or `main_test_rvrt.py` appears to run but finds no frames.

Likely causes and checks:

1. Wrong folder depth. Generic video test datasets expect `root/clip/frame.ext`, not a flat `root/frame.ext` folder. Vimeo90K expects `root/clip/sequence/im1.png` through `im7.png`.
2. Wrong command root. For REDS4 VSR, `--folder_lq` should point at `testsets/REDS4/sharp_bicubic`, not at `testsets/REDS4` or an individual frame folder.
3. Hidden or unsupported files. KAIR scanners ignore hidden entries and image readers expect real image files.
4. Extra scale directory. If frames are under `sharp_bicubic/X4/000/...` but the command points at `sharp_bicubic`, the immediate subfolder is `X4`, not the clip id. Point at `sharp_bicubic/X4` or restructure.
5. Meta-info selects missing folders. If `meta_info_file` is provided, only listed first tokens are used.

Read-only checks:

```bash
python sub-skills/data-preparation/scripts/check_dataset_layout.py image --root trainsets/trainH
python sub-skills/data-preparation/scripts/check_dataset_layout.py video --root testsets/REDS4/sharp_bicubic --paired-root testsets/REDS4/GT
python sub-skills/data-preparation/scripts/check_dataset_layout.py video --root testsets/vimeo90k/vimeo_septuplet/sequences --layout vimeo --meta-info data/meta_info/meta_info_Vimeo90K_test_GT.txt
```

## LQ/GT count mismatch

Symptoms:

- `AssertionError: Different number of images in lq ... and gt folders ...`.
- Metrics are missing or wrong because outputs cannot be paired.

Fixes:

1. Compare clip folder names in LQ and GT roots.
2. Compare frame counts per clip.
3. Confirm frame sorting and filename templates. REDS uses eight digits, DVD often five, GoPro six.
4. For SR datasets, account for naming suffixes such as `x4` in LQ names when checking image pairs.
5. For Vimeo90K, ensure every listed sequence has `im1.png` through `im7.png` in both clean and LR trees.

Read-only checks:

```bash
python sub-skills/data-preparation/scripts/check_dataset_layout.py video --root testsets/DVD10/test_GT_blurred --paired-root testsets/DVD10/test_GT
python sub-skills/data-preparation/scripts/check_dataset_layout.py image --root testsets/Set5/LR_bicubic/X4 --paired-root testsets/Set5/HR --pair-strategy stem-loose
```

## Existing output folder exits

Symptoms:

- A subimage or LMDB conversion exits immediately with a message like `Folder ... already exists. Exit.`

Cause:

- KAIR's source subimage and LMDB helpers intentionally stop when the target folder already exists to avoid overwriting data.

Fixes:

1. Do not delete an existing output blindly.
2. Inspect whether it is complete: count files, check `data.mdb`, `lock.mdb`, and `meta_info.txt` for LMDBs.
3. If regenerating, move the old output aside or choose a new target path.
4. Re-run a writer only after the new target is empty and the source path/key plan is confirmed.

## Destructive move/copy scripts

Symptoms:

- Original GoPro/DVD/UDM10 clip folders disappear after preparation.
- REDS validation folders are duplicated into the train tree.

Cause:

- Some source helpers use `shutil.move`, `shutil.rmtree`, or shell `cp -r`.

Safe handling:

1. Work on a disposable copy or backed-up dataset tree.
2. Print or document the exact old and new tree before running any mover.
3. Use the bundled checker after regrouping.
4. Keep destructive steps separate from LMDB conversion so failures are easier to recover.

## Missing `meta_info_file`

Symptoms:

- Training fails with file-not-found for `meta_info_file`.
- Video training produces no keys or errors while parsing meta-info.

Fixes:

1. Confirm the path in the training config is relative to the user's KAIR checkout.
2. Use the proper format:
   - REDS/DVD/GoPro/DAVIS training: `<clip> <frame_count> (<h>,<w>,<c>) <start_frame>`.
   - Vimeo90K: `<clip>/<sequence> 7 (<h>,<w>,<c>)`.
3. Confirm each first token corresponds to an actual clip folder or LMDB key prefix.
4. Confirm `start_frame` width matches `filename_tmpl`: `00000000` for `08d`, `00000` for `05d`, `000001` for `06d`.

Read-only check:

```bash
python sub-skills/data-preparation/scripts/check_dataset_layout.py meta --meta-info data/meta_info/meta_info_REDS_GT.txt --root trainsets/REDS/train_sharp
```

## LMDB already exists or has wrong keys

Symptoms:

- Conversion refuses to run because the `.lmdb` folder exists.
- Training cannot fetch keys even though `data.mdb` exists.
- REDS or Vimeo training fails after conversion.

Likely causes:

1. Target `.lmdb` already exists; KAIR exits by design.
2. The LMDB was created from the wrong source root, causing keys to include an extra path component such as `X4/000/00000000`.
3. Vimeo GT LMDB contains only `im4` keys but the config expects all frames.
4. `meta_info.txt` is missing or inconsistent with generated keys.

Fixes:

1. Inspect the LMDB folder with the read-only checker:

   ```bash
   python sub-skills/data-preparation/scripts/check_dataset_layout.py lmdb --root trainsets/REDS/train_sharp_with_val.lmdb
   ```

2. Generate a fresh plan:

   ```bash
   python sub-skills/data-preparation/scripts/plan_lmdb_conversion.py --dataset reds
   python sub-skills/data-preparation/scripts/plan_lmdb_conversion.py --dataset vimeo90k
   ```

3. Regenerate into a new target folder only after confirming source root and key convention.

## Libpng read fallback

Symptoms:

- OpenCV reports a PNG read failure or `libpng error: Read Error` during LMDB creation.

KAIR's LMDB image worker attempts a PIL fallback when OpenCV returns `None`. If this happens:

1. Treat the image as suspicious; inspect or replace it if possible.
2. Do not ignore repeated failures across many files.
3. Consider validating all images with a small PIL/OpenCV scan before starting a long LMDB conversion.

## Multiprocessing memory pressure

Symptoms:

- LMDB conversion is killed by the OS.
- The machine swaps heavily or stalls while reading images.

Cause:

- KAIR's LMDB helper can read all images into memory when `multiprocessing_read=True`.

Fixes:

1. Disable multiprocessing read for constrained machines.
2. Reduce worker count.
3. Use smaller batches or split conversion by dataset family.
4. Avoid running subimage extraction and LMDB conversion concurrently.

## `dataset_type` is not found

Symptoms:

- `Dataset [x] is not found.`

Fixes:

1. Check `references/data-layouts.md#dataset_type-mapping`.
2. Use lowercase or one of KAIR's accepted aliases.
3. Distinguish image dataset types (`sr`, `dncnn`, `jpeg`) from video dataset class names (`VideoRecurrentTrainDataset`, `VideoRecurrentTestDataset`). KAIR lowercases before matching, so case is not the issue if the name is otherwise valid.

## REDS4 validation split confusion

Symptoms:

- The user thinks REDS4 clips are missing from training.
- Validation metrics use the wrong clips.

Facts:

- REDS4 validation clips are `000`, `011`, `015`, and `020`.
- In REDS training configs with `val_partition: REDS4` and `test_mode: False`, those clips are excluded from training keys.
- The `official` validation partition refers to copied validation clips indexed `240` through `269` after regrouping.

## `main_test_vrt.py` no dataset found for custom video

Use this checklist:

1. Is `--folder_lq` a root containing clip subfolders, not a single clip unless the selected task supports single-video testing?
2. Does each clip subfolder contain frames directly?
3. If `--folder_gt` is provided, do clip names and frame counts match LQ?
4. If there is no GT, use the video-restoration command path that omits `--folder_gt` and relies on input-only behavior for the chosen task.
5. Run the read-only video checker before rerunning the model command.
