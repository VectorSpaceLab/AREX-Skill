# Backend troubleshooting

## `DeepSpeed backend selected but module not available`

The backend wrapper checks `import deepspeed`. Install DeepSpeed only after confirming the user needs it and the torch/CUDA stack is compatible. If the task only uses `full`, `axial_row`, `axial_col`, or `conv_like` attention, DeepSpeed sparse attention may not be required.

## `--deepspeed` ignored or parsed as unavailable

When DeepSpeed is not importable at parser construction time, the wrapper still adds a `--deepspeed` argument but makes it parse to false. This prevents accidental selection of an unavailable backend. Install/verify DeepSpeed, then rerun parser/help checks.

## `LOCAL_RANK` missing

DeepSpeed backend expects distributed launcher environment variables such as `LOCAL_RANK`. Use the proper DeepSpeed launcher instead of plain `python` when selecting DeepSpeed distributed execution.

## Horovod import failures

`HorovodBackend` requires `horovod.torch`. Horovod installs are MPI/CUDA sensitive; do not add Horovod to a working environment without approval.

## Apex build failures

Common causes:

- no `nvcc`;
- torch/CUDA ABI mismatch;
- incompatible compiler;
- insufficient RAM/disk;
- using Apex when `--fp16` or lower batch size would be enough.

## Sparse attention failures

If `attn_types` contains `sparse`, verify DeepSpeed sparse attention and Triton compatibility. If the user only needs image-axis sparse-like attention, use `axial_row`, `axial_col`, or `conv_like` instead.

## CUDA allocation passes but training fails

A one-tensor CUDA smoke proves only that torch sees a device. Full training can still fail due to memory, checkpoint shape, W&B/network, data loader workers, torch/extension ABI, or model size. Reduce the problem to data validation and tiny API smokes before launching full training.
