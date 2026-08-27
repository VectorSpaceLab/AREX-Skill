# Single-GPU Inference Workflows

## Standard command with bundled runner

After environment and checkpoint validation, build a command that uses the bundled runner. If `hyvideo` is not installed/importable in the active environment, add `--repo-root <hunyuan-video-source-root>` to the builder command.

```bash
python sub-skills/inference/scripts/build_sample_command.py \
  --prompt "A cat walks on the grass, realistic style." \
  --height 544 --width 960 \
  --video-length 129 \
  --seed 42 \
  --use-cpu-offload \
  --save-path ./results
```

The printed command will look like:

```bash
python sub-skills/inference/scripts/run_sample_video.py --model-base ckpts --video-size 544 960 --video-length 129 --infer-steps 50 --prompt 'A cat walks on the grass, realistic style.' --embedded-cfg-scale 6.0 --flow-shift 7.0 --save-path ./results --seed 42 --flow-reverse --use-cpu-offload
```

The builder is safe. The runner is a real GPU/model job and should only be executed after checkpoint and CUDA preflights pass.

## Choosing resolution and frames

- Use `544 960` or `960 544` for 540p-class jobs when memory is constrained.
- Use `720 1280` or `1280 720` for 720p-class jobs only when the GPU memory budget is adequate.
- Use 65 frames for a shorter roughly 2-second video and 129 frames for a roughly 5-second video.
- Avoid arbitrary frame counts unless they satisfy the default VAE rule.

## Reproducibility

Use a fixed `--seed` when you need repeatable seed selection. A deterministic bit-identical video can still depend on CUDA kernels, PyTorch/flash-attn versions, and distributed execution details, so do not promise exact reproducibility across different hosts.

## Memory mitigation sequence

1. Lower resolution.
2. Keep `--use-cpu-offload` for single-GPU mode.
3. Use FP8 weights if the FP8 checkpoint and map exist.
4. Use xDiT multi-GPU only after optional dependencies and a valid degree plan are ready.
