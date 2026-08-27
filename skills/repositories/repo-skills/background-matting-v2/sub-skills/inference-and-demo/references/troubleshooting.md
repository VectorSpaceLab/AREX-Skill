# Inference and demo troubleshooting

## Purpose

Use this page when inference or demo commands fail after imports work.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `FileNotFoundError` for a checkpoint | checkpoint path is wrong | point `--model-checkpoint` at a real file or use the smoke helper that does not need weights |
| `src and bgr must have the same shape` | input directories, video frames, or webcam background capture are mismatched | resize or align the inputs before inference |
| `src and bgr must have width and height that are divisible by 4` | `MattingRefine` requires spatial sizes divisible by 4 | use a 4-divisible resolution or resize upstream |
| `Only mattingrefine support ref output` | `ref` was requested for `mattingbase` | switch to `mattingrefine` or drop `ref` |
| `Only mattingbase and mattingrefine support err output` | invalid model/output pair | choose a supported model type |
| very slow CPU inference | the demo is being used as if it were a live GPU pipeline | use CUDA or lower the resolution / throughput expectation |
| OpenCV GUI or webcam failure | headless environment or missing camera | run image/video inference instead of webcam demo |
| `HomographicAlignment` fails | too few feature matches or noisy frames | turn off `--preprocess-alignment` |
| output directory already exists | the CLI protects existing output trees | use a fresh directory or add `-y` when overwrite is intentional |

## Extra guidance

- Use the bundled smoke helper first when you only need to prove the model path.
- Keep image and video fixtures tiny while iterating on command shape.
- Use `mattingbase` only when you explicitly want the coarse model.
- For better live-demo behavior, keep the background and source lighting close.
- If the demo keeps failing on the same input pair, check that your pair files
  are not swapped and that the background is not smaller than the source.
