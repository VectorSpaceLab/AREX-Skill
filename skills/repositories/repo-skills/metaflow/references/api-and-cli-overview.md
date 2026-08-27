# Metaflow API and CLI Overview

## Purpose

Read this when you need a compact map of Metaflow's public imports and command surfaces before choosing a sub-skill.

## Verified package facts

- Distribution name: `metaflow`.
- Import root: `metaflow`.
- Version inspected for this skill: `2.19.37`.
- Console entry points: `metaflow` and `metaflow-dev`.
- Core imports commonly used by flows and tooling:
  ```python
  from metaflow import (
      FlowSpec, step, Parameter, JSONType, IncludeFile, Config, config_expr,
      current, Flow, Run, Step, Task, DataArtifact, Metaflow, S3,
      Runner, NBRunner, Deployer, DeployedFlow,
  )
  ```

## Verified signatures to preserve

- `FlowSpec(use_cli=True)` constructs a flow and runs the CLI when `use_cli=True`.
- `step(f=None, *, start=False, end=False, node_info=None)` marks a method as a graph step.
- `Parameter(name, default=None, type=None, help=None, required=None, show_default=None, **kwargs)` defines a CLI/run parameter.
- `IncludeFile(name, required=None, is_text=None, encoding=None, help=None, parser=None, **kwargs)` stores a local file as an artifact-like parameter.
- `Config(name, default=None, default_value=None, help=None, required=None, parser=None, plain=False, **kwargs)` defines deploy-time configuration.
- `Runner(flow_file, show_output=True, profile=None, env=None, cwd=None, file_read_timeout=3600, **kwargs)` runs a flow file programmatically.
- `Deployer(flow_file, show_output=True, profile=None, env=None, cwd=None, file_read_timeout=3600, **kwargs)` configures production deployer providers.

## Flow-script CLI groups

Every flow script exposes top-level options such as `--metadata`, `--environment`, `--datastore`, `--with`, `--pylint/--no-pylint`, and commands such as:

- `check`, `show`, `output-dot`, `output-raw`, `run`, `resume`, `spin`, and `version`.
- `package` with `info`, `list`, and `save`.
- `card` with `create`, `view`, `get`, `list`, and `server`.
- `logs` with `show` and `scrub`.
- `tag` with `add`, `list`, `remove`, and `replace`.
- Remote/provider groups: `batch`, `kubernetes`, `argo-workflows`, `step-functions`, and `airflow`.

The standalone `metaflow` console command is a management CLI with commands such as `configure`, `tutorials`, `status`, `code`, and `develop`; it does not accept `metaflow --version`.

## Routing reminder

- Use the nearest sub-skill for detailed command syntax and failure recovery.
- Treat provider CLIs as potentially credentialed/service-affecting unless the reference explicitly marks a command as help-only or compile-only.
