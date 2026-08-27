---
name: setup-and-ops
description: "Install, inspect, configure, and safely operate the RD-Agent
  package and its CLI, UI, logs, and environment checks."
metadata:
  disco-role: operating
  parent-skill: rd-agent
license: MIT
disable-model-invocation: true
---

# RD-Agent setup and operations

Use this sub-skill for installation, import/CLI failures, health checks, configuration discovery, log/UI operation, and safe maintenance. For an actual research run, route onward to the domain sub-skill after the runtime is proven.

## Install and identify the active package

Use a supported Python 3.10 or 3.11 environment. From a checkout, prefer:

```bash
python -m pip install -e .
python -m pip check
python -c "import rdagent; print(rdagent.__file__)"
```

The last line is intentionally not an RD-Agent command; use the bundled `scripts/verify_install.py` instead. For a published installation, `python -m pip show rdagent` and the import path must agree. Do not mix a globally installed `rdagent` with a different checkout through `PYTHONPATH`.

## Probe the CLI in increasing cost order

```bash
rdagent --help
rdagent health_check --no-check-env --no-check-docker
rdagent data_science --help
rdagent fin_quant --help
rdagent fin_factor_report --help
rdagent llm_finetune --help
rdagent general_model --help
rdagent ui --help
rdagent server_ui --help
rdagent ds_user_interact --help
python -m rdagent.scenarios.rl.autorl_bench.run --help
```

Use `scripts/verify_install.py` to collect these results as JSON. A passing `--help` check proves registration only; it does not prove model access, Docker, Qlib data, a GPU, or an external benchmark.

## Configuration and processes

- Keep secrets in an uncommitted `.env` or environment manager. Never paste API keys into prompts, generated code, or logs.
- Choose a run-specific output/log directory and record the resolved configuration before starting an agent loop.
- For the generic UI, use `rdagent ui --log-dir <log-dir> --port <local-port>` after checking its help. Bind locally and stop it after inspection.
- `server_ui` and the fine-tune UI may need extra assets or a long-running process. Start them only when the user explicitly wants a UI smoke test.
- Health checks that skip environment/Docker checks are lightweight package checks, not a deployment readiness proof.

## Failure handling

- **Import/command not found:** inspect `pip show`, `import rdagent`, and the active interpreter first.
- **Health check failure:** separate missing optional tools from hard package/import errors; preserve the exact check output.
- **UI startup failure:** check port ownership, log directory readability, and optional frontend dependencies.
- **Long or silent process:** inspect the run log and child processes before retrying; do not launch duplicate listeners.

Read [operational-checklist.md](references/operational-checklist.md) for a compact preflight and recovery checklist. Use [the parent troubleshooting guide](../../references/troubleshooting.md) for cross-scenario failures.
