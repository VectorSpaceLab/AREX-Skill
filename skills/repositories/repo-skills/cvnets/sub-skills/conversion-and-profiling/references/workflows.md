# Conversion and Profiling Workflows

## Purpose

Read this when you need the command pattern for CoreML conversion, throughput benchmarking, or loss-landscape generation.

## Conversion pattern

```bash
python sub-skills/conversion-and-profiling/scripts/cvnets_convert.py \
  --repo-root <repo-root> \
  --common.config-file config/classification/imagenet/resnet.yaml \
  --common.results-loc coreml_models \
  --model.classification.pretrained <weights> \
  --conversion.coreml-extn mlmodel
```

For detection and segmentation, add the task-specific class-count arguments and keep the export-specific preprocessing keys aligned with the recipe.

Useful conversion inputs:

- `--conversion.input-image-path <path>` to provide a concrete image instead of the default random tensor.
- `--common.enable-coreml-compatible-module` is set by the conversion entry point before export.
- `--model.<category>.pretrained <weights>` to load the model before export.
- `--conversion.coreml-extn <ext>` to choose the emitted CoreML file extension.

## Benchmark pattern

```bash
python sub-skills/conversion-and-profiling/scripts/cvnets_benchmark.py \
  --repo-root <repo-root> \
  --common.config-file config/classification/imagenet/resnet.yaml \
  --benchmark.batch-size 1 \
  --benchmark.warmup-iter 10 \
  --benchmark.n-iter 100
```

Useful benchmark inputs:

- `--benchmark.use-jit-model` to benchmark the optimized traced path.
- `--common.mixed-precision` when the device is CUDA and the model supports it.
- `--common.channels-last` if the model and backend support that layout.

## Loss-landscape pattern

```bash
python sub-skills/conversion-and-profiling/scripts/cvnets_loss_landscape.py \
  --repo-root <repo-root> \
  --common.config-file config/classification/imagenet/resnet.yaml \
  --common.results-loc loss_landscape \
  --loss-landscape.n-points 11 \
  --loss-landscape.min-x -1.0 \
  --loss-landscape.max-x 1.0 \
  --loss-landscape.min-y -1.0 \
  --loss-landscape.max-y 1.0
```

## Practical notes

- The benchmark path is intentionally small by default and can be expanded only after the model is known to work.
- CoreML export expects the family to be compatible with the conversion path and may need Mac-specific validation for a full deployment check.
- Loss-landscape runs reuse the training engine but do not run a normal training loop.
