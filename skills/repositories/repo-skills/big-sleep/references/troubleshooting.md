# Troubleshooting

## Purpose

Read this when Big Sleep fails to import, cannot see CUDA, cannot download weights, or rejects prompt/config values.

## Fast recovery order

1. Run `scripts/check_runtime.py`.
2. Run `python -m pip check` in the installed environment.
3. Re-run `dream --help`.
4. If import still fails, reinstall a CUDA-enabled torch/torchvision pair that matches the driver and then reinstall `big-sleep`.

## 1) Import fails before any generation starts

### Symptoms

- `AssertionError: CUDA must be available in order to use Big Sleep`
- `ImportError: libcudnn.so.9: cannot open shared object file`
- `ImportError: ... libtorch_cpu.so: undefined symbol: iJIT_NotifyEvent`

### Likely causes

- CPU-only torch/torchvision.
- A CUDA wheel was installed without its matching NVIDIA runtime packages.
- Mixed torch/CUDA packages from different channels or versions.

### Recovery

- Confirm `torch.cuda.is_available()` in `scripts/check_runtime.py`.
- Install a matching CUDA-enabled torch/torchvision pair.
- Make sure `python -m pip check` passes after the install.
- Reinstall `big-sleep` only after the backend is healthy.

### Stop here when

- No NVIDIA GPU is visible.
- The driver is too old for the selected CUDA wheel.
- You are on a CPU-only machine and do not intend to move the task to GPU hardware.

## 2) `dream --help` works but generation fails immediately

### Symptoms

- Fire prints the help text, but a real run crashes during import or first CUDA use.
- `torch.cuda.is_available()` is false inside the environment even though the host has GPUs.

### Likely causes

- The active environment is not the same one that passed the help check.
- A stale editable install shadows the intended package.
- Torch imports from the wrong channel or version.

### Recovery

- Re-run `scripts/check_runtime.py` and check the imported `big_sleep` path.
- Confirm `python -m pip show big-sleep` reports the expected installed package.
- Reinstall into the same prefix rather than mixing multiple prefixes implicitly.

## 3) First-run model downloads fail or stall

### Symptoms

- Requests to the CLIP or BigGAN model URLs time out.
- Cache files are corrupt or incomplete.
- The run stalls the first time it tries to load a model.

### Likely causes

- The host has no outbound network access.
- The CLIP cache at `~/.cache/clip` is missing or stale.
- The BigGAN cache directory is missing, stale, or pointed at the wrong location.

### Recovery

- Re-run with network access if this is the first real generation.
- Preseed caches if the environment will be offline later.
- If needed, point `PYTORCH_PRETRAINED_BIGGAN_CACHE` at a writable cache directory.

### Stop here when

- Network access is intentionally forbidden.
- You cannot provide the required model files in another way.

## 4) Prompt, image-size, or config validation errors

### Symptoms

- `RuntimeError: Input ... is too long for context length 77`
- `AssertionError: image size must be one of 128, 256, or 512`
- `AssertionError: max_classes must be between 0 and 1000`
- `AssertionError: the deterministic (seeded) operation does not work with interpolation`

### Likely causes

- The prompt is too long for CLIP.
- An unsupported image size was selected.
- `--max_classes` is out of range.
- `--torch_deterministic` was combined with `--bilinear`.

### Recovery

- Shorten the prompt or split it into multiple phrases with `|`.
- Use `128`, `256`, or `512` for `image_size`.
- Keep `max_classes` in the `1..1000` range or omit it.
- Disable either `bilinear` or `torch_deterministic`.

## 5) Output-file surprises

### Symptoms

- The CLI asks before overwriting an existing file.
- A `.best.png` file never appears.
- `open_folder` tries to launch a GUI on a headless host.

### Likely causes

- `overwrite=False` and the target PNG already exists.
- `save_best` never saw an improved score.
- `open_folder=True` on SSH, CI, or another non-desktop session.

### Recovery

- Pass `--overwrite=True` for unattended runs.
- Use `--open_folder=False` rather than `--open_folder false` when you want to suppress desktop opening on a headless or remote machine. The space-separated form can be parsed as a string and still trigger the folder-opener.
- Lower the step count only for smoke tests; longer runs are more likely to produce a better score.
- Use `--open_folder=False` on remote or headless systems.

## 6) CUDA is visible on the host but not in the environment

### Symptoms

- `nvidia-smi` works, but torch cannot see CUDA.
- `dream --help` fails because the package import fails before the CLI parser runs.

### Likely causes

- The environment contains the wrong torch build.
- The environment mixes conda and pip packages from incompatible CUDA variants.
- The runtime packages required by the wheel are missing.

### Recovery

- Treat the environment as broken rather than trying to reason around the symptom.
- Rebuild or repair the environment until `scripts/check_runtime.py` and `python -m pip check` both pass.
- Only then move on to the generation workflow.

## Recommended next command

If you want one quick check that exercises the key runtime surface without starting a long run, use:

```bash
python scripts/check_runtime.py --check-cli
```

That should tell you whether the installed package, CUDA torch, and CLI are ready for an actual generation job.
