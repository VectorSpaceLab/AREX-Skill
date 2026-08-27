# Cross-Cutting Troubleshooting

## Purpose

Read this when the failure spans installation, imports, optional extras,
telemetry, provider configuration, or package selection. Workflow-specific
failures live in the nearest sub-skill troubleshooting reference.

## Fast triage

1. Confirm Python is `>=3.12`.
2. Run `python scripts/check_giskard_imports.py` from this skill directory or
   adapt the path to the bundled script.
3. Use `import giskard.checks`, `import giskard.scan`, `import giskard.llm`,
   `import giskard.agents`, or `import giskard.core`; do not use underscore
   package names.
4. If the task needs a live LLM, confirm the provider extra is installed and the
   matching environment variable is set before running provider-backed code.
5. If the task is a scan or LLM judge, configure a default generator/provider
   first; deterministic checks and no-key inspection helpers can run without
   credentials.

## Common symptoms

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'giskard_checks'` | Giskard v3 uses split namespace imports, not underscore package imports. | Replace with `import giskard.checks` and run the import smoke helper. |
| `ModuleNotFoundError: No module named 'giskard.scan'` | The scan package/extra is not installed. | Install `giskard-scan` or `giskard[scan]`; rerun with `--require-scan`. |
| Import mentions a legacy `giskard` package conflict | The old monolithic/legacy `giskard` distribution is mixed with v3 split packages. | Uninstall the legacy distribution from that environment, reinstall the v3 packages, and run the import smoke. |
| LLM judge or scan fails before generation | No default generator/provider is configured, provider SDK is missing, or credentials are absent. | Use `llm-providers` to install/configure the provider, then set `giskard.checks.set_default_generator(...)` where needed. |
| `ProviderNotAvailableError` | The selected provider SDK extra is missing. | Install the provider-specific extra shown by the error, such as `giskard[openai]`, `giskard[google]`, or `giskard[anthropic]`. |
| Authentication or Azure endpoint errors | Environment variables or alias parameters do not match the provider. | Check the [provider matrix](../sub-skills/llm-providers/references/provider-matrix.md); verify keys and endpoint/base-url variables. |
| Optional Rego or scanner integration import fails | Optional extra (`regorus`, `garak`, `deepteam`, or private integration package) is not installed. | Install only the selected extra if the workflow needs it; otherwise keep the capability explicitly unverified. |
| Telemetry concern | Telemetry opt-out was not set before first import. | Set `DO_NOT_TRACK=1` or `GISKARD_TELEMETRY_DISABLED=1` before import, or call `giskard.core.disable_telemetry()` for the current process. |
| Real scan is slow, costly, or nondeterministic | Scan generation uses LLM calls, remote datasets, or third-party scanners. | Run no-key inspection helpers first; then bound `max_scenarios`, set `target_mode`, confirm target concurrency safety, and get credentials/network approval. |

## Escalate to focused sub-skills

- Checks/evals failures: `sub-skills/checks-evals/references/troubleshooting.md`.
- Provider routing/API failures: `sub-skills/llm-providers/references/troubleshooting.md`.
- Agent workflow/tool/template failures: `sub-skills/agents-workflows/references/troubleshooting.md`.
- Scan/third-party scanner failures: `sub-skills/scan-redteam/references/troubleshooting.md`.
- Runtime/core import and telemetry issues: `sub-skills/runtime-setup/references/troubleshooting.md`.

## Stop conditions

Stop and ask for missing external inputs rather than guessing when a workflow
requires provider credentials, remote dataset access, third-party scanner
installation, private packages, or long-running red-team execution. A successful
CPU import does not verify live provider behavior.
