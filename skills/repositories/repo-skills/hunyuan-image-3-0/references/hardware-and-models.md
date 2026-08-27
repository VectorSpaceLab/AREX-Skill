# Hardware and Model Notes

## Model families

| Model | Main workflow | Checkpoint source signal | Recommended VRAM from repo docs | Notes |
|---|---|---|---|---|
| HunyuanImage-3.0 | text-to-image | `tencent/HunyuanImage-3.0` | at least `3 x 80 GB` | Base checkpoint; prompt rewrite is external/manual rather than the instruct self-rewrite path. |
| HunyuanImage-3.0-Instruct | T2I, TI2I, prompt self-rewrite, CoT think | `tencent/HunyuanImage-3.0-Instruct` | at least `8 x 80 GB` | Preferred for editing and multi-image fusion. |
| HunyuanImage-3.0-Instruct-Distil | same instruct workflows with fewer steps | `tencent/HunyuanImage-3.0-Instruct-Distil` | at least `8 x 80 GB` | Use `diff_infer_steps=8` for the repo's distilled recipe. |

Rename downloaded local checkpoint directories to dot-free names before using
them as local paths, for example:

- `HunyuanImage-3`
- `HunyuanImage-3-Instruct`
- `HunyuanImage-3-Instruct-Distil`

## CUDA and PyTorch

The repo documents CUDA 12.8 and PyTorch 2.8.0-style setup. The generated skill
verified a CUDA smoke with:

- PyTorch `2.8.0+cu128`
- torchvision `0.23.0`
- CUDA runtime `12.8`
- NVIDIA A100 GPUs visible to torch

A successful tiny CUDA allocation only proves backend viability. It does not
prove that a full 80B checkpoint fits in memory.

## Optional accelerators

- `flashinfer-python==0.5.0` can improve MoE inference speed when compatible.
- FlashAttention is optional for `flash_attention_2` attention.
- Both accelerator paths must match the installed torch/CUDA ABI. If they are
  missing, use `moe_impl="eager"` and `attn_implementation="sdpa"`.

## Memory planning

Treat the README VRAM numbers as hard planning guidance for full native runs.
If the environment has less memory per GPU than the table recommends:

1. Keep import/API and command-render checks separate from generation checks.
2. Prefer distilled or lower-step recipes only when the checkpoint itself is
   compatible with the hardware.
3. Avoid claiming native generation verification from CPU or parser-only tests.
4. Record OOM risk before starting a long GPU job.

## vLLM deployment hardware

The vLLM wrapper uses tensor parallel size `8`, disables prefix/chunked prefill,
sets `--gpu-memory-utilization 0.6`, and assumes the custom HunyuanImage-3.0
vLLM branch. Change tensor parallelism only when the serving topology and
checkpoint placement have been planned deliberately.
