---
name: classic-agents
description: "Use the unsupported AutoGPT Classic, Forge, and direct benchmark
  packages safely, with workspace, CLI, permissions, and report guidance."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Classic Agents

Use this sub-skill only for the `classic/` project: the original AutoGPT agent,
Forge framework, and `direct_benchmark` harness. Classic is explicitly
unsupported, its dependencies are not maintained, and the repository documents
known security risks. Prefer the current Platform for new production work.

## Reference map

- Read [Classic workflows](references/classic-workflows.md) for installation,
  layered configuration, agent/Forge startup, workspaces, and benchmark runs.
- Read [CLI reference](references/classic-api-cli-reference.md) for installed
  package facts, help routes, command options, benchmark strategies/models, and
  test locations.
- Read [troubleshooting](references/troubleshooting.md) before using API keys,
  changing permissions, resetting benchmark state, or diagnosing legacy imports.
- Run `python scripts/classic_cli_probe.py --repo <checkout>` for read-only
  layout/import/help checks. It never starts an agent or benchmark.

## Start safely

```bash
cd classic
poetry install
cp .env.example .env  # Forge-oriented setup; use the matching Classic template
poetry run python -m forge
poetry run autogpt --help
poetry run serve --help
poetry run direct-benchmark --help
```

Keep API keys in local env files only. A Classic workspace stores agent state,
permissions, history, and files under `.autogpt/`; inspect the permission layer
before allowing shell, file, or web actions.

## Benchmark guardrails

`direct-benchmark run` can execute many challenges, strategies, model presets,
parallel workers, retries, and LLM calls. Before running it, choose the
challenge subset, model/provider, attempts, concurrency, timeout, workspace,
and report directory. Use `list-challenges`, `list-models`, and
`list-strategies` first; use `--json`, `--quiet`, `--keep-answers`, or
`--retry-failures` deliberately. Never assume a missing API key is a reason to
silently switch providers.

## Tests and routing

Focused safe tests include `pytest forge/tests/test_permissions.py -q` and
unit tests under `original_autogpt/tests/unit/`. Route current Platform
self-hosting, backend, and frontend work to the sibling `platform-*` skills.
