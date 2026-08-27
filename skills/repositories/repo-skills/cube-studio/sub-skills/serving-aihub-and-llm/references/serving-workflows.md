# Serving workflows

CubeStudio has two closely related serving paths:

1. a user-authored `Service` record for general containerized internal services
2. an `InferenceService` record for model-serving frameworks and deployment tuning

## Service lifecycle

- `Service` stores the image, command, environment, working directory, ports, resources, node selector, host, and replica count.
- The `Service` view exposes deploy / clear actions and derives host and IP links from the cluster/domain configuration.
- The service form allows the operator to set the container image, mount, command, env, GPU count, and a homepage path.
- A service can be static or can expose a framework-specific endpoint.

## Inference-service lifecycle

- `Training_Model.deploy` creates or reuses an `InferenceService` record from a training artifact.
- `InferenceService` stores `service_type`, `model_name`, `model_version`, `model_path`, `inference_config`, `ports`, `metrics`, `health`, `hpa`, `cronhpa`, `sidecar`, and scale limits.
- The inference-service form differs from the generic service form because it carries model metadata and framework-specific launch defaults.
- A trained model can be published into a service with the same name/version or into a derived service name.

## AIHub and chat flow

- `Aihub` records cards for visual, audio, language, multimodal, and large-model content.
- The AIHub card view points users toward development, training, and deployment actions.
- `Chat` and `ChatLog` store user-facing chat scenarios and prompt/service configuration.
- Chat can target an OpenAI-compatible service or a CubeStudio AIHub-style service payload.

## What to inspect first

- service type and model path shape
- port list and health/metrics endpoint
- node selector and GPU request
- HPA or cronHPA settings
- sidecar configuration and optional commercial flags
- deployment links, rollback expectations, and route labels

## Native evidence

- `view_inferenceserving.py` defines the service types and default framework constants.
- `view_serving.py` defines the generic service form and host handling.
- `view_train_model.py` shows how a trained model becomes a deployable inference service.
- `view_aihub.py` and `view_chat.py` define the catalog and gateway-oriented views.
