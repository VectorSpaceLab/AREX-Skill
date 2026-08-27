# Troubleshooting

Use this reference when an extension manifest, compose overlay, or catalog
change does not behave the way you expect.

## Start with the bundled summary helper

The safest first check is a read-only inventory of the catalog root:

```bash
python3 scripts/extension_manifest_summary.py --root <catalog-root>
```

Run it on the runtime catalog, the library catalog, or any local service root
that uses the same manifest layout. The helper does not mutate files.

## Symptom to cause map

| Symptom | Likely cause | What to check |
|---|---|---|
| No services appear in the catalog summary | The root path is wrong, or the manifest tree is missing | Point the summary helper at the catalog root that actually contains service directories. |
| A service shows as disabled | `compose.yaml.disabled` is present instead of `compose.yaml` | Restore the enabled marker or re-enable the service. |
| A service is missing from the resolved stack | The compose file is disabled, the backend is incompatible, or the manifest parse failed | Check `service.gpu_backends`, the compose marker, and the manifest syntax. |
| `overlay-required` appears during audit | The manifest declares a backend but the matching `compose.<backend>.yaml` file is missing | Add the missing overlay or narrow `gpu_backends`. |
| `compose-port-mismatch` appears during audit | The manifest port does not match any compose target port | Align `service.port` with the compose mapping or fix the compose mapping. |
| `healthcheck-missing` or a bad health path appears | The compose file has no healthcheck or the manifest health path is wrong | Add a healthcheck and make sure `service.health` matches it. |
| `alias-collision` or a core-service collision appears | A new alias or service id duplicates an existing one | Rename the id or alias so it does not shadow a bundled service. |
| The resolver says a compose file escapes the extension directory | The compose path is absolute or uses traversal | Keep `service.compose_file` relative and inside the extension directory. |
| The resolver rejects a user extension compose file | The security scan found an unsafe directive | Compare the file against the security failure list below. |
| A library update is marked `modified` or `untracked` | The installed definition diverged from the stored receipt, or the install predates receipts | Decide whether to keep the local edit or replace it with the library definition. |
| A model-swapping service stops working after a swap | The manifest is missing swap-safety metadata or the probe cannot authenticate | Add `service.llm`, keep `route: gateway` where possible, and provide a real probe. |

## Common rejection text

If the resolver refuses a user extension, the message usually points to one of
these patterns:

- `uses privileged mode`
- `uses a local build`
- `runs as root`
- `uses host network mode`
- `uses host PID namespace`
- `uses host IPC namespace`
- `uses host user namespace`
- `adds dangerous capability`
- `uses dangerous security_opt`
- `declares devices`
- `requests GPU passthrough via deploy.resources.reservations.devices`
- `mounts the Docker socket`
- `bind-mounts absolute host path`
- `declares extra_hosts`
- `declares sysctls`
- `uses reserved Docker Compose label`
- `must bind 127.0.0.1`
- `collides with a built-in core service name`
- `compose_file escapes the extension directory`

## Update and rollback confusion

If a catalog entry looks wrong after an update:

1. Check whether the installed definition is `current`, `available`,
   `modified`, or `untracked`.
2. Remember that update/rollback replace definitions only; they do not remove
   data, volumes, secrets, or existing config files.
3. If the service is enabled, an update may reconcile the running container
   after the new definition is staged.
4. If the service is disabled, update and rollback should keep it disabled.

## When to switch sub-skills

- Dashboard catalog UI or frontend behavior -> `dashboard-and-api`
- Exact `ods enable/disable/list/audit` command syntax -> `ops-cli-and-host-tools`
- Model tier selection or backend routing decisions -> `hardware-and-models`

