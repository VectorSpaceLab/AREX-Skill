# Feature Extraction Troubleshooting

## Input And Path Failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `csv_path` is rejected or feature extraction stops at dataset initialization | Missing CSV path, unreadable CSV, or no `slide_id` column | Provide a CSV with a `slide_id` column; use bare slide IDs when possible. |
| CLAM looks for `slide_1.svs.svs` or cannot find slide files | `slide_id` values already include an extension that does not match `--slide_ext`, or `--slide_ext` is wrong | Make `slide_id` values bare IDs or use the exact real extension in `--slide_ext`. |
| Coordinate file not found under `data_h5_dir/patches` | WSI preprocessing did not create fast coordinate bags, or `data_h5_dir` points at the wrong parent | Confirm `data_h5_dir/patches/<slide_id>.h5`; use `../wsi-preprocessing/SKILL.md` if patches are missing. |
| HDF5 key or attribute errors from `Whole_Slide_Bag_FP` | The HDF5 file is malformed or from the legacy saved-image pipeline | Fast coordinate HDF5 files need a `coords` dataset with `patch_level` and `patch_size` attributes. |
| OpenSlide cannot open a slide | Missing slide file, unsupported extension, corrupt WSI, or native OpenSlide library issue | Confirm `data_slide_dir/<slide_id><slide_ext>` exists and OpenSlide supports that file format in the environment. |

## Encoder And Checkpoint Failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `AssertionError: UNI is not available` | `UNI_CKPT_PATH` is not set before running `--model_name uni_v1` | Download/request UNI weights outside this skill and export `UNI_CKPT_PATH` to the checkpoint file. |
| `CONCH not installed or CONCH_CKPT_PATH not set` | Optional CONCH package is missing, or `CONCH_CKPT_PATH` is unset | Install CONCH in the CLAM environment and export `CONCH_CKPT_PATH` before `--model_name conch_v1`. |
| CUDA out of memory | Batch size too large, especially with UNI or CONCH | Lower `--batch_size`; retry with a smaller value before changing other options. |
| Results differ from older CLAM runs | Current feature extraction resizes patches to `--target_patch_size`, defaulting to `224` | Set `--target_patch_size` deliberately and keep it consistent across comparable feature sets. |

## Output And Downstream Failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Slides are skipped unexpectedly | Existing `feat_dir/pt_files/<slide_id>.pt` files trigger default auto-skip | Add `--no_auto_skip` when intentional recomputation is needed. |
| `h5_files/` or `pt_files/` is missing after a failed run | The job stopped before extraction or lacked permission to write under `feat_dir` | Confirm `feat_dir` is writable; `extract_features_fp.py` creates both subdirectories at startup. |
| Training/evaluation cannot find features | `--data_root_dir` or task-specific feature folder does not point to a directory containing `pt_files/` | Arrange `DATA_ROOT_DIR/<dataset_feature_dir>/pt_files/<slide_id>.pt` and use `../training-evaluation/SKILL.md`. |
| Model shape mismatch when training or evaluating | Feature dimension does not match downstream `--embed_dim` | Use `--embed_dim 1024` for `resnet50_trunc` or `uni_v1`; use `--embed_dim 512` for `conch_v1`. |
| Heatmap checkpoint load fails after switching encoders | Heatmap model config, checkpoint, and feature encoder dimensions are inconsistent | Keep the same encoder family and `embed_dim` across feature extraction, training, evaluation, and heatmaps. |

## Safe Preflight

Run the bundled helper before launching a heavy job:

```bash
python scripts/clam_feature_command_builder.py \
  --data_h5_dir DIR_TO_COORDS \
  --data_slide_dir DATA_DIRECTORY \
  --csv_path CSV_FILE_NAME \
  --feat_dir FEATURES_DIRECTORY \
  --slide_ext .svs \
  --model_name uni_v1 \
  --batch_size 128 \
  --target_patch_size 224
```

The helper checks option consistency, previews slide-to-path mapping when the CSV is available, and prints expected output paths. It does not import CLAM, open WSI files, inspect HDF5 contents, load checkpoints, or download model weights.
