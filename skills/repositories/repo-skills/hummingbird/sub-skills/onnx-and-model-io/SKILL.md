---
name: onnx-and-model-io
description: "Use Hummingbird's ONNX backend, ONNX-ML source conversion, and
  container save/load workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# ONNX and Model I/O

Use this sub-skill when a task mentions ONNX output, ONNX-ML input models,
`onnxmltools`, `skl2onnx`, `onnxruntime`, `ONNXContainer`, saving a Hummingbird
model, loading a saved digest, or deciding whether `override_flag=True` is safe.

## Fast route

1. If the user only needs the basic `hummingbird.ml.convert(...)` or
   `convert_batch(...)` call shape, route to
   [`../core-conversion/SKILL.md`](../core-conversion/SKILL.md) first and return
   here for ONNX-specific dependency, tracing, and artifact choices.
2. For ONNX output from a fitted sklearn-style model, pass representative
   `test_input` and use `backend="onnx"`; read
   [`references/onnx-workflows.md`](references/onnx-workflows.md).
3. For ONNX-ML `ModelProto` inputs produced by `onnxmltools` or `skl2onnx`,
   check the ONNX-ML recipe and schema limits in
   [`references/onnx-workflows.md`](references/onnx-workflows.md).
4. For saved Hummingbird artifacts, load with the digest returned by `save()`
   whenever possible; use `override_flag=True` only for trusted artifacts. Read
   [`references/model-io.md`](references/model-io.md).
5. When conversion or load fails, diagnose from
   [`references/troubleshooting.md`](references/troubleshooting.md) before
   changing backends or bypassing integrity checks.

## Bundled runtime helper

Run [`scripts/onnx_conversion_smoke.py`](scripts/onnx_conversion_smoke.py) to
validate a small ONNX backend conversion without relying on source notebooks or
tests:

```bash
python scripts/onnx_conversion_smoke.py --json
python scripts/onnx_conversion_smoke.py --onnxml --json
python scripts/onnx_conversion_smoke.py --output hb_onnx_demo --json
```

The default smoke trains a tiny deterministic sklearn classifier, converts it to
Hummingbird's ONNX backend, and asserts label/probability parity. `--onnxml`
adds an ONNX-ML source-model check when `onnxmltools`/`skl2onnx` are importable.
`--output` is the only mode that writes an artifact.

## What this sub-skill owns

- ONNX target backend requirements and `onnxruntime` container behavior.
- ONNX-ML input model recipes and `test_input` behavior.
- `constants.ONNX_TARGET_OPSET` and `constants.ONNX_OUTPUT_MODEL_NAME` usage.
- `ONNXContainer`, `TorchContainer`, `TVMContainer`, and generic
  `hummingbird.ml.load` save/load semantics.
- Digest verification, bad-digest failures, and trusted override behavior.
- Prediction interface routing by estimator kind: `predict`, `predict_proba`,
  `transform`, `decision_function`, and `score_samples`.

## Route elsewhere

- Basic conversion syntax, backend aliases, not-fitted estimators, and
  `convert_batch`: [`../core-conversion/SKILL.md`](../core-conversion/SKILL.md).
- LightGBM, XGBoost, SparkML, Prophet, and optional source package installation:
  [`../optional-source-models/SKILL.md`](../optional-source-models/SKILL.md).
- CUDA acceleration, TVM, batching/performance tuning, and GPU-specific runtime
  choices: [`../advanced-backends-and-performance/SKILL.md`](../advanced-backends-and-performance/SKILL.md).

## Minimum safety rules

- Do not treat `onnx` alone as sufficient for Hummingbird ONNX inference;
  `onnxruntime` must be importable for `ONNXContainer` prediction and loading.
- Do not bypass load integrity checks for untrusted artifacts. Prefer
  `digest=save_return_value`; use `override_flag=True` only after an explicit
  trust decision.
- Do not promise CUDA, TVM, LightGBM, XGBoost, Prophet, or SparkML behavior from
  this sub-skill; those paths are optional and routed to their owning sub-skills.
