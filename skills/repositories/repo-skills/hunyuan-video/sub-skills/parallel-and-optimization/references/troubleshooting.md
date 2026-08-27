# Parallel and Optimization Troubleshooting

## xDiT missing dependency

Symptom:

```text
Ulysses Attention and Ring Attention requires xfuser package.
```

Install and verify `xfuser` in the active HunyuanVideo environment. If `flash-attn` build fails, confirm PyTorch and CUDA versions first; install `ninja`, then rebuild flash-attn against the active stack.

## CPU offload conflict

Distributed mode asserts that `use_cpu_offload` is false. Remove `--use-cpu-offload` from `torchrun` commands and rely on multi-GPU sequence parallelism instead.

## World-size mismatch

Symptom:

```text
number of GPUs should be equal to ring_degree * ulysses_degree
```

Set `--nproc_per_node` equal to `--ulysses-degree * --ring-degree`.

## Sequence split error

If the error says the video sequence cannot be split evenly, choose a documented resolution/degree pair or adjust the degree so the latent spatial dimensions split cleanly.

## Missing FP8 map

FP8 conversion expects `dit_weight.replace('.pt', '_map.pt')`. If `mp_rank_00_model_states_fp8.pt` exists but `mp_rank_00_model_states_fp8_map.pt` does not, download or place the map file before launching.

## Floating point exception or core dump

Use one of the README-backed dependency paths: CUDA 12.4 with compatible CUBLAS/CUDNN, or force CUDA 11.8 PyTorch and reinstall requirements, flash-attn, and xDiT.
