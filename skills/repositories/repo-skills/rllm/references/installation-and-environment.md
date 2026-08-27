# Installation and Environment Notes

## Package facts captured for this skill

- Main package: `rllm`, source metadata version `0.3.0.pre`, Python `>=3.10`.
- Sibling package: `rllm-model-gateway`, source metadata version `0.1.0`, Python `>=3.10`.
- CLI entry points: `rllm = rllm.cli.main:cli`; `rllm-model-gateway = rllm_model_gateway.server:main`.
- The editable inspection environment proved core imports, CLI help, gateway imports, and CUDA visibility, but runtime users must still install the backend extra and credentials for the workflow they run.

## Installation patterns

For a source checkout:

```bash
uv pip install -e .
# or
python -m pip install -e .
```

For package use from Git or an index, install the `rllm` distribution plus only the extras needed by the task. Avoid `all` unless the user explicitly wants a heavy, broad environment.

## Optional dependency groups

| Extra | Use when | Notes |
| --- | --- | --- |
| `tinker` | Tinker RL or SFT backend | Requires Tinker credentials and Python compatible with the Tinker client stack. Full training is service-backed. |
| `verl` | Local distributed RL/SFT through Verl | Heavy dependency; expects CUDA/GPU for realistic runs. Separated/async Verl training also requires a matching `cupy` wheel. |
| `fireworks` | Fireworks managed RL/SFT backend | Requires `FIREWORKS_API_KEY`; Fireworks SDK imports are deferred until backend execution. |
| `agentcore` | AgentCore remote runtime workflows | Requires AgentCore/Boto/runtime credentials and backend-specific setup. |
| `ui` | `rllm login`, live UI logging, and result browsing helpers | UI login is optional for local CLI/eval execution. |
| `tools`, `code-tools`, `swe`, `web`, `langgraph`, `strands`, `smolagents`, `harbor`, `rewards`, `opentelemetry` | Optional harnesses, tool integrations, reward helpers, observability, or benchmark families | Install only when a selected harness/dataset/runtime requires it. |
| `dev` | Repository development and tests | Not required for package-user workflows. |

## Backend readiness levels

- **Core ready:** `import rllm`, `rllm --help`, decorators, data classes, dataset registry, and gateway model classes import successfully.
- **Evaluation ready:** core ready plus provider config or explicit OpenAI-compatible `--base-url`/`--model`; sandbox backend installed only if the benchmark/agent/verifier needs it.
- **Training ready:** evaluation ready plus a selected backend extra (`tinker`, `verl`, or `fireworks`) and its hardware/credential requirements.
- **Gateway ready:** `rllm_model_gateway` imports, `rllm-model-gateway --help` works, and workers/providers are reachable from the environment that will call the gateway.

Use `scripts/rllm_smoke_check.py` for a safe readiness summary. It does not replace actual backend runtime verification for required GPU/service-backed training.
