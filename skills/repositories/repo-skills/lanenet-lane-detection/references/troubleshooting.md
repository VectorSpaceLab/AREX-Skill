# LaneNet troubleshooting

This page collects cross-cutting failures. Workflow-specific details still live in the nearest sub-skill references.

| Symptom | Likely cause | Recovery | Owning route |
| --- | --- | --- | --- |
| `TypeError: Descriptors cannot not be created directly` while importing TensorFlow | `protobuf` is too new for TensorFlow 1.15 | Pin `protobuf<=3.20.x` in the inspection/runtime environment and retry the import | Shared runtime |
| `Could not auto-detect the repository root` | The script was launched outside the repo checkout or without `--repo_root` | Run from the repository root or pass an explicit repository root | Shared runtime |
| `Config file ... cannot be read` or config paths still contain `REPO_ROOT_PATH` | The script was launched from the wrong directory or placeholder paths were never normalized | Run from the repo root, pass `--repo_root`, or replace placeholders before direct use | Shared runtime |
| `gt_image/`, `gt_binary_image/`, or `gt_instance_image/` missing | The TuSimple archive has not been converted yet | Go to the data-preparation sub-skill and regenerate the masks and list files | [data-preparation](../sub-skills/data-preparation/SKILL.md) |
| TFRecord generation fails because list files still contain `ROOT_PATH` | The sample list files were copied without normalization | Rewrite the paths to real files or rerun the TFRecord wrapper with a real `--data-dir` | [data-preparation](../sub-skills/data-preparation/SKILL.md) |
| Training produces no snapshots on a tiny dataset | `steps_per_epoch` is 1 or less because the batch size is too large for the available TFRecords | Lower `TRAIN.BATCH_SIZE` or add more TFRecords before starting the run | [training](../sub-skills/training/SKILL.md) |
| Training cannot restore a checkpoint | The restore path is missing, points at the wrong base name, or does not match the moving-average graph | Use the training wrapper to resolve the checkpoint base path and verify the restore flag | [training](../sub-skills/training/SKILL.md) |
| Inference produces an empty or black mask | DBSCAN parameters are too strict, the checkpoint does not match the graph, or lane fitting is unsuitable for the data | Tune `POSTPROCESS.DBSCAN_EPS` / `DBSCAN_MIN_SAMPLES`, try `--with_lane_fit 0`, and verify the checkpoint | [inference-evaluation](../sub-skills/inference-evaluation/SKILL.md) |
| Batch evaluation crashes when forming output paths | The image tree is not a TuSimple-style `test_set/clips` layout | Use a TuSimple-style directory or the batch wrapper's non-TuSimple smoke option for custom data | [inference-evaluation](../sub-skills/inference-evaluation/SKILL.md) |
| `MNNConverter` is missing | The PB→MNN step depends on an external converter toolchain | Freeze the checkpoint first, then install or point to the external MNN converter before retrying | [model-export](../sub-skills/model-export/SKILL.md) |
| GPU is visible on the host but TensorFlow sees no CUDA device | The runtime lacks matching CUDA/cuDNN libraries for the TensorFlow build | Use the validated TensorFlow 1.15 + CUDA 10.0 + cuDNN 7.6 environment or adjust the backend stack | Shared runtime |

## Fast recovery order

1. Confirm the repo root and config path.
2. Confirm the dataset layout or checkpoint base path.
3. Confirm the backend environment and TensorFlow/protobuf compatibility.
4. Then reopen the specific sub-skill for the workflow you are running.
