# ONNX and Model I/O Troubleshooting

Use this table before changing backends, reinstalling broad optional extras, or
bypassing load integrity checks.

## ONNX conversion and runtime failures

| Symptom or error | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'onnxruntime'` or `ONNX Container requires ONNX runtime installed.` | The `onnx` package is installed, but ONNX Runtime is not importable in the same environment. | Install the ONNX extra or `onnxruntime` in the runtime environment. Re-run `python scripts/onnx_conversion_smoke.py --json`. Use the advanced-backends route before choosing GPU-specific `onnxruntime-gpu`. |
| `onnx` imports, but `convert(..., "onnx", X)` fails when creating/predicting with the container | `onnx` serializes models; Hummingbird's `ONNXContainer` executes them through `onnxruntime`. | Treat `onnxruntime` as required for Hummingbird ONNX inference and saved ONNX container loads. |
| `RuntimeError: Backend onnx requires test inputs` | A non-ONNX source model is being converted to ONNX without representative tracing input. | Pass `test_input=X` or set `extra_config[constants.TEST_INPUT]` to a representative `numpy.ndarray` or supported input tuple. Match the intended inference shape and dtype. |
| ONNX-ML source conversion complains that it cannot fetch input name, data type, or shape | The ONNX graph schema is incomplete or too dynamic for Hummingbird to synthesize tracing input. | Pass explicit `test_input`; use named tensor inputs when creating the ONNX-ML model. |
| `Input data type ... not supported` while converting an ONNX-ML model with omitted `test_input` | Hummingbird auto-generates ONNX-ML tracing inputs only for float32, float64, int32, and int64 tensor types. | Provide explicit `test_input` if the converter supports that data path, or change the ONNX-ML export to a supported numeric tensor type. |
| ONNX-ML model has multiple inputs and conversion fails on shape assertions | Auto-generated inputs must have the same inferred shape. | Provide an explicit tuple of arrays whose widths match each graph input, or rebuild the ONNX-ML model with compatible input schemas. |
| String ONNX-ML or preprocessing model fails during ONNX backend conversion | String tensors are not part of Hummingbird's auto-generated ONNX-ML test-input path, and exporter/runtime support depends on model shape and PyTorch behavior. | Pass explicit string `test_input` only when the source workflow supports it, set `constants.MAX_STRING_LENGTH` when needed, and validate with a tiny fixture. Route complex string/pipeline layout questions to sklearn-pipelines-and-operators. |
| `MissingBackend` for `"onnx"` | Backend string normalization did not find ONNX support, usually because the runtime package set is incomplete or the backend name is misspelled. | Verify `hummingbird.ml.backends` includes `onnx`; use the smoke script to check package imports. |

## ONNX-ML tooling failures

| Symptom or error | Likely cause | Recovery |
| --- | --- | --- |
| `ONNXMLTOOLS not installed` or `ModuleNotFoundError: No module named 'onnxmltools'` | The environment lacks ONNX-ML conversion tooling. | Install the ONNX extra or install `onnxmltools` in the same environment. If optional source packages are also missing, route their installs to optional-source-models. |
| `ModuleNotFoundError: No module named 'skl2onnx'` | The sklearn-to-ONNX converter is absent. | Install the ONNX extra or `skl2onnx`; then rerun the smoke with `--onnxml` if validating ONNX-ML recipes. |
| `onnxmltools` is installed but import fails with `No module named 'pkg_resources'` | The environment is missing or has a broken `setuptools` installation that `onnxmltools` imports through `pkg_resources`. | Install or repair `setuptools` in the same environment; do not reinstall unrelated heavy source-model extras unless they are needed. |
| ONNX-ML predictions and Hummingbird predictions disagree | Output ordering can differ between label and probability outputs, or the wrong prediction method is being compared. | Compare labels from `predict` to label outputs and probabilities from `predict_proba` to probability outputs. For regression, compare `predict` to the single numeric output. |

## Save/load and digest failures

| Symptom or error | Likely cause | Recovery |
| --- | --- | --- |
| `RuntimeError: No digest provided... set override_flag to True` | Loading a saved artifact without the `digest` returned by `save()` and without an explicit trusted override. | Preferred: recover the digest from the save step and call `load(location, digest=digest)`. Only use `override_flag=True` after deciding the archive source is trusted. |
| `RuntimeError: Integrity check failed` | The provided digest does not match the current archive bytes. | Treat the artifact as modified, corrupted, or mismatched. Re-save or reacquire the model. Do not use override as an automatic fallback. |
| `Zip file ... does not exist` | The load location points to the wrong base path or zip path. | Load with either `"name"` or `"name.zip"` matching the saved archive. Confirm the archive exists before retrying. |
| Save fails because a directory already exists | Hummingbird refuses to save over an existing unzipped directory name. | Choose a fresh output base name or remove the stale extracted directory after verifying it is not needed. |
| Loading warns about missing, extra, or different package versions | The archive's version metadata differs from the current environment or was saved by an older Hummingbird version. | Treat warnings as compatibility signals. Run a tiny prediction parity check after load; rebuild the artifact in the current environment when exact reproducibility matters. |
| `ONNXContainer.load` fails after moving to another environment | The target environment lacks ONNX Runtime or compatible ONNX/PyTorch packages used for container metadata. | Install the ONNX stack in that environment; prefer re-running the bundled smoke before loading production artifacts. |

## Method and interface mismatches

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Converted model has no `predict_proba` | The original estimator is a regressor, transformer, or classifier without probability output support. | Use `predict` for regressors/class labels, `transform` for transformers, and `decision_function`/`score_samples` for anomaly detectors when available. |
| `transform` is present but `predict` is missing | The original model is a transformer/preprocessor. | Compare to the source transform output, not classifier/regressor predictions. |
| `predict` output shape differs from expected probabilities | Labels and probability outputs are different methods. | Use `predict_proba` for probability matrices; use `predict` for labels or regression values. |

## Smoke script diagnostics

Run from this sub-skill directory or provide the script path explicitly:

```bash
python scripts/onnx_conversion_smoke.py --json
python scripts/onnx_conversion_smoke.py --onnxml --json
python scripts/onnx_conversion_smoke.py --output hb_onnx_demo --json
```

Expected outcomes:

- Exit code `0`: tiny ONNX backend conversion and parity checks passed.
- Exit code `2`: a required dependency for the selected smoke mode is missing
  or not importable; the message identifies the import that failed.
- Nonzero assertion/runtime error after dependency checks: inspect the reported
  step, then use the workflow tables above to decide whether the issue is input
  shape, dtype, optional tooling, or artifact integrity.
