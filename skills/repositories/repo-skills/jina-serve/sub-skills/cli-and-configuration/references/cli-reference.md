# CLI Reference

## Top-level commands

The installed parser exposes these command families:

| Command | Purpose | Safe first check |
|---|---|---|
| `jina executor` | Start a shared Executor process. | `jina executor --help` |
| `jina deployment` | Start a Deployment from YAML. | `jina deployment --help` |
| `jina flow` | Start a Flow from YAML. | `jina flow --help` |
| `jina gateway` | Start a Gateway runtime directly. | `jina gateway --help` |
| `jina client` | Start a CLI client. | `jina client --help` |
| `jina ping` | Check readiness of Flow/Deployment/Gateway/Executor endpoints. | `jina ping --help` |
| `jina export` | Export schema, Kubernetes YAML, Docker Compose YAML, or flowchart artifacts. | `jina export --help` |
| `jina new` | Create a local Jina project template. | `jina new --help` |
| `jina hub` | Create, push, pull, or manage Executor Hub artifacts. | `jina hub --help` only unless credentials/network are approved. |
| `jina cloud` | Manage Jina AI Cloud Flows, jobs, secrets, and logs. | `jina cloud --help` only unless credentials/network are approved. |
| `jina auth` | Login/logout/token operations. | `jina auth --help`; avoid real login/token actions without explicit approval. |
| `jina help` | Fuzzy lookup for a command or option. | `jina help port` |

## Command-selection patterns

- Use `jina flow --uses flow.yml` when the YAML `jtype` is `Flow` and contains Gateway/Executor topology.
- Use `jina deployment --uses deployment.yml` when the YAML `jtype` is `Deployment` and serves one Executor through Deployment orchestration.
- Use `jina executor --uses executor.yml --port 12345` for a lower-level shared Executor process. It does not provide the same standalone service Gateway shape as `Deployment`.
- Use `jina ping flow grpc://localhost:12345`, `jina ping deployment grpc://localhost:12345`, `jina ping executor localhost:12346`, or `jina ping gateway grpc://localhost:12345` after a service is already running.
- Use `jina export docker-compose flow.yml docker-compose.yml` or `jina export kubernetes flow.yml ./config` as static export steps. Running the containers or applying to a cluster is a separate production operation.

## Autocomplete and version checks

`pip install jina` may install shell completions for Bash, Zsh, or Fish. If this side effect is unwanted in automation, install in an isolated environment or redirect the home/config path during test installs.

Use:

```bash
jina --version
jina -vf
```

`--version-full` (`-vf`) shows Jina and dependency versions. It is useful for bug reports, but it may include machine details; do not paste secrets or private paths into public reports.
