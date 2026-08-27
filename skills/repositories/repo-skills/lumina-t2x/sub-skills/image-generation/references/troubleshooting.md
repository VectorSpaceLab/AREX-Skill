# Image Generation Troubleshooting

## Purpose

Use this page when image inference or conversion fails before the model produces output.

## Missing FlashAttention

**Symptoms**
- `ModuleNotFoundError: No module named 'flash_attn'`
- Importing `lumina_t2i`, `lumina_next_t2i`, or the mini/compositional image modules fails immediately.

**Likely cause**
- The environment does not have a compatible FlashAttention build.

**Recovery**
- Install a CUDA-compatible `flash-attn` build before retrying image inference.
- Re-run the root `scripts/check_env.py --workflow image` check.
- Do not rely on `--use_flash_attn False` as a workaround for missing module imports; that flag only changes a runtime path after the model code is importable.

## Gated checkpoint or LLM access

**Symptoms**
- Hugging Face download failures.
- Warnings about gated checkpoints or missing access tokens.
- `AutoModel.from_pretrained(...)` fails while loading the text encoder.

**Likely cause**
- The checkpoint requires a token or the model path is wrong.

**Recovery**
- Confirm the checkpoint directory and the `ckpt_lm` / `token` values in the config or CLI.
- Re-download the model if the directory is incomplete.

## Checkpoint layout problems

**Symptoms**
- `model_args.pth` is missing.
- `consolidated*.pth` / `consolidated*.safetensors` is missing.
- The script cannot find the EMA or non-EMA weights.

**Likely cause**
- The checkpoint folder belongs to a different model family or was only partially copied.

**Recovery**
- Validate the checkpoint tree with `scripts/check_checkpoints.py` before launching inference.
- Use the matching subproject (`lumina`, `lumina_next`, or mini/compositional) for the checkpoint family you downloaded.

## Invalid resolution or prompt-file layout

**Symptoms**
- Resolution parsing errors.
- Sample scripts fail when given the resolution string in the wrong format.
- The prompt file is not read correctly.

**Likely cause**
- The resolution string does not match the repo's expected `widthxheight` or `category:widthxheight` format.
- The prompt file path is wrong or empty.

**Recovery**
- Check the `resolution` format in the workflow reference before retrying.
- Keep a short prompt file with one caption per line for batch sampling.

## Multi-GPU inference attempts

**Symptoms**
- The script raises `NotImplementedError` for multi-GPU inference.

**Likely cause**
- The image inference code paths are single-GPU only in this repo version.

**Recovery**
- Relaunch with `--num_gpus 1` and keep distributed launches for the training subskill only.

## Diffusers / PyTorch compatibility

**Symptoms**
- Importing `diffusers` fails with a PyTorch API mismatch.
- The environment has a newer or older torch build than the repo's selected image stack expects.

**Likely cause**
- A too-new diffusers release or an incompatible PyTorch wheel was installed in the inspection environment.

**Recovery**
- Use the shared environment checker to record the mismatch.
- Repair the private inspection environment before claiming image workflows are verified.
