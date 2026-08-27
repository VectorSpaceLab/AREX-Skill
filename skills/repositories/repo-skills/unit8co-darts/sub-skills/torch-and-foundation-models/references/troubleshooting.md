# Torch and foundation troubleshooting

## `ModuleNotFoundError` for torch or PyTorch Lightning

Install `darts[torch]` or a compatible environment package. If GPU is required, follow the backend-specific torch installation first, then install Darts.

## CUDA is unavailable

**Symptom:** `torch.cuda.is_available()` is false or trainer cannot use CUDA.

**Likely causes:** CPU-only torch wheel, missing NVIDIA driver, incompatible CUDA runtime, container without GPU access, or no GPU hardware.

**Recovery:** verify hardware and wheel; run a tiny Darts model with CUDA trainer kwargs before claiming success. If unavailable, answer in CPU scope and document the limitation.

## Training writes unexpected files

Use `save_checkpoints=False`, `logger=False`, and an explicit `work_dir` outside the skill directory. For experiments, ask the user where checkpoints should live.

## Chunk/covariate shape errors

- Target series may be shorter than `input_chunk_length + output_chunk_length`.
- Past covariates may not cover the full historical window.
- Future covariates may not extend through `output_chunk_length`/forecast horizon.
- Model class may not support the requested covariate type.

Route data-span repair to `data-processing-and-covariates`, then revisit model choice.

## Foundation wrapper downloads in restricted environments

Do not instantiate wrappers that may contact model hubs unless the user approved network access or provided a local cache/path. A no-network plan should check installed packages, cache paths, memory, and exact wrapper support first.

## Optional wrapper package missing

`NeuralForecastModel` and `TiRexModel` require extra packages beyond the baseline environment. Install only the wrapper package needed by the selected task, then rerun import checks.

## Slow or unstable tiny training

Reduce `n_epochs`, `batch_size`, hidden/channel sizes, and series length. Disable progress bars/loggers. Use CPU first unless the task specifically tests an accelerator.
