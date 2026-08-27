# Hummingbird Model I/O

This reference covers saving/loading converted Hummingbird containers. It applies
to ONNX output as well as the shared Torch, TorchScript, and TVM container load
patterns exposed by `hummingbird.ml`.

## Public entry points

| Converted backend | Save call | Specific load call | Generic load call | Runtime requirement |
| --- | --- | --- | --- | --- |
| `torch` / `pytorch` | `digest = hb_model.save("model_name")` | `hummingbird.ml.TorchContainer.load("model_name", digest=digest)` | `hummingbird.ml.load("model_name", digest=digest)` | `torch` |
| `torch.jit` / `torchscript` | `digest = hb_model.save("model_name")` | `hummingbird.ml.TorchContainer.load("model_name", digest=digest)` | `hummingbird.ml.load("model_name", digest=digest)` | `torch` |
| `onnx` | `digest = hb_model.save("model_name")` | `hummingbird.ml.ONNXContainer.load("model_name", digest=digest)` | `hummingbird.ml.load("model_name", digest=digest)` | `onnx`, `onnxruntime`, `torch` for version metadata |
| `tvm` | `digest = hb_model.save("model_name")` | `hummingbird.ml.TVMContainer.load("model_name", digest=digest)` | `hummingbird.ml.load("model_name", digest=digest)` | `tvm`, plus the TVM runtime constraints owned by the advanced-backends route |

`hummingbird.ml.load(location, ...)` inspects the saved `model_type.txt` inside
the archive and dispatches to the matching container loader. Use the specific
container loader when you already know the backend and need backend-specific
options; use generic `load` when code should accept any Hummingbird-saved
container.

## Save and load recipe

```python
import hummingbird.ml
from hummingbird.ml import convert

hb_onnx = convert(fitted_model, "onnx", test_input=X)

digest = hb_onnx.save("hb_onnx_model")  # writes hb_onnx_model.zip

# Preferred: verify the archive digest returned by save().
loaded = hummingbird.ml.ONNXContainer.load("hb_onnx_model", digest=digest)

# Equivalent generic route when callers do not want to branch by backend.
loaded_generic = hummingbird.ml.load("hb_onnx_model", digest=digest)

# Only for artifacts from a trusted source when the digest is unavailable.
trusted_loaded = hummingbird.ml.load("hb_onnx_model", override_flag=True)
```

## Archive and path behavior

- `save(location)` writes a zip archive and returns a digest string. If
  `location` is `"hb_model"`, the saved file is `hb_model.zip`; if `location`
  already ends in `.zip`, the final artifact still uses that `.zip` name.
- The unzipped directory name must not already exist when saving; Hummingbird
  asserts before overwriting it.
- Temporary unzipped directories are removed after successful save and after
  normal load.
- Load accepts either the base name (`"hb_model"`) or zip name
  (`"hb_model.zip"`).
- A missing archive raises an assertion error that the zip file does not exist.
- `TorchContainer.load` has a `delete_unzip_location_folder` option for the
  PyTorch/TorchScript loader. `ONNXContainer.load`, `TVMContainer.load`, and
  generic `hummingbird.ml.load` clean up the extracted directory on the normal
  path.

## What is stored

| File in saved archive | Purpose |
| --- | --- |
| `model_type.txt` | Backend discriminator used by generic `hummingbird.ml.load`. Values include `torch`, `torch.jit`, `onnx`, and `tvm`. |
| `model_configuration.txt` | Version metadata for Hummingbird and backend libraries. Loading warns, rather than necessarily failing, when version counts or versions differ. |
| `container.pkl` | Pickled container metadata for ONNX and TVM paths, and TorchScript container metadata. |
| `deploy_model.onnx` | ONNX model payload for ONNX containers. |
| `deploy_model.zip` | Torch/TorchScript payload path used by PyTorch container logic. |
| TVM deploy files | TVM library, graph, and parameter files; use the advanced-backends route for TVM constraints. |

During save, Hummingbird clears stored `test_input` values from container
`extra_config` before pickling. Keep your own representative sample if you need
future conversion-time tracing or validation data.

## Digest and trusted override semantics

Hummingbird save/load uses a digest to protect archive integrity.

| Situation | Expected behavior | Recommended action |
| --- | --- | --- |
| `digest` matches the saved archive | Load succeeds. | Preferred path for saved artifacts. |
| `digest` is omitted and `override_flag=False` | Load raises `RuntimeError` asking for a digest or trusted override. | Retrieve the digest from the save step or verify the source out-of-band. |
| `digest` does not match | Load raises `RuntimeError: Integrity check failed`. | Treat the artifact as corrupt or not the same file. Do not override unless a human explicitly trusts the artifact. |
| `override_flag=True` with no digest | Load skips integrity checking and prints a trusted-source message. | Use only for artifacts from a trusted source when the digest is unavailable. |

Security note: the generic loader can unpickle container metadata. Do not load
artifacts from untrusted sources. A trusted override is not a repair mechanism;
it is a deliberate decision to bypass the digest check.

## Prediction interface after loading

Loaded containers keep the same sklearn-style interface as the converted model:

| Container family | Common inference methods |
| --- | --- |
| Classification | `predict`, `predict_proba` |
| Regression | `predict` |
| Transformer | `transform` |
| Anomaly detection | `predict`, `decision_function`, `score_samples` |

When a loaded ONNX model has `predict` but no `predict_proba`, or `transform`
but no `predict`, first identify the original estimator type. Method mismatch is
often an estimator-kind issue, not an artifact-load issue.
