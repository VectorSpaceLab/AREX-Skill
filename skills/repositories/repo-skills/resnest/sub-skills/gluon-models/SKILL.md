---
name: gluon-models
description: "Use optional MXNet Gluon ResNeSt models, pretrained parameter
  cache behavior, ImageNet recipes, and backend troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Gluon Models

Use this sub-skill when the user wants the MXNet Gluon implementation of ResNeSt classifiers, Gluon parameter-store behavior, ImageNet validation/training recipe interpretation, RecordIO requirements, or optional MXNet backend troubleshooting.

Status: Gluon support is optional for this repo skill. The minimum inspected environment did not install MXNet, GluonCV, Horovod, MPI, ImageNet data, or Gluon pretrained parameters. Treat all runtime checks here as conditional on the user's environment having compatible optional dependencies.

## Route by request

- For Gluon model constructors, `get_model`, `get_model_list`, `ctx`, `pretrained`, `root`, `classes`, and `dilation`, read [references/api-reference.md](references/api-reference.md).
- For tiny inference, ImageNet validation, RecordIO data, and distributed training recipe interpretation, read [references/workflows.md](references/workflows.md).
- For missing MXNet/GluonCV, pretrained download/cache/hash failures, RecordIO layout problems, CUDA/Horovod requirements, and API misuse, read [references/troubleshooting.md](references/troubleshooting.md).
- Run [scripts/gluon_tiny_inference.py](scripts/gluon_tiny_inference.py) when you need a safe local Gluon smoke check; it defaults to random input, CPU, and `pretrained=False`, so it does not use the network unless `--pretrained` is explicitly set.

## Boundaries

- Use this sub-skill only for `resnest.gluon` and MXNet Gluon workflows.
- Route PyTorch package, Torch Hub, PyTorch training, and PyTorch Split-Attention usage to `pytorch-models`.
- Route Detectron2 backbone/FPN, COCO configs, and Detectron2 train/eval launchers to `detectron2-backbones`.
- Do not install Horovod, MPI, CUDA wheels, or MXNet as a default action. Ask for the user's target backend and constraints before changing an environment.
