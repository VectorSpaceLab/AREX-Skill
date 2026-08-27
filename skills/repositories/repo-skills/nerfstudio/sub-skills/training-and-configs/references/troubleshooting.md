# Training troubleshooting

## CUDA unavailable

If the task is real training/rendering, check CUDA before starting:

```bash
python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"
```

Install a CUDA-enabled torch wheel compatible with the driver. Do not count a CPU-only import as validation of production Nerfstudio training.

## Out of memory

Reduce the workload before switching methods:

- lower `--pipeline.datamanager.train-num-rays-per-batch`;
- reduce evaluation chunk/ray settings;
- choose `nerfacto` rather than bigger variants;
- reduce image scale in data processing or dataparser settings;
- avoid viewer + extra logger combinations on tight memory.

## `tinycudann` missing

Many components have a torch fallback but default high-performance configs may prefer TCNN. Use a torch implementation for reduced smoke checks, or install tiny-cuda-nn with a matching CUDA toolkit/compiler when full acceleration is required.

## `gsplat` or `nerfacc` errors

These packages must match the installed torch/CUDA ABI. Reinstalling torch without rebuilding/reinstalling extensions can cause import or undefined-symbol errors. Splatfacto and Instant-NGP workflows should remain blocked until their dependencies import correctly.

## Flag rejected or ignored

Use nested help and move the flag to the owning subcommand:

```bash
ns-train METHOD --help
ns-train METHOD DATAPARSER --help
```

Dataparser flags go after the dataparser name, not before it.

## Resume path wrong

Training resume uses checkpoint/model directories such as `nerfstudio_models`. Viewer/eval/render/export generally use the saved `config.yml`. If a checkpoint path exists but a config does not, reconstructing the pipeline is unsafe.
