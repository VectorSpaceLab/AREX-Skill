# Inference frameworks

CubeStudio distinguishes several serving frameworks and exposes different defaults for each one.

## Framework summary

| Service type | Model-path expectation | Typical ports | Health | Metrics |
| --- | --- | --- | --- | --- |
| `serving` | user-defined | user-defined | user-defined | user-defined |
| `ml-server` | sklearn / xgb artifact path | custom | custom | custom |
| `tfserving` | `saved_model` directory | `8501` | `8501:/v1/models/$model_name/versions/$model_version/metadata` | `8501:/metrics` |
| `torch-server` | `.mar` or TorchScript artifact | `8080,8081` | `8080:/ping` | `8082:/metrics` |
| `triton-server` | `onnx:` prefixed repo path, or other Triton backends | `8000,8002` | `8000:/v2/health/ready` | `8002:/metrics` |

## Distilled defaults from the source

- `tfserving` uses a TensorFlow serving entrypoint with model, monitoring, and platform config files.
- `torch-server` uses TorchServe, copies the model into the model store, and starts with the framework config properties.
- `triton-server` uses `tritonserver --model-repository=/models/ --strict-model-config=true --log-verbose=1`.
- `tfserving` adds TensorFlow environment settings such as `TF_CPP_VMODULE=http_server=1` and `TZ=Asia/Shanghai`.
- `torch-server` uses a config map block with inference, management, and metrics addresses plus CORS and queue settings.

## Resource and selector semantics

- `resource_gpu` is user input, but the runtime selector flips to GPU placement when the parsed quantity is at least 1.
- The node selector adds a model-type-specific label such as `serving` or `notebook` depending on the view/model family.
- `service_type_choices` in the serving UI include commercial / platform variants beyond the open default frameworks.
- HPA and cronHPA fields are string-based and are validated by the form / UI layer rather than a Python type system.

## Sidecars and optional flags

CubeStudio's serving UI references optional sidecars such as:

- `istio`
- `rate_limit`
- `jwt`
- `monitor`
- `whitelist`
- `quotalimit`
- `security`
- `search`
- `retry`
- `desensitization`
- `prompt`
- `value_map`
- `value_fixed`

These are not all open-source defaults; some are commercial or platform-specific options.

## What to validate before deployment

- the model path matches the chosen framework
- the host/domain path is legal for the chosen cluster
- ports, metrics, and health endpoints agree with the framework choice
- the model version and model name match the training artifact
- the image and registry are available to the target cluster

## Native evidence

- `view_inferenceserving.py` defines `INFERNENCE_*` constants and the `InferenceService` form.
- `view_train_model.py` repeats the framework model-path guidance for trained-model deployment.
- `images/serving/*` contains the framework image build recipes used as catalog evidence.
