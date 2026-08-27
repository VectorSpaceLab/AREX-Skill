# Troubleshooting

## Purpose

Read this when DragGAN fails to install, import, or launch, or when a browser/API workflow behaves differently from the docs.

## Install and import issues

### `ImportError: cannot import name media_data from gradio_client`

The Gradio stack is too new for this repo snapshot.
Pin `gradio-client==0.2.6` in the active environment and retry the bundled preflight.

### `ModuleNotFoundError: No module named 'pkg_resources'`

Your `setuptools` build is too new for the pinned Gradio release.
Install a setuptools release that still provides `pkg_resources`, such as `setuptools<81`, and rerun the bundled preflight.

### `ModuleNotFoundError: No module named 'audioop'`

This usually shows up on newer Python releases where `audioop` is no longer shipped.
Use a Python build that still includes `audioop`, or install the `audioop-lts` backport before importing Gradio.

### `torch` imports but CUDA is unavailable

The verified drag workflow requires CUDA.
Install a CUDA-enabled PyTorch/TorchVision pair and confirm `torch.cuda.is_available()` before launching the demo.

## Checkpoint and network issues

### First launch hangs or retries while downloading weights

That is usually the checkpoint cache being populated.
Check `DRAGGAN_HOME`, proxy settings, and network access to the Hugging Face mirror used by `draggan.utils.get_path()`.

### A checkpoint file cannot be found

Confirm the relative checkpoint path exactly matches the catalog in `references/checkpoints.md` and that the file exists under the cache root.

## Runtime limitations in this snapshot

### CPU or MPS launch flags do not behave like a supported drag backend

The current drag loop hardcodes CUDA. Treat CPU and MPS as unsupported for actual dragging, even if the UI help accepts the flag.

### The mask tab appears but does not constrain the edit

The current optimizer does not enforce the mask in the live implementation. Do not rely on the mask tab for protected regions.

### Uploaded-image inversion fails

Treat uploaded-image inversion as experimental in this snapshot. If it raises a name or import error during upload, fall back to the seeded-image flow and treat the upload path as non-essential.

## What to do next

1. Run `scripts/check_install.py --mode web` or `--mode api`.
2. Re-read `references/deployment.md` if the issue is launch-related.
3. Re-read the relevant sub-skill if the issue is workflow-specific.
