# ScanNet troubleshooting

Use this when ScanNet preprocessing, validation, training, or whole-scene evaluation fails.

## Fast diagnosis table

| Symptom | Likely cause | Recovery |
|---|---|---|
| `SyntaxError: Missing parentheses in call to 'print'` or `except Exception, e` fails | Legacy Python 2 script executed with Python 3 | Use Python 2 for raw repository scripts, or use the bundled Python 3 validators/command builders for static checks. |
| `TabError`, `IndentationError`, or inconsistent block parsing | The ScanNet trainer/dataset files mix tabs and spaces in Python 2-era style | Avoid editing raw files casually. If patching, normalize indentation in a copy and rerun only in the legacy environment. |
| `FileNotFoundError` / `IOError` for `scannet_train.pickle` or `scannet_test.pickle` | Missing `data/scannet_data_pointnet2` preprocessed pickle root | Download or create the preprocessed pickle root, then run `scripts/validate_scannet_layout.py` before training. |
| Batch assignment error such as shape `(8192,6)` into `(8192,3)` | Pickle point arrays include RGB/extra columns instead of XYZ only | Convert raw `.npy` preprocessing artifacts into separate `N x 3` XYZ arrays and 1-D label arrays. Do not feed `N x 8` raw scene arrays directly to the trainer. |
| `IndexError` while indexing `labelweights[semantic_seg]` | Label id outside `[0, 20]` or labels are not 1-D | Run the validator; fix class mapping, flatten labels to `N`, or retrain only after explicitly changing `NUM_CLASSES`. |
| Accuracy is zero/NaN or class metrics ignore many points | Labels are mostly `0` (`unannotated`) or sample weights are zero from block masks | Inspect label histograms with the validator. The trainer intentionally evaluates only `label > 0` and positive weights. |
| Raw preprocessing maps many labels to `unannotated` unexpectedly | Wrong TSV version or wrong raw/NYU40 columns | For V1 use raw column `0` and NYU40 column `6`; for V2 inspect the header and use shifted columns with validator overrides. |
| `scannet-labels.combined.tsv` cannot be found | The preprocessing utility opens the TSV by bare filename in the current working directory | Run from the preprocessing working directory or copy/pass the TSV path to a wrapper. Validate the chosen TSV before preprocessing. |
| Missing `*_vh_clean_2.ply`, `*.aggregation.json`, or `*.segs.json` | Raw ScanNet folder path is wrong or the original dataset was not downloaded/extracted | Run `scripts/validate_scannet_layout.py --raw-scan-root ... --scene-list ...` and fix the raw root independently of demo output. |
| `demo_output/scene.obj` is missing | `demo.py` did not run, expected `scannet_scenes/scene0001_01.npy` is absent, or output path is different | Check demo output with `--demo-output` separately. A missing demo artifact is not the same as a missing raw ScanNet folder. |
| `ImportError: No module named pointnet2_sem_seg` | `scannet/train.py` adds the ScanNet folder and repo root to `sys.path` but not necessarily `models/` | Run from `scannet/` with `PYTHONPATH` including `../models`, or copy/symlink the semantic model file into the ScanNet working directory. |
| `cp: cannot stat ... pointnet2_sem_seg.py` at startup | `MODEL_FILE` backup path assumes the model file is in the ScanNet directory | This copy failure is a source-script quirk. The import can still work if `PYTHONPATH` resolves the model. For a clean run, place a copy/symlink where the backup path expects it. |
| TensorFlow op load errors for sampling/grouping/interpolation | PointNet++ custom `.so` libraries are missing or ABI-incompatible | Use the root/model-API custom-op guidance. CPU-only pickle validation does not prove PointNet++ model execution readiness. |
| `CUDA_ERROR`, missing `nvcc`, or GPU device placement failure | Legacy CUDA/custom-op backend is unavailable or incompatible | Treat full ScanNet training/evaluation as optional backend verification. Continue with validators and static command guidance unless a compatible TF1/CUDA stack is prepared. |
| Whole-scene evaluation runs out of memory | Too many `batch_size x num_point` tiles in a model call, often from large scenes | Reduce `--batch_size` first. Reducing `--num_point` changes model input assumptions and should be reported as an experimental setting. |
| Whole-scene evaluation appears to skip some tiles | `ScannetDatasetWholeScene` drops tiles whose strict inner mask covers less than 1% of sampled points | This is source behavior. Confirm scene scale and coordinates; it may indicate malformed points or very sparse cells. |
| `ValueError: need at least one array to concatenate` in whole-scene or virtual-scan loaders | No valid tiles/views were produced | Check scene extents, nonempty point arrays, nonzero labels, and coordinate scale. Tiny fixtures should span XY enough to create at least one tile. |
| Different `pc_util` behavior than expected | The ScanNet folder contains a legacy duplicate `pc_util.py`, while shared utilities also exist elsewhere | Do not treat the ScanNet duplicate as canonical runtime guidance. Use the repo skill's shared utility/custom-op sub-skill for cross-workflow utility behavior. |

