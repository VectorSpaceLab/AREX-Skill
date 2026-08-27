# Skills management troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `potpie skills status` reports unavailable | Daemon is not running. | Run `potpie daemon status`; start/setup the daemon or use `scripts/list_bundle_skills.py` for offline catalog inspection. |
| Unknown agent target | The target name is unsupported by this Potpie version. | Check `potpie skills install --help` and choose a supported target. |
| Project install writes to the wrong place | `--scope project` was used without the intended `--path`, or the shell cwd was unexpected. | Re-run with explicit project path and inspect status before overwriting. |
| Global install is not visible to the agent | Harness-specific skill directory differs from Potpie's target path or the agent must restart/reload. | Inspect `skills status`, confirm target path, and restart/reload the agent harness. |
| Status shows missing skills | Bundle was never installed for that target/scope. | Run `potpie skills install --agent <agent> --scope <scope>`. |
| Status shows outdated skills | Package bundle changed after install. | Run `potpie skills update --agent <agent>` after confirming the target. |
| Status shows locally modified files | User or agent edited installed skill files. | Decide whether to preserve edits, diff manually, or update/overwrite with explicit user approval. |
| `skills remove` would delete too much | Target/scope/path is broader than intended. | Re-run status with explicit target and path; confirm before removal. |
| Offline helper fails to import package resources | Potpie package is not installed in the Python environment running the script. | Run the helper with the same Python environment that owns `potpie`, or install Potpie first. |

## Daemon dependency rule

The CLI catalog/status/install/update/remove surface may use the daemon-backed Skill Manager. If only catalog inspection is needed, prefer the bundled offline helper. If installation or drift reconciliation is needed, make daemon readiness explicit first.

## Drift handling

1. Run status for the exact target/scope/path.
2. Categorize each skill: missing, current, outdated, or locally modified.
3. Update missing/outdated entries only after confirming the target.
4. Preserve or intentionally overwrite local modifications; do not silently replace user edits.
5. Re-run status after install/update/remove.

## Scope handling

- `global` affects the user's harness-wide skill location.
- `project` should include an explicit project path when automation is involved.
- The same agent target can have both global and project skills; inspect the correct scope before making conclusions.
