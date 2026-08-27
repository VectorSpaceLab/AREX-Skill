---
name: deployment-and-operations
description: "Operate PaddleViT across configuration, environment,
  AMP/distributed execution, static export, inference, quantization, and
  optional weight porting without conflating model-family semantics or hiding
  backend failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PaddleViT deployment and operations

Use this sub-skill when a task crosses PaddleViT model directories or asks how
an existing model is configured, launched, exported, served, diagnosed, or
ported. It is an operating guide for the repository's standalone projects, not
a replacement for the model-family skills.

## Route and boundaries

- Use [configuration.md](references/configuration.md) before changing a YAML,
  command line, working directory, or checkpoint path.
- Use [distributed-and-amp.md](references/distributed-and-amp.md) for GPU
  selection, `paddle.distributed.spawn`, `DataParallel`, NCCL, or AMP.
- Use [deployment.md](references/deployment.md) for dynamic-to-static export,
  Paddle Inference, preprocessing parity, prediction, and PaddleSlim
  quantization boundaries.
- Use [troubleshooting.md](references/troubleshooting.md) for safe diagnosis
  of import, CUDA/cuDNN, artifact, and launch failures.
- Run the bundled probes before attributing a failure to a model:
  `python scripts/check_paddlevit_environment.py --help`,
  `python scripts/check_paddle_inference.py --help`, and
  `python scripts/validate_checkpoint_manifest.py --help`.

This sub-skill does **not** select a ViT/BEiT/DETR/segmentation/GAN model,
define its dataset or transforms, promise benchmark reproduction, perform
full training, download data or weights, run arbitrary shell strings, or port
weights automatically. Link to the owning model-family skill for those
semantics.

## Operating sequence

1. Identify the concrete model directory and its entry script. PaddleViT is a
   collection of standalone projects rather than one installable package;
   imports such as `from config import ...` are commonly resolved relative to
   the model directory. Prefer an explicit `cd` into that directory and record
   the exact commit, config, checkpoint, output prefix, device selection, and
   preprocessing.
2. Resolve configuration in this order: Python defaults in `config.py`, YAML
   (including its `BASE` chain), then supplied CLI options. CLI values win over
   YAML. Record flags such as `-eval`, `-amp`, `-pretrained`, and `-resume`
   separately because they change control flow, not only scalar values.
3. Probe the installed backend and inference API. Treat CPU import success as
   weaker evidence than a CUDA tensor/layer smoke for GPU claims. Do not copy
   machine-specific loader fixes, `LD_LIBRARY_PATH`, cache paths, or private
   prefixes into a public skill or command.
4. For training, choose single GPU first. Add `-amp` only for training on a
   supported NVIDIA backend and use the distributed procedure only after a
   one-process smoke is healthy. A multi-GPU `batch_size` is per GPU in the
   documented examples.
5. For export, build the dynamic model, load a compatible state dict, call
   `model.eval()`, use an `InputSpec` matching the model's NCHW shape, call
   `paddle.jit.to_static`, and save to an output *prefix*. Verify the three
   expected files before inference:
   `<prefix>.pdmodel`, `<prefix>.pdiparams`, and
   `<prefix>.pdiparams.info`.
6. For exported inference, load the `.pdmodel`/`.pdiparams` pair with
   `paddle.inference.Config`, inspect the predictor's input names, reshape the
   input handle, copy `float32` NCHW data, run, and inspect output names and
   shapes. Reproduce the original resize/crop/channel/order/scale/mean/std
   preprocessing exactly; random input only proves the API path, not accuracy.
7. Keep quantization and weight porting as explicit opt-in boundaries. The
   documented PaddleSlim post-training flow consumes a static model and emits
   its own `__model__`/`__params__` layout; it is not interchangeable with
   Paddle Inference's `.pdmodel`/`.pdiparams` files. PyTorch/timm porting needs
   a manually reviewed parameter-and-buffer mapping, Linear transpose checks,
   and batched `allclose` comparison before saving `.pdparams`.
8. On failure, classify first (path/config, Python import, backend loader,
   distributed rendezvous, export graph, artifact manifest, preprocessing,
   or numerical parity). Apply the smallest local diagnostic, preserve the
   original error, and stop rather than weakening a required backend claim.

## Safe command policy

Commands in this guide are templates. Substitute quoted, user-owned paths only
after checking them. Probes are read-only and do not download, overwrite,
extract, delete, or alter environment state. Training, multi-process launch,
export, quantization, and checkpoint conversion are operational actions: ask
for explicit approval and use a new output directory/prefix rather than a
source or checkpoint path. `CONTRIBUTING.md` supports normal review and test
expectations; it is not a release/deployment contract.

## Evidence and limits

This guide was distilled from `docs/paddlevit-config.md`,
`paddlevit-amp.md`, `paddlevit-multi-gpu.md`, `paddlevit-export-en.md`,
`paddlevit-quant-cn.md`, `paddlevit-port-weights.md`,
`image_classification/BEiT/export_models.py`,
`image_classification/BEiT/infer_exported_models.py`,
`image_classification/T2T_ViT/export_models.py`, representative config/main
parsers, and `CONTRIBUTING.md`. The requested `docs/paddlevit-predict-en.md`
was not present in this checkout; the available
`docs/paddlevit-predict-cn.md` was used for the custom prediction boundary.
The checked-in T2T export example also has an invalid `name='x'` placement in
its `InputSpec` list and is explicitly treated as reference-only until fixed.
Installed construction facts include passing Paddle Inference import, Paddle
GPU 2.6.2, and a tiny CUDA smoke. This host required a private cuDNN runtime
loader setup; that setup is intentionally not prescribed here.

