# Cross-Cutting Troubleshooting

## Import or entry-point failures

- `ModuleNotFoundError: rllm`: install the package in the active Python environment. For source work, use an editable install from the checkout; for package work, install the `rllm` distribution and only the extras required by the workflow.
- `ModuleNotFoundError: rllm_model_gateway`: the sibling gateway package is missing from the install. Reinstall from a source distribution/checkout that includes the gateway package.
- `rllm --help` works but backend imports fail: this is expected for optional backends. Install `tinker`, `verl`, `fireworks`, `agentcore`, or other extras only when the selected workflow needs them.
- Docs or old examples that import `rllm.sdk` are not authoritative for this revision; the inspected source exposes top-level decorators and types under `rllm`, `rllm.types`, `rllm.eval`, `rllm.trainer`, and `rllm_model_gateway`.

## Provider and model configuration

- If `rllm eval` reports missing setup, use `rllm model setup` or pass both `--base-url` and `--model` explicitly.
- `--base-url` without `--model` is not enough because the OpenAI-compatible client still needs a model string.
- Provider credentials are external state: OpenAI/OpenRouter-style keys, Tinker keys, Fireworks keys, UI login, and remote sandbox credentials must be validated for the target environment.

## Sandbox and snapshot issues

- Sandbox work is triggered by three signals: the flow declares `needs_env`, the verifier kind needs a sandbox, or the task metadata/benchmark layout declares an environment. If no consumer can use a task-declared environment, rLLM warns and skips provisioning.
- Docker/local sandboxes are local; remote backends such as Modal/Daytona/E2B/Runloop/GKE may need tunnels and credentials.
- Snapshots are an optimization, not a correctness requirement. Use `--no-snapshot` to debug cold-start behavior and `rllm snapshot` only when the backend supports snapshot builds.

## Training/backend issues

- Do not treat a CPU import check as proof of a local `verl` or service-backed training run. Full RL/SFT verification requires the selected backend and hardware/credentials.
- For Verl separated/async training, install the `cupy` wheel matching CUDA (`cupy-cuda12x` or `cupy-cuda13x`) or validation fails before the confusing downstream checkpoint-engine error.
- Tinker and Fireworks training are service-backed and may warn or fail on sampling/logprob settings that are legal for eval but unsafe for policy optimization.
- Read `../sub-skills/training/references/backend-matrix.md` before changing backend-specific config.

## Where to go next

- Agent/evaluator protocol errors: `../sub-skills/evaluation/references/troubleshooting.md`.
- Dataset/task layout or verifier metadata errors: `../sub-skills/datasets/references/troubleshooting.md`.
- CLI setup, login, snapshot, and project scaffolding errors: `../sub-skills/cli-ops/references/troubleshooting.md`.
- Backend validation and gateway trace-enrichment errors: `../sub-skills/training/references/troubleshooting.md`.
