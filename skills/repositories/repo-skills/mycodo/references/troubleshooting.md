# Mycodo Cross-Cutting Troubleshooting

Read this when a task spans install/runtime, control workflows, custom modules, API automation, or source maintenance and you need the first routing decision.

## First classify the failure surface

| Symptom | Start with | Why |
| --- | --- | --- |
| Web UI not reachable, daemon red, upgrade failed, logs/service/database problem | `installation-operations` | This is deployed-host/service state. |
| Sensor/Output/PID/Function/Action/Widget behavior wrong | `devices-and-control` | This is controller configuration, hardware, or measurement state. |
| Custom module upload/import/activation/runtime error | `custom-modules` | This is module contract or custom code behavior. |
| REST API, API key, multi-channel query, Pyro, or `mycodo-client` failure | `api-and-automation` | This is an automation surface and credential/endpoint issue. |
| Source import/test/docs/migration/API code failure in a checkout | `development-and-testing` | This is maintainer workflow and focused tests. |

## Global safety rules

- Do not repeat a command that can change hardware state just because the first attempt failed.
- Ask before running installers, service restarts, dependency installation, Docker commands, backup/restore/import/export/upgrade, DB rename/delete, or manual hardware tests.
- Treat API keys, logs, backups, camera images, and measurement histories as sensitive.
- A skipped hardware/service check is not a pass. Mark it as requiring live target verification.
- Prefer read-only probes, logs, and static validators before mutating commands.

## Common cross-skill root causes

| Root cause | Observable signals | Next step |
| --- | --- | --- |
| Wrong Mycodo version or stale skill | current version/commit differs from provenance; docs/API shape mismatch | read `repo-provenance.md`; refresh the repo skill if source changed |
| Wrong host or install path | commands assume `/opt/Mycodo` but user uses a custom path; Docker vs bare-metal confusion | ask for installed path or use bundled probes with explicit `--repo-root` |
| Missing optional dependency | import errors in daemon log, dependency page prompts, controller inactive | install only selected module dependency after approval; avoid all optional deps |
| Hardware unavailable/miswired | manual tests fail, no `/dev` device, I2C address absent, camera unavailable | stop until target hardware/wiring is confirmed |
| Stale measurement data | PID/Conditional sees old values, graphs blank, API returns `null` | check Input period, Max Age, system time, InfluxDB, channel/unit IDs |
| Credentials/permissions | REST 401/403, webhook/email/MQTT failures, logs expose auth issues | validate API key/user role or external service credentials privately |
| DB/migration mismatch | System Information database version red, upgrade log errors | use installation operations; avoid DB deletion without backup/approval |

## Bundled scripts by purpose

- Root `scripts/quick_mycodo_probe.py`: safe package/version/source-layout probe.
- `installation-operations/scripts/check_mycodo_environment.py`: safe installed-layout/config probe.
- `devices-and-control/scripts/summarize_supported_modules.py`: static module-family inventory from a checkout.
- `custom-modules/scripts/validate_custom_module.py`: AST validator for custom module files.
- `api-and-automation/scripts/mycodo_api_request.py`: REST helper with explicit auth/TLS handling.
- `development-and-testing/scripts/run_selected_checks.py`: focused non-hardware checkout checks.

Run helper `--help` first and confirm the helper fits the user's host/context.
