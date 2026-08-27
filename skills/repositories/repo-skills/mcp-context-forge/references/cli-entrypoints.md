# ContextForge CLI entry points

This page lists the public commands that operators are expected to use.

| Command | Backing module | Purpose | Notes |
| --- | --- | --- | --- |
| `mcpgateway` | `mcpgateway.cli:main` | Uvicorn wrapper for the gateway app | Defaults to `mcpgateway.main:app` with host/port injection when needed. Environment overrides: `MCG_HOST`, `MCG_PORT`. |
| `mcpgateway-server` | `mcpgateway.__main__:main` | Direct server startup | Equivalent to `python -m mcpgateway`. It starts the server path rather than offering help-oriented inspection. |
| `cforge` | `mcpgateway.tools.cli:main` | Builder/deployment CLI | Exposes `gateway` and `plugin` command groups. Use it for config validation, builds, certs, deploy, verify, and destroy. |
| `init-secrets` | `mcpgateway.scripts.init_secrets:main` | Generate strong secrets | Supports `--output`, `--force`, `--stdout`, and `--patch-env`. |

## `mcpgateway` diagnostics

`mcpgateway` also supports a few inspection-only flags before it hands off to Uvicorn:

- `--validate-config [path]` — validate an env file with the gateway settings model
- `--config-schema [output]` — print or write the Settings JSON schema
- `--support-bundle` — build a sanitized troubleshooting bundle
- `--version` / `-V` — print the package version

## Related references

- Package identity and install options: [`package-overview.md`](package-overview.md)
- Runtime setup, secrets, and deployment choices: [`../sub-skills/runtime-configuration/SKILL.md`](../sub-skills/runtime-configuration/SKILL.md)
