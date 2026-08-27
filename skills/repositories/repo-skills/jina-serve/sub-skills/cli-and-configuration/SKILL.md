---
name: cli-and-configuration
description: "Use Jina CLI commands, install variants, environment variables,
  YAML/JAML configuration, and parser inspection safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# CLI and Configuration

Use this sub-skill when the task asks how to install Jina, choose a `jina` CLI command, inspect command options, write or debug Flow/Deployment/Executor YAML, use environment variables, export schemas, or diagnose configuration errors.

## Read first

- [CLI reference](references/cli-reference.md) for command families and safe command-selection patterns.
- [Configuration reference](references/configuration.md) for Jina YAML/JAML, `${{ ENV.* }}` and context variables, schema completion, and config override rules.
- [Troubleshooting](references/troubleshooting.md) for CLI import warnings, autocomplete side effects, YAML substitution, and dependency pins.
- Run [inspect_jina_cli.py](scripts/inspect_jina_cli.py) to inspect the installed CLI/parser without modifying source files.

## Common routes

| User asks | Do this |
|---|---|
| "Which `jina` command should I run?" | Identify whether they are starting an `executor`, `deployment`, `flow`, `gateway`, sending a CLI `client`, checking `ping`, exporting artifacts, creating a project with `new`, or using `hub`/`cloud`. Then read [CLI reference](references/cli-reference.md). |
| "Write a Flow/Deployment YAML" | Use [configuration reference](references/configuration.md), then route service logic to [executor-service-patterns](../executor-service-patterns/SKILL.md) or topology to [orchestration-and-deployment](../orchestration-and-deployment/SKILL.md). |
| "Show all options / generate schema" | Use `jina <command> --help`, `jina help <argument>`, or `jina export schema`; use `scripts/inspect_jina_cli.py` for parser JSON/Markdown. |
| "Install is broken" | Check [root install compatibility](../../references/install-and-compatibility.md) and [troubleshooting](references/troubleshooting.md). |
| "Disable telemetry or set runtime env" | Use `JINA_OPTOUT_TELEMETRY=1` for telemetry; pass runtime env with Flow/Deployment `env` blocks or Python `env={...}`. |

## Safe CLI checks

```bash
jina --version
jina --help
jina help deployment
jina flow --help
jina export --help
```

If these fail, do not start long-running services. Fix import/dependency issues first.

## Boundaries

- This sub-skill owns CLI/config mechanics, not Executor method logic. Use [executor-service-patterns](../executor-service-patterns/SKILL.md) for `Executor` code.
- This sub-skill owns YAML syntax and variables, not multi-service topology strategy. Use [orchestration-and-deployment](../orchestration-and-deployment/SKILL.md) for `Flow` graphs, Gateway protocols, readiness, and exports.
- This sub-skill mentions `hub` and `cloud` command routing only. Use [observability-and-production](../observability-and-production/SKILL.md) before commands that require credentials, Docker, Kubernetes, or Jina Cloud.
