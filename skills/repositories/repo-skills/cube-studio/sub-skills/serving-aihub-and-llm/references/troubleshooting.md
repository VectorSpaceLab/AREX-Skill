# Troubleshooting

## Common inference-service symptoms

### Service never becomes healthy

- the model path does not match the selected framework
- the health endpoint is wrong for the framework
- the container image does not contain the expected runtime
- the service name or version does not match the deployed artifact
- the node selector requests a backend that the cluster does not have

### Metrics or ports are wrong

- the chosen service type does not match the expected default ports
- `ports`, `metrics`, or `health` were edited inconsistently
- the model framework expects an extra management port or metrics port
- the UI values were changed without updating the framework-specific defaults

### Model deployment from training fails

- the training-model record has an empty or wrong `path`
- the model version does not match the inferred service name
- the trained artifact is not in a path the serving framework can read
- the inference-service record already exists with a different configuration

### AIHub or chat requests fail

- the AIHub card metadata does not point to a usable dataset, model, or notebook
- the chat service configuration points to the wrong URL or missing headers
- an OpenAI-compatible gateway is missing tokens, quotas, or transform settings
- a commercial sidecar or chat flag was selected without the required platform feature

## Recovery checks

1. Match the model artifact path to the framework before changing any service flags.
2. Verify the default port / health / metrics trio for the chosen framework.
3. Compare the training-model record, model name, and model version before creating a duplicate service.
4. If the chat scenario fails, inspect `service_config`, `knowledge`, and `prompt` separately.
5. Keep deployment-side image build or cluster install issues in the deployment sub-skill, not here.

## What not to do

- Do not treat a generic container service as if it already includes framework defaults.
- Do not use notebook or training-image guidance as proof that a serving image is correct.
- Do not start or update live services during skill drafting.

## Useful cross-links

- `inference-frameworks.md` for model-path and endpoint expectations
- `serving-workflows.md` for training-model and service lifecycle behavior
- `aihub-and-chat.md` for AIHub and prompt/gateway payloads
