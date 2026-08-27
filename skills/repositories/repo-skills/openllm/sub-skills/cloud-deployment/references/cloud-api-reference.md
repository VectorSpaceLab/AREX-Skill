# Cloud Deployment API Reference

## When to read

Read this for verified helper signatures and source-level behavior behind `openllm deploy`.

## Verified signatures

```python
resolve_cloud_config() -> pathlib.Path
get_current_context() -> str | None
ensure_cloud_context() -> None
get_cloud_machine_spec(context: str | None = None) -> list[DeploymentTarget]
_deploy_cmd = _get_deploy_cmd(
    bento: BentoInfo,
    target: DeploymentTarget | None = None,
    cli_envs: list[str] | None = None,
    context: str | None = None,
    cli_args: list[str] | None = None,
) -> tuple[list[str], EnvVars]
deploy(
    bento: BentoInfo,
    target: DeploymentTarget,
    cli_envs: list[str] | None = None,
    context: str | None = None,
    cli_args: list[str] | None = None,
    interactive: bool = False,
) -> None
```

## Data flow

1. CLI resolves a model Bento with the model repository logic.
2. If no explicit `--instance-type` is provided, OpenLLM queries BentoCloud instance types and ranks runnable targets with `can_run`.
3. `_get_deploy_cmd` builds a `bentoml deploy <bento-tag>` command.
4. Required `bento.yaml` envs are filled from explicit `--env`, existing shell variables, or interactive prompts.
5. `--context` and `--instance-type` become BentoML CLI flags.
6. OpenLLM resolves the BentoCloud config path and copies the config into the model repo's BentoML home before running the command.

## Security notes

- Do not log BentoCloud API tokens.
- Do not print literal `--env NAME=value` secrets in shared transcripts.
- Treat missing cloud config as a setup failure, not as a package import failure.
