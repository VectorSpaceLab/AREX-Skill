# Potpie root troubleshooting

Use this page for cross-cutting triage before routing into a workflow-specific sub-skill.

## First probe sequence

```bash
potpie --version
potpie --help
potpie daemon status
```

If these fail, start with install/import troubleshooting. If they pass but higher-level commands fail, diagnose daemon/backend readiness.

## Cross-cutting failure map

| Symptom | Route | First recovery |
| --- | --- | --- |
| CLI missing or import crash | [`runtime`](../sub-skills/runtime/SKILL.md) | Install/repair package, run `python -m pip check`, and rerun help/version checks. |
| `status`, `doctor`, `backend list`, or `skills status` says unavailable | [`runtime`](../sub-skills/runtime/SKILL.md) | Run `potpie daemon status`; start/setup daemon before retrying daemon-dependent commands. |
| No active pot, wrong repo default, or unlinked source | [`workspace-boundaries`](../sub-skills/workspace-boundaries/SKILL.md) | Inspect `pot list/info/linked/default` and `source list/status`. |
| Provider credential, OAuth, PAT, or ledger failure | [`auth-integrations`](../sub-skills/auth-integrations/SKILL.md) | Run provider-specific status/login and preserve host/site/workspace details. |
| Empty graph read | [`graph-read`](../sub-skills/graph-read/SKILL.md) | Check pot/source scope, graph status, and read filters before assuming data is absent. |
| Unsupported graph include/view | [`graph-read`](../sub-skills/graph-read/SKILL.md) | Run `graph catalog` or generate the live contract and choose a reader-backed include. |
| Rejected graph mutation, review gate, expired plan, or failed verification | [`graph-write`](../sub-skills/graph-write/SKILL.md) | Regenerate mutation template, re-propose, inspect plan warnings, and obtain explicit approval. |
| Bundled agent-skill drift or invalid install target | [`skills-management`](../sub-skills/skills-management/SKILL.md) | Inspect exact agent/scope/path and use offline catalog helper when daemon is down. |

## Do not conflate these states

- **Installed package failure:** `potpie --help` cannot render.
- **Stopped daemon:** `potpie --help` works and `potpie daemon status` reports `up=False`; daemon-dependent commands may be unavailable.
- **Wrong workspace:** runtime is healthy, but pot/source state points at a different repo or no source.
- **Missing credentials:** source/auth commands fail against a provider even though local graph commands may work.
- **Empty graph:** command is valid but no records match the selected pot/source/scope.
- **Unsupported graph route:** the include/view/operation is not backed by this runtime.

## Safe bundled helpers

From the generated skill root:

```bash
scripts/potpie_smoke.sh
python scripts/typecheck_public_context_api.py
python scripts/generate_agent_contract.py > potpie-agent-contract.md
python sub-skills/skills-management/scripts/list_bundle_skills.py --markdown
```

These helpers are read-only and do not start the daemon, mutate a graph backend, or install files.

## Escalation rules

- Ask the user before running destructive workspace actions (`pot reset`, source removal, broad skill removal, graph repairs that delete state).
- Ask for credentials rather than inventing tokens or hosts.
- Treat cloud/managed and external-ledger features as limited unless the current runtime proves support.
- If command help differs from this skill, regenerate the live agent contract and treat this generated skill as stale until refreshed.
