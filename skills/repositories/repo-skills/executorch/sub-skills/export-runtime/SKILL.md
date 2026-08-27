---
name: export-runtime
description: "Export PyTorch models to ExecuTorch .pte/.ptd programs and
  validate them with Python or C++ runtime APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# export-runtime

Use this sub-skill when the user needs to convert a PyTorch model into an ExecuTorch runtime artifact, validate a `.pte` or `.pte` + `.ptd` pair, reason about dynamic shapes, add basic backend-aware quantization, or debug failures that occur between `torch.export` and runtime loading.

## Scope

This sub-skill owns:

- Standard `.pte` export: `model.eval()` -> example inputs -> `torch.export.export()` -> `executorch.exir.to_edge_transform_and_lower()` -> `.to_executorch()` -> write `buffer`.
- Optional program-data separation: emit `.pte` plus `.ptd` when constants/weights must be stored outside the program file.
- Experimental `executorch.export` session/recipe APIs when the user wants a higher-level export pipeline, target recipes, calibration samples, or multi-backend composition.
- Dynamic shape bounds and runtime shape-mismatch recovery.
- Basic PT2E quantization placement in the export pipeline; backend-specific quantizer details belong to backend sub-skills.
- Python runtime smoke validation, Python pybindings validation for `.ptd`, and C++ `Module`/`TensorPtr` integration patterns.
- CV tensor contracts: shape/layout/dtype/color/normalization/output assumptions that must be preserved through export and app runtime code.
- Export/runtime troubleshooting directly tied to `.pte`/`.ptd`, runtime method loading, missing pybindings, static memory planning, and delegation visibility.

Do not use this sub-skill for general installation/build setup, backend choice, vendor SDK setup, profiling deep dives, LLM-specific flows, Cortex-M details, Qualcomm details, or binary-size work. Route those to the sibling sub-skills `setup-build`, `backend-selection`, `profiling-debugging`, `llm-workflows`, `cortex-m`, `qualcomm`, or `binary-size`.

## Fast path

1. Confirm the user can instantiate the PyTorch model locally and can provide representative example inputs.
2. Confirm target runtime artifact(s): `.pte` only, or `.pte` + `.ptd` for program-data separation.
3. Confirm target backend intent:
   - Portable/no delegate: safest for functional validation.
   - XNNPACK/mobile CPU or other delegates: route backend choice and partitioner setup to `backend-selection`, then return here for the export/runtime sequence.
   - Vendor flows such as QNN or Cortex-M: route to the dedicated sibling sub-skill first.
4. Export in eval mode and keep input contracts explicit. Use [references/export-workflows.md](references/export-workflows.md) for command and code templates.
5. Validate before device integration:
   - Python runtime for ordinary `.pte` files.
   - `executorch.extension.pybindings.portable_lib._load_for_executorch(pte, ptd)` for program-data separation.
   - C++ `Module`/`TensorPtr` when validating app/native integration. Use [references/runtime-integration.md](references/runtime-integration.md).
6. If export, lowering, delegation, or runtime loading fails, diagnose with [references/troubleshooting.md](references/troubleshooting.md) before changing model code.

## Canonical snippets

### Direct export to `.pte`

```python
import torch
from executorch.exir import to_edge_transform_and_lower

model = MyModel().eval()
inputs = (torch.randn(1, 3, 224, 224),)

exported = torch.export.export(model, inputs)
program_manager = to_edge_transform_and_lower(exported).to_executorch()

with open("model.pte", "wb") as f:
    f.write(program_manager.buffer)
```

Add backend partitioners only after the backend choice is clear:

```python
program_manager = to_edge_transform_and_lower(
    exported,
    partitioner=[XnnpackPartitioner()],
).to_executorch()
```

### Python runtime validation

```python
from executorch.runtime import Runtime

runtime = Runtime.get()
program = runtime.load_program("model.pte")
method = program.load_method("forward")
outputs = method.execute([input_tensor])
```

Compare representative outputs against eager PyTorch with task-appropriate tolerances before moving to app code or device-only backends.

## Bundled helper

Use the bundled smoke script for a deterministic local export check that does not download assets and does not require the source checkout:

```bash
python scripts/export_smoke.py --help
python scripts/export_smoke.py --output-dir /tmp/executorch-export-smoke
python scripts/export_smoke.py --output-dir /tmp/executorch-export-smoke --dynamic
python scripts/export_smoke.py --output-dir /tmp/executorch-export-smoke --recipe-api
```

The script reports import availability, writes a tiny `.pte`, optionally writes `.ptd`, and validates via the Python runtime when the installed ExecuTorch package includes runtime pybindings.

## Evidence provenance

Distilled from ExecuTorch documentation for getting started, export/lowering, quantization, CV model handling, runtime overview, Python/C++ runtime API references, Module and Tensor extensions, pybindings notes, the public EXIR/export/runtime package initializers, export pipeline source/tests, and curated export pitfall notes. Runtime files intentionally do not link to the source checkout.