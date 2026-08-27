# rLLM CLI Command Map

Use this map for routing and for safe command discovery. Run `rllm <command> --help` before executing a side-effecting command.

| Command | Purpose | Owner |
| --- | --- | --- |
| `rllm agent` | Manage user-registered agent scaffolds and import paths | `sub-skills/cli-ops/` plus `sub-skills/evaluation/` for AgentFlow semantics |
| `rllm dataset` | List, pull, inspect, register, remove, and curate datasets | `sub-skills/datasets/` |
| `rllm eval` | Evaluate an agent/model on a benchmark dataset | `sub-skills/evaluation/` |
| `rllm init` | Scaffold a new agent project and optional evaluator | `sub-skills/cli-ops/` |
| `rllm login` | Authenticate to the rLLM UI/service for live logging | `sub-skills/cli-ops/` |
| `rllm model` | Configure, show, or swap provider/model defaults | `sub-skills/cli-ops/` |
| `rllm sft` | Supervised fine-tuning from registered datasets or files | `sub-skills/training/` |
| `rllm snapshot` | Manage sandbox environment snapshots for supported backends | `sub-skills/cli-ops/`, then `evaluation` or `training` for runtime use |
| `rllm train` | RL training on benchmark datasets | `sub-skills/training/` |
| `rllm view` | Browse saved eval episodes in a local web viewer | `sub-skills/cli-ops/` and `evaluation` for result schema |
| `rllm setup` | Hidden deprecated alias | Prefer `rllm model setup` |

## Common help checks

```bash
rllm --help
rllm model --help
rllm dataset --help
rllm eval --help
rllm train --help
rllm sft --help
rllm snapshot --help
rllm-model-gateway --help
```

## Shared local state

- `RLLM_HOME` controls the rLLM user-state root; default is `~/.rllm`.
- Model/provider setup is stored under the rLLM home config files used by `rllm model`.
- User agent/evaluator registrations are stored under rLLM home registries and are loaded before built-in catalogs and entry points.
- Sandbox snapshot groups are tracked under the rLLM home snapshot registry.

Use the CLI owner sub-skill before mutating any of this state.
