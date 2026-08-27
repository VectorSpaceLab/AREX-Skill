# `lep` Command Map

This map is distilled from the package README, the click entry point, the click helper used by all groups, and installed help output. Always refresh exact syntax with `lep --help`, `lep <group> --help`, or `lep <group> <subcommand> --help` because command availability can vary by installed version.

## Minimum Discovery Commands

```bash
lep --version
lep --help
lep <group> --help
lep <group> <subcommand> --help
```

Global options:

- `-v`, `--version`: print the package CLI version and exit.
- `-h`, `--help`: print help and exit.

The package exposes the entry point named `lep`. If `lep` is not on `PATH`, use the troubleshooting reference before planning any live operation.

## Top-Level Groups Seen In Installed Help

| Group | Main purpose | Safe first help/read commands | Route deeper details to |
|---|---|---|---|
| `endpoint` | Manage deployed endpoints; visible alias for deployment commands. | `lep endpoint --help`, `lep endpoint list`, `lep endpoint status -n NAME`, `lep endpoint get -n NAME` | workload-management |
| `finetune` | Manage fine-tuning jobs. | `lep finetune --help`, `lep finetune list`, `lep finetune get ID` | workload-management |
| `ingress` | Manage ingress and endpoint traffic weights. | `lep ingress --help`, `lep ingress list`, `lep ingress get -n NAME` | storage-secrets-ingress |
| `job` | Manage batch jobs. | `lep job --help`, `lep job list`, `lep job get -i JOB_ID`, `lep job events -i JOB_ID` | workload-management |
| `log` | Retrieve endpoint, job, or replica logs. | `lep log get --help` | workload-management for workload logs; this sub-skill for scoping |
| `login` / `logout` | Workspace session commands at the root level. | `lep login --help`, `lep logout --help` | workspace-and-auth |
| `node` | List node groups, nodes, reservations, resource shapes, and storage volumes. | `lep node --help`, `lep node list`, `lep node resource-shape` | workload-management |
| `pod` | Manage dev pods. | `lep pod --help`, `lep pod list`, `lep pod get -n NAME` | workload-management |
| `raycluster` | Manage Ray clusters and Ray jobs. | `lep raycluster --help`, `lep raycluster list`, `lep raycluster get -n NAME` | workload-management |
| `secret` | Manage workspace secrets. | `lep secret --help`, `lep secret list` | storage-secrets-ingress |
| `template` | List workload templates. | `lep template --help`, `lep template list` | workload-management |
| `workspace` | Inspect/select workspace context. | `lep workspace --help`, `lep workspace list`, `lep workspace status`, `lep workspace id`, `lep workspace url` | workspace-and-auth |

## Hidden Or Compatibility Groups

These groups may not appear in top-level help but are present in the click command tree for compatibility. Try `lep <group> --help` before concluding the capability is missing.

| Hidden group | Meaning | Command set |
|---|---|---|
| `deployment` | Backward-compatible alias for `endpoint`. Source registers the same endpoint command objects under hidden `deployment` and visible `endpoint`. | `create`, `events`, `get`, `list`, `log`, `remove`, `restart`, `status`, `stop`, `update` |
| `storage` | Hidden file-storage group. | `download`, `du`, `ls`, `ls-file-system`, `mkdir`, `rm`, `rmdir`, `upload` |
| `file` | Hidden alias for the same storage group. | Same as `storage` |

Hidden subcommands also exist in some groups, such as `finetune list-trainers` and `template get`. Use help first and avoid hidden commands unless the user specifically needs that surface.

## Subcommand Summary

| Group | Subcommands from installed command tree |
|---|---|
| `endpoint` / `deployment` | `create`, `events`, `get`, `list`, `log`, `remove`, `restart`, `status`, `stop`, `update` |
| `finetune` | `create`, `delete`, `get`, `list`, hidden `list-trainers` |
| `ingress` | `add-endpoint`, `create`, `delete`, `get`, `list`, `remove-endpoint`, `set-endpoints`, `update-endpoint` |
| `job` | `clone`, `create`, `events`, `get`, `list`, `log`, `nodes`, `remove`, `remove-all`, `replicas`, `start`, `stop`, `stop-all` |
| `log` | `get` |
| `node` | `list`, `list-nodes`, `list-reservations`, `resource-shape`, `storage` |
| `pod` | `create`, `get`, `list`, `remove`, `ssh`, `stop` |
| `raycluster` | `create`, `get`, `list`, `list-jobs`, `remove`, `start`, `stop`, `stop-job`, `submit-job`, `update` |
| `secret` | `create`, `list`, `remove` |
| `storage` / `file` | `download`, `du`, `ls`, `ls-file-system`, `mkdir`, `rm`, `rmdir`, `upload` |
| `template` | `list`, hidden `get` |
| `workspace` | `id`, `list`, `login`, `logout`, `remove`, `removeall`, `status`, `token`, `url` |

## Click Abbreviations

The CLI wraps click groups with custom abbreviation resolution:

- An abbreviation matches when the first character is the same and the abbreviation's characters appear in order within exactly one command name.
- Resolution returns the full command name internally.
- Hidden command names participate in matching, so abbreviations that look unique in visible help can still be ambiguous.
- If multiple commands match, click fails before running the command and prints the candidates.

Examples from the installed command tree:

```bash
lep dpl --help          # resolves to hidden compatibility group `deployment`
lep depl --help         # resolves to hidden compatibility group `deployment`
lep stor --help         # resolves to hidden `storage`
lep w stat --help       # resolves to `workspace status`
lep ing add-e --help    # resolves to `ingress add-endpoint`
lep fi --help           # ambiguous: `file`, `finetune`
lep l --help            # ambiguous: `log`, `login`, `logout`
```

Operational rule: accept abbreviations as user input for diagnosis, but expand to full command names in plans, confirmations, logs, and any command that mutates state.

## Version Check Behavior

On normal CLI invocation the root callback performs a best-effort PyPI check at a cache interval. If a newer package is available, `lep` may print a warning like “A newer version of leptonai (...) is available...”. Network or PyPI failures are silently ignored. Treat this warning as advisory; do not treat it as command failure unless the command exit status is nonzero.

For reproducible automation, parse command output defensively: capture exit status separately, tolerate a leading upgrade warning, and prefer `lep --version` for the installed package version.
