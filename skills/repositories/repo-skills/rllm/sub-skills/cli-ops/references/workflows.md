# CLI Operations Workflows

## Provider/model setup

```bash
rllm model setup
rllm model show
rllm model swap
```

Use `rllm model setup` for first-time provider/API-key/model state. The old `rllm setup` command is a hidden deprecated alias that forwards to model setup.

For one-off eval/training runs, explicit flags can bypass saved model state:

```bash
rllm eval <benchmark> --agent <agent> --base-url <url> --model <model>
```

## UI login and viewing results

```bash
rllm login
rllm view <results-or-episodes-path>
```

UI login controls live logging and hosted/local viewing support. Evaluation can still run with `--no-ui` and saved local episodes.

## Project scaffold and agent registry

```bash
rllm init my-agent --evaluator
rllm agent list
rllm agent register <name> <module:object>
rllm agent info <name>
rllm agent unregister <name>
```

Scaffolded projects can provide an AgentFlow and optional evaluator entry point. Registry lookup is useful for CLI eval/train, but direct `module:object` paths are often better for one-off experiments.

## Snapshot management

```bash
rllm snapshot --help
rllm snapshot create <benchmark> --sandbox-backend <backend>
rllm snapshot list
rllm snapshot inspect <group-or-id>
rllm snapshot destroy <group-or-id>
rllm snapshot sync --sandbox-backend <backend>
```

Snapshots accelerate sandbox cold starts. They are backend-dependent and not required for correctness. Use `--no-snapshot` in eval/train to debug whether a failure is snapshot-related.
