# Training troubleshooting

## Purpose

Use this page when training or data configuration fails.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| placeholder `PATH_TO_IMAGES_DIR` values remain in `data_path.py` | the dataset layout has not been configured yet | replace placeholders with real directories and re-run the layout checker |
| foreground and alpha image counts differ | paired directories are not aligned | fix the directory trees or regenerate the dataset pair |
| `dataset-name` chosen as `backgrounds` | argparse accepts it, but the main training loop expects a foreground/alpha dataset | choose one of the real datasets such as `videomatte240k`, `photomatte13k`, `distinction`, or `adobe` |
| `batch_size % distributed_num_gpus` assertion fails | batch size does not divide the GPU count | lower the batch size or change visible GPU count |
| `torch.cuda.device_count()` is zero | no usable CUDA device is visible | use a CUDA-enabled host or stay with non-training workflows |
| NCCL or DDP startup fails | distributed setup, driver, or GPU visibility problem | confirm `CUDA_VISIBLE_DEVICES`, driver, and local GPU access before retrying |
| `--model-refine-threshold` is rejected | the actual flag is `--model-refine-thresholding` in this repo | use the spelling exposed by the help text |
| missing DeepLabV3 pretraining weights | base-training pretraining path is not configured | point `--model-pretrain-initialization` at a real file or use `--model-last-checkpoint` |
| TensorBoard or Kornia import errors | the runtime stack is incomplete | install the runtime packages used by the repo workflows |
| Octave benchmark unavailable | the benchmark script is reference-only and depends on Octave/MATLAB | use the benchmark documentation or a local Octave install |

## Extra guidance

- Use `scripts/check_data_layout.py` before a long run.
- Keep batch size and GPU count aligned for refine training.
- If you only need to validate a checkpoint or command shape, stay in dry-run
  mode.
- Confirm the background roots are separate from the foreground/alpha pair.