## Python 2 and indentation sensitivity

The raw ScanNet scripts are not modern Python modules. They contain Python 2 print statements, `xrange`, old exception syntax, and mixed tab/space indentation. This is why the runtime skill ships Python 3-safe validators and command builders instead of copying the raw trainer.

When a user must run the original scripts:

1. Use a Python 2.7 / TensorFlow 1.x environment.
2. Run only after static validation has passed.
3. Avoid broad automated reformatting unless the user explicitly wants to port the scripts.
4. If patching paths or model imports, patch a copy and preserve the original evidence.

## Pickle layout failures

Most ScanNet data failures reduce to one of these schema problems:

- the pickle file is missing one of the two sequential objects;
- points and labels lists have different numbers of scenes;
- point arrays are not 2-D `N x 3` arrays;
- semantic labels are `N x 1` or `N x K` instead of 1-D `N`;
- labels contain unexpected ids such as NYU40 ids beyond `20`;
- all labels are `0`, so training/evaluation masks remove useful supervision.

Run:

```bash
python3 scripts/validate_scannet_layout.py data/scannet_data_pointnet2 --splits train test --max-scenes 25
```

If a synthetic or real fixture intentionally includes an unexpected class id, the validator should fail with a message naming the offending split, scene index, and observed invalid ids.

## V1 vs V2 label table mismatch

The V1 source utility maps raw class names with TSV columns `(0, 6)`. The repository note says V2 columns are shifted by one. A wrong column choice often produces a plausible-looking table but maps semantic names incorrectly, causing excessive `unannotated` labels or ids outside the 21-class table after preprocessing.

Recovery process:

1. Open the TSV header and identify the raw class name column and NYU40 class-name column.
2. Validate those explicit columns:

   ```bash
   python3 scripts/validate_scannet_layout.py --label-tsv path/to/table.tsv --raw-column <raw_col> --nyu40-column <nyu40_col>
   ```

3. Only then run or adapt the raw collector.
4. Revalidate generated `.npy` files and final pickles.

## Preprocessing path edits

The raw preprocessing scripts have hard-coded relative paths such as `SCANNET_DIR = 'scannet_clean_2'`, bare `scannet_all.txt`, and bare TSV filenames. Treat the bundled command builder output as a reminder of the working directory, not as proof that all paths exist.

Validate independently:

```bash
python3 scripts/validate_scannet_layout.py --raw-scan-root /data/scannet_clean_2 --scene-list scannet_all.txt
python3 scripts/validate_scannet_layout.py --label-tsv scannet-labels.combined.tsv
python3 scripts/validate_scannet_layout.py --preprocessed-scenes scannet_scenes
python3 scripts/validate_scannet_layout.py --demo-output demo_output
```

This separation matters: a preprocessing case can have a missing raw-data path but still have an old `demo_output`, or valid raw data with no demo output yet.

## Whole-scene memory and batch-size behavior

Whole-scene evaluation is tile-based. A single large scene can produce many tiles, and the trainer carries extra tiles into later model calls. Reducing `--batch_size` reduces per-call memory, but it may increase the number of calls. Reducing `--num_point` reduces tensor size but also changes the sampled point count and can make metrics incomparable to the original default.

When diagnosing memory:

1. Keep `--num_point 8192` if comparability matters.
2. Lower `--batch_size` first.
3. Validate scene coordinate scale and extents if the tile count is unexpectedly huge.
4. Report CUDA/custom-op readiness separately from data-layout validity.
