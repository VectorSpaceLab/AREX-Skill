# Skills management workflow reference

Potpie ships an agent-bundle catalog that can be installed into compatible agent harnesses. This sub-skill covers Potpie's own `potpie skills ...` CLI, not DisCo's generated repo-skill import process.

## Bundled skill IDs in this repo version

- `potpie-change-timeline`
- `potpie-cli`
- `potpie-debug-memory`
- `potpie-graph`
- `potpie-infra-architecture`
- `potpie-project-preferences`
- `potpie-repo-baseline`
- `potpie-source-ingestion`

Use `python scripts/list_bundle_skills.py --markdown` from this sub-skill directory to print the installed package's current catalog without contacting the daemon.

## Command matrix

| Goal | Command | Notes |
| --- | --- | --- |
| List daemon-backed catalog | `potpie skills list` | Requires runtime daemon availability. |
| Install bundled skills | `potpie skills install --agent <agent>` | Writes templates for the selected agent target. |
| Update installed skills | `potpie skills update --agent <agent>` | Use after status shows drift or package upgrade. |
| Remove installed skills | `potpie skills remove --agent <agent>` | Confirm target and scope first. |
| Inspect drift/status | `potpie skills status --agent <agent>` | Shows missing/outdated/current files when daemon is available. |
| Add custom skill | `potpie skills add ...` | Separate from bundled catalog install. |
| Offline catalog | `python scripts/list_bundle_skills.py` | Reads installed package resources; no daemon required. |

## Agent targets and scopes

- Choose the agent target deliberately (`claude`, `codex`, `cursor`, or the targets supported by the current CLI help).
- Use global scope for user-wide harness installs.
- Use project scope and an explicit path when the user wants skills local to one project.
- Do not infer a target path from unrelated environment variables unless Potpie's CLI help/source confirms that target.

## Recommended sequence

```bash
potpie daemon status
potpie skills list
potpie skills status --agent <agent>
potpie skills install --agent <agent> --scope <global-or-project>
potpie skills status --agent <agent>
```

If the daemon is unavailable and the user only needs to inspect the bundle catalog, use the offline helper:

```bash
python scripts/list_bundle_skills.py --markdown
```

## Setup integration

`potpie setup` can install agent skills as part of first-run onboarding. Use `setup --dry-run` to preview that behavior. For detailed target/scope/drift repair, return to explicit `potpie skills ...` commands.

## Difference from this generated DisCo repo skill

This generated `potpie` repo skill is a self-contained DisCo Researcher operating skill. Do not import it using `potpie skills install`; Potpie's skills command manages Potpie's own bundled agent templates.
