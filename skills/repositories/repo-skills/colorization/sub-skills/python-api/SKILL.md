---
name: python-api
description: "Programmatic Python API for the colorizers package: constructors,
  preprocessing/postprocessing helpers, tensor shape contracts, SIGGRAPH hints,
  and no-download smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# colorization Python API

Use this sub-skill when the task is to use the `colorizers` package from Python: imports, model constructors, forward calls, Lab preprocessing/postprocessing helpers, tensor/data shape contracts, SIGGRAPH hint inputs, or no-download API smoke checks.

## Start here

- API surface and call signatures: [references/api-reference.md](references/api-reference.md)
- RGB/Lab/tensor data conventions: [references/data-formats.md](references/data-formats.md)
- Common failures and fixes: [references/troubleshooting.md](references/troubleshooting.md)
- Local diagnostic helper: [scripts/api_smoke.py](scripts/api_smoke.py)

## Routing

- Stay in this sub-skill for programmatic model construction, helper-function use, forward-signature questions, tensor shape/range debugging, and smoke tests that avoid pretrained downloads.
- For end-to-end image-file colorization, CLI invocation, saving output images, or batch output management, use the sibling `automatic-colorization` sub-skill instead.
- Training workflows and the unsupported Caffe branch are out of scope.

## Safety defaults

- Use `eccv16(pretrained=False)` and `siggraph17(pretrained=False)` for import/API tests that must not access the network.
- Calling `eccv16()` or `siggraph17()` without arguments requests pretrained weights because both wrappers default `pretrained=True`.
- Keep model tensors, L tensors, SIGGRAPH hint tensors, and masks on the same device before `forward`; move model outputs to CPU before postprocessing when needed.
