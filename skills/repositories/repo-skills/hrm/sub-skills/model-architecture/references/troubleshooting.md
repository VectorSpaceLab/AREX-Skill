# Model Architecture Troubleshooting

## FlashAttention import fails

Symptoms:

- `ModuleNotFoundError: No module named 'flash_attn_interface'` followed by
  `ModuleNotFoundError: No module named 'flash_attn'`.
- Importing `models.layers` or `models.hrm.hrm_act_v1` fails before model
  construction.

Likely causes:

- FlashAttention was not installed.
- The installed wheel does not match Python, PyTorch, CUDA, or GPU architecture.
- Hopper users attempted to use FA2 when the README recommends FA3.

Recovery:

1. Verify PyTorch CUDA first with a tiny tensor allocation.
2. Install the FlashAttention variant compatible with the GPU and torch build.
   For A100/Ampere, FA2 is the usual path; Hopper may use FA3.
3. Re-run `inspect_model_config.py --cuda-smoke`.

## `adam_atan2_backend` missing

Symptoms:

- `ModuleNotFoundError: No module named 'adam_atan2_backend'` while importing
  `pretrain.py` or `adam_atan2`.

Likely causes:

- `adam-atan2` installed as a pure Python wheel without compiling the CUDA
  extension.
- CUDA toolkit headers, `nvcc`, `pybind11` headers, or compiler tools were
  missing when it was installed.

Recovery:

1. Ensure PyTorch CUDA and a compatible CUDA toolkit are installed in the same
   environment.
2. Install build helpers (`ninja`, `setuptools-scm`, `pybind11`) if required.
3. Reinstall `adam-atan2` from source with build isolation disabled so it sees
   the installed PyTorch/CUDA stack.
4. Treat missing `adam_atan2_backend` as a required training backend block, not
   an optional skip.

## Device mismatch in model smoke

Symptoms:

- `Expected all tensors to be on the same device, but found cuda:0 and cpu` in
  `reset_carry`.

Likely causes:

- Buffers were initialized on CPU while inputs were on CUDA.
- The smoke constructed the model outside the same `torch.device("cuda")`
  context used by the training code.

Recovery:

1. Follow the repository's `pretrain.create_model` pattern, which instantiates
   inside `with torch.device("cuda")`.
2. Create batch tensors inside the same CUDA context or explicitly place them
   on CUDA.

## Non-contiguous FlashAttention output with `.view(...)`

Symptoms:

- `RuntimeError: view size is not compatible with input tensor's size and stride
  ... Use .reshape(...) instead.`

Likely cause:

- The installed FlashAttention version returns a non-contiguous output tensor,
  while `models/layers.py` reshapes with `.view(batch_size, seq_len,
  output_size)`.

Recovery:

1. For a code-editing task, change the attention output reshape to
   `.reshape(...)` or call `.contiguous()` before `.view(...)`, then run a
   bounded model forward smoke.
2. For a pure usage task, try the dependency versions used by the repository or
   an environment where this stride behavior does not occur.
3. Do not claim full model forward verification until this smoke passes.

## Bad model/loss identifier

Symptoms:

- `ValueError` unpacking identifier or `AttributeError` for a class name.
- Hydra config references a module without `@ClassName`.

Recovery:

1. Use `module@class` strings under the `models.` prefix.
2. Validate identifiers with `inspect_model_config.py --repo-root <HRM>`.
3. Keep `arch.loss.loss_type` equal to a loss function name in `models.losses`,
   such as `stablemax_cross_entropy` or `softmax_cross_entropy`.
