# Troubleshooting

## Purpose

Use this reference for cross-cutting installation, import, CLI, and optional-backend failures. It points to the sub-skill that owns the deeper workflow details.

## Common failure surfaces

| Symptom or error fragment | Likely cause | Next step | Owning sub-skill |
| --- | --- | --- | --- |
| `ImportError` while importing `agentlightning` or `agl` | Base dependency set or runtime-compatible dependency versions are missing or drifted | Run `python scripts/check_agentlightning_install.py` and review [compatibility](compatibility.md) | root / all |
| `cannot import name 'get_flat_dependant' from 'fastapi.dependencies.utils'` | FastAPI version incompatible with the installed LiteLLM proxy stack | Install a lockfile-compatible FastAPI release and rerun the install smoke | `cli-and-services` |
| `No module named 'prometheus_client'` when running `agl prometheus` | Prometheus client is missing from the environment | Install `prometheus-client` or the repo's dev tooling set, then rerun the CLI help/check | `cli-and-services` |
| `No active tracer found` when emitting rewards/messages/objects | Emitter helpers were used without an active tracer | Enter a tracer lifespan or use `propagate=False` for offline local tests | `tracing-and-instrumentation` |
| `Function signature ... does not match any known agent patterns` from `@rollout` | Agent function signature does not match a supported pattern | Use `task, llm[, rollout]` or `task, prompt_template[, rollout]`, or switch to a class-based `LitAgent` | `agent-authoring` |
| `PROMETHEUS_MULTIPROC_DIR is not set` | The Prometheus service expects the multiprocess directory | Set the environment variable or use the metrics helper with a local, explicit temp directory | `cli-and-services` |
| Rollout stays `queuing`, `preparing`, or `running` unexpectedly | Store, runner, or retry config mismatch | Inspect `RolloutConfig`, `query_rollouts`, `query_spans`, and runner worker state | `runner-store-training` |
| Reward span missing from trace analysis | Agent returned no reward, the final reward was not emitted, or the adapter was not selected | Check `emit_reward`, `find_final_reward`, and the adapter selected by the training loop | `tracing-and-instrumentation` / `runner-store-training` |
| `APO` import fails with `No module named 'poml'` | Optional APO extra is missing | Install the `apo` extra and any required OpenAI-compatible backend | `runner-store-training` / `examples-and-recipes` |
| vLLM / Unsloth / VERL / ChartQA / Spider workflows fail to import or launch | CUDA-oriented extras or matching torch/vLLM wheels are missing | Read the example catalog and install the relevant optional groups before retrying | `examples-and-recipes` |
| Mongo store CLI starts but persistence is unavailable | Mongo backend or replica set was not prepared | Use `LightningStore` in-memory for CPU smoke tests or provision the Mongo service | `runner-store-training` / `cli-and-services` |
| CLI help works but a subcommand crashes on import | An optional dependency for that subcommand is absent | Treat the subcommand as optional and install only its dependency group when needed | `cli-and-services` |

## Recovery patterns

### Install or import problems

1. Confirm the package version and entry points with [scripts/check_agentlightning_install.py](../scripts/check_agentlightning_install.py).
2. Compare the current environment with [compatibility](compatibility.md).
3. Install the missing base or optional dependency group.
4. Re-run the relevant CLI help or smoke script.

### Tracing and reward problems

1. Make sure a tracer is active before emitting spans.
2. Use `OtelTracer` or `AgentOpsTracer` consistently within one run.
3. Check whether the final reward was emitted, not just an intermediate reward.
4. Inspect the trace with `query_spans` and the adapter that matches the algorithm.

### Store and trainer problems

1. Start with `InMemoryLightningStore` for CPU-local checks.
2. Confirm `RolloutConfig.max_attempts` and retry conditions before assuming a runner failure.
3. Use `query_rollouts` plus `query_spans` to see where the lifecycle stalled.
4. If you need a service-backed store, verify the service backend before adjusting agent code.

### CLI/service problems

1. Check the exact subcommand help first.
2. Confirm the backend-specific optional dependency is installed.
3. For Prometheus, ensure the required environment variable exists.
4. For proxy/server workflows, keep API keys and model names explicit and avoid printing secrets.

## When to stop

Stop and ask for more resources when the fix requires any of these and they are unavailable:

- a live external API or API key,
- CUDA hardware or a matching model/runtime stack,
- MongoDB or another persistent service,
- Docker or Node/npm,
- a large dataset or benchmark download.
