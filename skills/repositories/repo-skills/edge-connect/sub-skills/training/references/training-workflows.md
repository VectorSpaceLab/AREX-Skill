# Training workflows

## Startup contract
`train.py` is a thin wrapper: it calls `main(mode=1)` and uses the shared loader to build the runtime config.

At startup the loader:
1. reads `config.yml` from the checkpoint directory,
2. creates the checkpoint directory if needed,
3. copies the bundled template into `config.yml` when the file is missing,
4. sets `CUDA_VISIBLE_DEVICES` from `GPU`,
5. seeds Python, NumPy, and Torch,
6. builds `EdgeConnect`, then loads any existing checkpoints.

Treat the checkpoint directory as the config home. It owns the generated config file, checkpoint weights, logs, and validation samples for the current run.

With `mode=1`, `main.load_config` forces `MODE = 1`. Passing `--model` to `train.py` overrides the YAML `MODEL` for that run; omitting it leaves the YAML value in control.

Training command shape:

```bash
python train.py --model <1|2|3|4> --checkpoints <checkpoint-dir>
```

`--path` is accepted as an alias for `--checkpoints`.

## MODE vs MODEL

| Key | Values | Meaning |
| --- | --- | --- |
| `MODE` | `1` train, `2` test, `3` eval | Selects which top-level loop runs |
| `MODEL` | `1` edge, `2` inpaint, `3` edge-inpaint, `4` joint | Selects which stage family is active |

`MODE` chooses the wrapper behavior. `MODEL` chooses the architecture and checkpoint family.

## Stage recipes

| `MODEL` | Loads on start | What trains | What saves | Main logs and samples |
| --- | --- | --- | --- | --- |
| `1` edge | Edge generator/discriminator if present | Edge generator + discriminator | `EdgeModel_gen.pth`, `EdgeModel_dis.pth` | `log_edge.dat`, `samples/edge/<iteration>.png` |
| `2` inpaint | Inpaint generator/discriminator if present | Inpaint generator + discriminator | `InpaintingModel_gen.pth`, `InpaintingModel_dis.pth` | `log_inpaint.dat`, `samples/inpaint/<iteration>.png` |
| `3` edge-inpaint | Edge checkpoints if present, then inpaint checkpoints if present | Inpaint generator + discriminator; edge model acts as conditioner | `InpaintingModel_gen.pth`, `InpaintingModel_dis.pth` | `log_edge_inpaint.dat`, `samples/edge_inpaint/<iteration>.png` |
| `4` joint | Both families if present | Both generators and both discriminators | Both checkpoint families | `log_joint.dat`, `samples/joint/<iteration>.png` |

Notes:
- `MODEL=3` keeps the edge branch as a conditioning path; the alternate teacher-forcing branch in the source is unreachable because the condition is hard-coded true.
- `MODEL=4` is the only stage that steps both model families in the same batch.

## Interval behavior
- `MAX_ITERS` stops training by iteration count, not by epoch.
- `LOG_INTERVAL` appends scalar loss values to the stage log file.
- `SAMPLE_INTERVAL` saves a stitched validation preview.
- `EVAL_INTERVAL` triggers the internal validation loop during training.
- `SAVE_INTERVAL` writes checkpoint files.
- `0` disables the corresponding action.

## Sample and eval loops
- `sample()` switches both models to eval mode, draws a batch from the validation iterator, and writes a stitched montage with the input, masked input, edge map, raw output, and merged output.
- `eval()` runs a validation pass and prints internal metrics only. It does not create the external scoring files handled elsewhere.
- Both loops use the validation dataset, not the test-only one-to-one mask path.
- `sample()` is a no-op when the validation set is empty.

## Resume and checkpoint behavior
- Generator checkpoints carry the iteration counter, so resume progress comes from the corresponding `*_gen.pth` file.
- Discriminator checkpoints are loaded only when `MODE=1` and only if the file exists.
- Optimizer state is not saved, so Adam momentum restarts on resume.
- If a discriminator file is missing, training still resumes from the generator weights.
- If a generator file is missing, the corresponding submodel starts fresh.

## Safe dry planning
- Run `scripts/make_training_config.py --help` to inspect the config surface.
- Use `scripts/make_training_config.py` without `--output` to preview YAML before writing it.
- Use `--cpu` only for inspection or smoke planning. Real training should keep a CUDA device list.
- Keep `BATCH_SIZE`, `INPUT_SIZE`, and `MAX_ITERS` small for a quick planning pass.
- The bundled notes only say that convergence varies by dataset; do not promise a fixed epoch count.

## Related side effects
- `samples/` is for validation snapshots during training.
- `results/` is the default inference output directory and is primarily used by test mode.
- External PSNR/SSIM/FID scoring belongs to evaluation, not this sub-skill.
