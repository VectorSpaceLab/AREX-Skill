---
name: pytorch-training
description: "Configure and inspect face.evoLVe PyTorch training, validation,
  checkpoints, and model components."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# face.evoLVe PyTorch Training Router

Use this sub-skill when a task is about face.evoLVe PyTorch training configuration, PyTorch model/backbone/head/loss inspection, legacy PyTorch training-source repair, checkpoint naming/resume behavior, validation during training, or GPU/CPU training expectations.

Do not use this sub-skill for identity-folder creation or low-shot pruning; route those to `data-preparation`. Route MTCNN alignment and crop generation to `face-alignment`, post-training checkpoint feature extraction or ROC verification to `feature-extraction-verification`, and PaddlePaddle training/deployment workflows to `paddle-workflows`.

## Read or run these bundled files

- Read [references/training-workflows.md](references/training-workflows.md) when you need the end-to-end PyTorch config, data-loader, train/validate, checkpoint, tiny-smoke, or skip/full-training decision flow.
- Read [references/model-api-reference.md](references/model-api-reference.md) when you need supported ResNet/IR/IR-SE backbones, advanced source backbones, head signatures, loss signatures, and stable-versus-experimental API status.
- Read [references/configuration.md](references/configuration.md) before editing `config.py` values such as `BACKBONE_NAME`, `HEAD_NAME`, `LOSS_NAME`, data/checkpoint/log roots, optimizer schedule, `MULTI_GPU`, and `GPU_ID`.
- Read [references/troubleshooting.md](references/troubleshooting.md) when PyTorch training or component inspection fails with syntax errors, missing validation data, bcolz/numpy issues, `head.metrics` import errors, GPU placement problems, checkpoint mismatches, or BatchNorm/tiny-batch issues.
- Run [scripts/inspect_pytorch_components.py](scripts/inspect_pytorch_components.py) for a safe parser/import/signature/CPU tensor-shape check of PyTorch components without launching full training.

## Operating defaults

- Prefer README-supported training combinations first: `IR_SE_50` or `IR_50` backbone, `ArcFace` head, and `Focal` or softmax cross-entropy loss.
- Treat full PyTorch training as a user-checkout operation that needs datasets, validation arrays, checkpoint/log directories, compatible dependencies, and usually CUDA GPUs. This sub-skill does not provide a bundled full-training launcher.
- Use the bundled inspection script before modifying full training code. It imports backbone/head/loss modules directly and intentionally avoids importing or executing the training entrypoint.
- If a task asks for an executable tiny CPU smoke, keep it to model/head/loss construction and one synthetic forward pass unless the user supplies a deliberately tiny ImageFolder fixture and accepts source repair work.
