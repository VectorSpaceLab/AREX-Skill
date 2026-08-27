# BentoCloud Deployment Workflows

## When to read

Read this when turning a model tag into a BentoCloud deployment plan.

## Basic deployment

```bash
openllm deploy llama3.2:1b --env HF_TOKEN
```

Use `--env HF_TOKEN` when the variable is already present in the shell. Avoid writing token values into shared logs.

## Deployment with explicit instance type

```bash
openllm deploy llama3.2:1b --instance-type <instance-type> --env HF_TOKEN
```

If `--instance-type` is omitted, OpenLLM asks BentoCloud for available instance types and chooses the first runnable target in noninteractive mode.

## Deployment with context and Bento args

```bash
openllm deploy llama3.2:1b --context <context-name> --arg key=value --env HF_TOKEN
```

`--arg` values are forwarded to the BentoML deploy command as Bento arguments.

## Required prerequisites

1. OpenLLM must be installed and importable.
2. The model must resolve to a Bento in a configured OpenLLM model repository.
3. BentoCloud credentials must exist; normally run `bentoml cloud login` first.
4. A BentoCloud context must be usable, or a `--context` must be provided.
5. Any Bento-required environment variables must be provided through the shell, `--env NAME`, or `--env NAME=value` in a private environment.

## Credential-safe planning

Use `scripts/plan_deploy_command.py` to validate deploy flags and required env names without contacting BentoCloud or exposing secret values.
