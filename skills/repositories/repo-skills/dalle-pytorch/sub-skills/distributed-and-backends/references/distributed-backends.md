# Distributed backends and attention options

## Backend selection model

The package exposes a small distributed abstraction with three backend classes:

- `DummyBackend`: default single-process behavior.
- `DeepSpeedBackend`: imports `deepspeed`, calls `deepspeed.init_distributed()`, wraps arguments with DeepSpeed config flags, and can save/load DeepSpeed checkpoint directories.
- `HorovodBackend`: imports `horovod.torch`, initializes Horovod, broadcasts parameters/optimizer state, and all-reduces losses.

Training helpers call `distributed_utils.wrap_arg_parser(parser)` and then `set_backend_from_args(args)`. `--distributed_backend deepspeed` or `--distr_backend deepspeed` selects DeepSpeed. `--deepspeed` is handled specially for backward compatibility.

## Safe availability check

```bash
python scripts/check_backend_availability.py --include-cuda
```

The check imports modules and optionally allocates one CUDA tensor. It does not initialize distributed process groups or run training.

## DeepSpeed

Use DeepSpeed when the user needs distributed DALL-E/VAE training, gradient accumulation, fp16, AMP, or sparse attention. The helpers build a Python `deepspeed_config` dictionary at runtime.

Important flags:

- `--deepspeed`: backward-compatible switch that selects DeepSpeed.
- `--distributed_backend deepspeed` / `--distr_backend deepspeed`: explicit backend name.
- `--fp16`: enables DeepSpeed fp16 block in the helper config.
- `--amp`: enables Apex AMP block in the helper config; cannot be combined with some ZeRO stages.
- `--ga_steps`: gradient accumulation steps for DALL-E training.
- `--flops_profiler`: DALL-E helper exits after a profile step.

Sparse attention:

- `attn_types` entries `full`, `axial_row`, `axial_col`, and `conv_like` are package-level attention choices.
- `attn_types` entry `sparse` routes through DeepSpeed sparse attention and requires compatible DeepSpeed/Triton setup.
- The source install helper for DeepSpeed sparse attention clones and builds from source; treat it as reference-only and ask before executing equivalent operations.

Checkpoint notes:

- DeepSpeed checkpoints may be directories named from the requested checkpoint stem plus `-ds-cp`.
- An auxiliary payload can be stored as `auxiliary.pt` inside that directory.
- ZeRO stage 2/3 may require consolidation before ordinary generation.

## Horovod

Use Horovod only when `horovod.torch` is installed and the user wants Horovod launch semantics:

```bash
horovodrun -np <num-gpus> python train_dalle.py ... --distributed_backend horovod
```

The Horovod backend treats the script batch size as local batch size and multiplies effective batch size by worker count. Learning rate may need rescaling.

## Apex AMP

Apex AMP is optional and source-build heavy. The repo's reference install path clones NVIDIA Apex and installs CUDA extensions. Ask before installing; verify CUDA toolkit/compiler and torch ABI first.

## Precision choices

- `--fp16`: DeepSpeed fp16 block; useful for memory reduction but can be unstable.
- `--amp`: Apex O1 mixed precision through DeepSpeed config; requires Apex and is not compatible with all ZeRO stages.
- Single-GPU users may prefer simpler torch/CUDA memory reductions before source-building Apex.
