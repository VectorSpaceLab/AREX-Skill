# Installation and Backend Notes

## Purpose

Read this before installing TurboDiffusion, diagnosing import/build failures, or choosing CUDA/SLA/SageSLA options. Full generation is CUDA-first; parser checks and command rendering are safe without model execution.

## Public installation patterns

TurboDiffusion documents Python `>=3.9`, `torch>=2.7.0`, and recommends `torch==2.8.0` because newer versions may cause out-of-memory behavior for the documented workflows.

Typical package install:

```bash
conda create -n turbodiffusion python=3.12
conda activate turbodiffusion
pip install turbodiffusion --no-build-isolation
```

Typical source install:

```bash
git clone https://github.com/thu-ml/TurboDiffusion.git
cd TurboDiffusion
git submodule update --init --recursive
pip install -e . --no-build-isolation
```

Source builds compile `turbo_diffusion_ops` from CUDA/C++ sources and need:

- a CUDA-capable PyTorch build matching the target environment,
- `nvcc` and CUDA development headers/libraries,
- an initialized CUTLASS submodule,
- enough RAM/build time for CUDA extension compilation,
- `flash-attn` available for the package requirement,
- optional SpargeAttn only when using SageSLA.

## Source-layout import quirk

Several scripts import top-level modules such as `imaginaire`, `rcm`, `ops`, `SLA`, `serve`, and `modify_model`. In a source checkout, documented commands export the package source directory on `PYTHONPATH` before running scripts. If an installed entry point or `python -m ...` command fails with `No module named imaginaire`, `No module named rcm`, or `No module named modify_model`, rerun with a source-layout `PYTHONPATH` that points at the package source directory of the checkout you are using.

Do not hardcode a generated-skill or historical checkout path. Ask the user for their checkout/package location if it is not obvious.

## Backend capability map

| Capability | Required pieces | Verification signal |
| --- | --- | --- |
| Parser/help and command builders | Python runtime plus importable dependencies | `--help` exits 0; bundled builders render commands |
| Custom INT8/FastNorm ops | CUDA PyTorch, compiled `turbo_diffusion_ops`, CUDA GPU | import `turbo_diffusion_ops`; tiny `int8_quant`, `FastRMSNorm`, `FastLayerNorm` smoke passes |
| Plain SLA (`attention_type=sla`) | CUDA/Triton custom attention path | import `SLA`; use real model validation rather than random-tensor numerical checks |
| SageSLA (`attention_type=sagesla`) | SpargeAttn installed in addition to base package | `SLA.core.SAGESLA_ENABLED` true; `SageSparseLinearAttention` constructs |
| Full T2V/I2V generation | CUDA GPU, model checkpoint(s), VAE, text encoder, optional image input, output path | one-shot script writes a video file |
| Training/distillation | multi-GPU/distributed PyTorch, training extras, DCP checkpoints, data shards, logging policy | dry-run config first; full training only after budget/credentials approval |
| TurboT2AV | separate LTX-2/Pixi environment, CUDA stack, HF checkpoints, Gemma access token when needed | `ltx_distillation.tools.run_av_inference_eval` command can run in that environment |

## Common install decisions

- Use `--quant_linear` only when the checkpoint filename/metadata/user confirms a quantized TurboDiffusion checkpoint.
- For large-memory GPUs and unquantized checkpoints, omit `--quant_linear` unless the user asks for the quantized path.
- If `sagesla` fails because SpargeAttn is absent, either install SpargeAttn with `--no-build-isolation` or switch to `sla`/`original` and explain the speed/quality trade-off.
- Do not install broad training extras (`megatron-core`, `hydra-core`, `wandb`, `webdataset`, `transformer_engine[pytorch]`) unless the user is actually preparing rCM/SLA training.
- Do not install or run TurboT2AV dependencies inside the core TurboDiffusion environment; TurboT2AV documents an isolated LTX-2/Pixi setup.

## Safe diagnostics

Use the root [environment diagnostic script](../scripts/check_turbodiffusion_env.py) for a no-download check. Use the backend sub-skill's [acceleration diagnostic](../sub-skills/acceleration-backends/scripts/check_acceleration_backend.py) when the question is specifically about custom ops, FastNorm, INT8, SLA, or SageSLA.
