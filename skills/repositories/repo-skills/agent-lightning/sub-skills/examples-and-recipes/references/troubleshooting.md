# Example troubleshooting

## Missing optional dependency

**Symptom**

`ModuleNotFoundError` for `poml`, `verl`, `vllm`, `torch`, `langchain`, `pymongo`, `weave`, `tinker`, `wandb`, `swebench`, or provider SDKs.

**Fix**

Check [dependency-and-backend-matrix.md](dependency-and-backend-matrix.md) and install only the group needed for the selected example. Do not install every optional group into a small CPU environment.

## API key or hosted service failure

**Symptom**

Authentication errors, quota errors, unknown model, deployment not found, or SDK client initialization failure.

**Fix**

- Confirm the user supplied credentials or a local endpoint.
- Verify the endpoint with `cli-and-services/scripts/check_litellm_proxy.py` when OpenAI-compatible.
- Never print secrets.
- Stop before launching fine-tuning, deployment, or cleanup without explicit approval.

## GPU/CUDA/vLLM/torch conflict

**Symptom**

Torch cannot see CUDA, vLLM import fails, flash-attn build errors, or model server exits on startup.

**Fix**

- Verify driver/GPU availability before installing heavy stacks.
- Use repository-compatible torch/vLLM groups rather than arbitrary latest packages.
- Run a tiny CUDA allocation or vLLM help/startup check before full training.
- Keep GPU training environments separate from CPU authoring environments.

## Dataset missing or too large

**Symptom**

File-not-found, download failure, schema errors, or unexpectedly long preprocessing.

**Fix**

- Ask whether the user wants to download or provide the dataset.
- Validate a tiny fixture first.
- Document the expected data layout and stop if the workflow depends on large downloads outside the budget.

## Docker/SWE-bench unavailable

**Symptom**

Docker daemon errors, image pull failures, or SWE-bench setup failures.

**Fix**

- Treat Docker/SWE-bench as optional.
- Do not start or stop Docker containers without permission.
- Validate the non-Docker parts of the tracing/agent workflow first.

## Ray restart or cleanup scripts are tempting

**Cause**

The source repository includes operational scripts that restart Ray or clean up cloud/generated resources.

**Fix**

Do not run destructive or credentialed cleanup/restart scripts unless the user explicitly requested that action and understands the side effects. Prefer documenting the precondition or asking for permission.

## Example CI passes but local run fails

**Cause**

CI may use secrets, cached datasets, specific Python/torch/CUDA variants, or marker selection that differs from the local environment.

**Fix**

- Reproduce the exact dependency group and marker set.
- Check whether the example was meant for CPU, GPU, hosted service, or documentation-only validation.
- Use a help-only or tiny-fixture check when full CI parity is not available.
