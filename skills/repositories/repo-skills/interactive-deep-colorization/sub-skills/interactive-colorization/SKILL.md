---
name: interactive-colorization
description: "Guides agents using interactive-deep-colorization local-hints
  colorization APIs, GUI semantics, masks, color suggestions, and saved
  outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# interactive-colorization

Use this sub-skill when a task is about the repository's local-hints interactive colorization workflow: explaining the GUI, reproducing the notebook-style API flow, preparing user hint tensors, choosing PyTorch versus Caffe wrappers, interpreting recommended colors, or handling saved local-hints artifacts.

## Route first

- Read [references/api-reference.md](references/api-reference.md) for class signatures, backend wrapper behavior, CLI defaults, and PyTorch tensor shapes.
- Read [references/workflows.md](references/workflows.md) for GUI interaction semantics, a distilled notebook-style local-hints recipe, and saved-result handling.
- Read [references/data-formats.md](references/data-formats.md) before creating or consuming `input_ab`, `mask`, Lab arrays, recommendation distributions, or saved `.npy`/`.png` artifacts.
- Read [references/troubleshooting.md](references/troubleshooting.md) when imports, GUI launch, backend choice, tensor shape, gamut, color suggestions, or output saving behavior is confusing.

## Boundaries

- For installation, dependency, display, backend setup, and model file acquisition questions, route to [../setup-and-models/SKILL.md](../setup-and-models/SKILL.md).
- For global histogram transfer or reference-image workflows, route to [../global-histogram-transfer/SKILL.md](../global-histogram-transfer/SKILL.md).
- Training is out of scope for this repository skill; the repository points local-hints training to a separate external project.
- Do not treat Caffe, PyQt GUI execution, or downloaded model-weight inference as construction-verified here. Source/API facts and PyTorch architecture smoke behavior are verified; full native GUI/model runs need the setup/model sub-skill gate.

## Safe bundled scripts

- Use [scripts/inspect_cli_defaults.py](scripts/inspect_cli_defaults.py) to inspect distilled GUI CLI parser facts without importing PyQt, qdarkstyle, Caffe, or model weights.
- Use [scripts/smoke_core_helpers.py](scripts/smoke_core_helpers.py) with a repository checkout passed via `--repo-root` to check safe imports, Lab/gamut helpers, wrapper image preparation, and tiny PyTorch architecture forwards without loading model weights or GUI/Caffe modules.

## Critical invariants to preserve

- The local-hints model consumes `input_ab` with shape `2 x Xd x Xd` and `input_mask` with shape `1 x Xd x Xd` before wrapper-specific normalization.
- Verified constructor and method signatures include `ColorizeImageBase(Xd=256, Xfullres_max=10000)`, `ColorizeImageTorch(Xd=256, maskcent=False)`, `ColorizeImageTorchDist(Xd=256, maskcent=False)`, `ColorizeImageCaffe(Xd=256)`, `ColorizeImageCaffeDist(Xd=256)`, `ColorizeImageCaffeGlobDist(Xd=256)`, `ColorizeImageTorch.prep_net(self, gpu_id=None, path='', dist=False)`, `SIGGRAPHGenerator(dist=False)`, and `SIGGRAPHGenerator.forward(self, input_A, input_B, mask_B, maskcent=0)`.
- The GUI CLI has a parser quirk: `--dist_model` stores into `dest='color_model'`, so there is no independent `args.dist_model`; both PyTorch wrapper initializations read `args.color_model`.
