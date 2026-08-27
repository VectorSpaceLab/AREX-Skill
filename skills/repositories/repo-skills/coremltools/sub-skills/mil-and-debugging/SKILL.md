---
name: mil-and-debugging
description: "Advanced coremltools MIL Builder, pass pipeline, custom op, typed
  execution, and debugging workflows for isolating conversion and runtime
  failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# MIL and debugging

Use this sub-skill when the task is about advanced coremltools internals rather than an ordinary framework-to-Core ML recipe:

- Build or inspect MIL Builder programs, functions, `input_specs`, op names, dtypes, and shapes.
- Control graph pass pipelines, bisect pass-related failures, or set graph pass options.
- Diagnose deployment-target compatibility, typed execution, precision regressions, or backend-specific ML Program versus neural network behavior.
- Register composite or custom operators and understand when custom layers are only viable for the neural network backend.
- Use experimental `MLModelInspector`, `MLModelValidator`, `MLModelComparator`, Torch comparators, or submodel extraction to isolate conversion/runtime failures.

Do **not** use this sub-skill for routine conversion recipes; route those to the sibling `convert-models` sub-skill. Route saved-model loading, artifact metadata, prediction, and packaging operations to `model-io-and-prediction`. Route palettization, pruning, quantization, and compression workflows to `optimize-models`.

## Operating map

1. Classify the failure stage: MIL construction/type inference, graph passes, backend lowering/save, deployment compatibility, or Core ML runtime/prediction.
2. Use [API reference](references/api-reference.md) for exact import paths and capability boundaries.
3. Use [workflows](references/workflows.md) for concrete triage sequences and code skeletons.
4. Use [troubleshooting](references/troubleshooting.md) for symptom-to-action mapping, especially native BlobWriter/runtime issues and experimental debugger limitations.
5. For a minimal environment probe, run [scripts/mil_smoke.py](scripts/mil_smoke.py) with `--help`, then choose `--convert-to mlprogram` or `--convert-to neuralnetwork` based on the backend under investigation.

## Minimal smoke command

```bash
python scripts/mil_smoke.py --convert-to mlprogram --output mil_smoke.mlpackage
python scripts/mil_smoke.py --convert-to neuralnetwork --output mil_smoke.mlmodel
```

The smoke script intentionally avoids prediction by default because Core ML prediction and intermediate-output retrieval are runtime-dependent and commonly require macOS or configured remote-device support.
