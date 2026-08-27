# Packaging and Extensions

## Code package CLI

Flow scripts expose:

```bash
python flow.py package info
python flow.py package list
python flow.py package save output.tgz
```

Use these commands to understand which files will be sent to remote tasks. Package operations can have a timeout; avoid saving large packages unnecessarily.

## Package suffixes

Top-level `--package-suffixes` controls included file extensions. Defaults include `.py`, `.R`, and `.RDS`. Add custom suffixes when a flow imports or opens local templates/configs at runtime; otherwise remote tasks may miss files that local runs can see.

## Extensions and plugin enablement

Metaflow resolves plugins and extension packages at import time. Plugin categories include CLI groups, step decorators, flow decorators, environments, datastores, metadata providers, sidecars, secrets providers, and deployer implementations. `ENABLED_*` configuration variables can restrict available plugins. When a decorator or CLI disappears, check plugin enablement before assuming package corruption.

## `metaflow-dev`

The `metaflow-dev` console entry point wraps development execution workflows. Use repository-maintenance guidance before relying on it for source-tree work.
