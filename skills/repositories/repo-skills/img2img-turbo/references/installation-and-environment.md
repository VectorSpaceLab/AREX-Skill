# Installation and Environment

## Purpose

Use this reference when you need to create, repair, or sanity-check a Python environment for the `img2img-turbo` source checkout.

## Source-checkout expectations

- This repository does not expose a normal Python package layout at the root.
- The runtime modules live under `src/` and `src/my_utils/`.
- If you import the source modules directly, add `src/` to `PYTHONPATH` or let the bundled environment checker do it for you.
- The public workflows are source scripts, not console entry points.

## Verified compatibility snapshot

The current checkout was inspected successfully with a CUDA-capable Python 3.10 environment. The compatible runtime stack included:

- PyTorch: `torch 2.5.1+cu121`
- TorchVision / TorchAudio: `torchvision 0.20.1+cu121`, `torchaudio 2.5.1+cu121`
- CUDA helper: `xformers 0.0.28.post3`
- Hugging Face / diffusion stack: `accelerate 0.34.2`, `diffusers 0.25.1`, `transformers 4.35.2`, `peft 0.7.1`, `huggingface-hub 0.25.2`
- UI / image stack: `gradio 3.43.1`, `opencv-python 4.6.0.66`
- Training extras used by the repo workflows: `clip`, `lpips`, `clean-fid`, `vision_aided_loss`

The repository's `environment.yaml` and `requirements.txt` capture the intended dependency family, but they are not a guarantee that the newest available wheels will work together. If import checks fail, prefer aligning the specific torch / torchvision / xformers / huggingface-hub / transformers / diffusers / peft combination before expanding the environment further.

## Suggested setup pattern

1. Create a private Python 3.10 environment with CUDA-aware PyTorch.
2. Install the repository runtime dependencies that match the selected workflow.
3. Run the bundled environment checker from the skill tree.
4. Only after that, route to the paired, unpaired, or training sub-skill that matches the task.

Example smoke check patterns:

```bash
python scripts/check_environment.py --repo-root /path/to/img2img-turbo --scope paired --check-help
python scripts/check_environment.py --repo-root /path/to/img2img-turbo --scope unpaired --check-help --require-cuda
python scripts/check_environment.py --repo-root /path/to/img2img-turbo --scope training --check-help --require-cuda
```

## Compatibility notes

- The source model code moves tensors and modules to CUDA. Actual generation and training require a working CUDA runtime.
- `setuptools<81` may be needed if `gdown` / `vision_aided_loss` complain about `pkg_resources`.
- Some legacy extras listed in dependency files are not required by the source workflows and can be omitted if they conflict with the selected stack.
- `accelerate launch` should be used with explicit process and port settings for training. For quick parser checks, prefer the source script `--help` paths or the bundled checker.

## When to stop and revise

If the checker reports missing imports, version mismatches, or CUDA failures:

1. Align the incompatible package versions.
2. Re-run the bundled checker.
3. If the task only needs one workflow family, narrow the scope instead of forcing a broader environment.
4. If actual model execution is still required after the checker passes, move to the matching sub-skill and confirm the task-specific prerequisites there.
