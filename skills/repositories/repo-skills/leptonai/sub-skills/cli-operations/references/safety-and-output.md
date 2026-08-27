# Safety And Output Rules For `lep`

Lepton CLI commands can read cloud state, mutate cloud resources, mutate local CLI state, transfer remote files, write local files, or open interactive sessions. Classify the command before running it.

## Read-First / Mutate-Confirm Workflow

1. **Identify context.** Know the intended workspace and target resource. If the workspace is unclear, route to workspace/auth handling instead of guessing.
2. **Discover syntax.** Run `lep <group> --help` and, for a specific action, `lep <group> <subcommand> --help`.
3. **Read current state first.** Use a narrow read command such as `list`, `get`, `status`, `events`, or scoped `log` where available.
4. **Prepare a confirmation block for mutations.** Include:
   - exact full `lep` command, with no abbreviations;
   - target workspace or confirmation that the CLI default workspace is intended;
   - target resource name or ID;
   - current state observed by the read step;
   - one sentence describing the impact;
   - whether local files or remote file storage will be written or deleted.
5. **Execute only after explicit confirmation for this exact target.** Approval for one resource or command does not carry over to a later resource, wildcard, bulk command, upload/download destination, or session.
6. **Summarize safely.** Report resource names, IDs, state, and next actions. Redact secrets and avoid printing raw tokens.

If a command has no safe read equivalent, say so, show the help-derived plan, and ask for confirmation before mutation.

## Read-Only Or Low-Risk Discovery Commands

These commands are suitable as first probes when credentials and workspace context are available, but they can still fail on auth/network errors:

- CLI surface: `lep --version`, `lep --help`, `lep <group> --help`, `lep <group> <subcommand> --help`.
- Workspace context: `lep workspace list`, `lep workspace status`, `lep workspace id`, `lep workspace url`.
- Workloads: `lep endpoint list/status/get/events`, `lep job list/get/events/nodes/replicas`, `lep pod list/get`, `lep raycluster list/get/list-jobs`, `lep finetune list/get`, `lep node list/list-nodes/list-reservations/resource-shape/storage`, `lep template list`.
- Storage/secrets/ingress reads: `lep storage ls`, `lep storage du`, `lep storage ls-file-system`, `lep file ls`, `lep secret list`, `lep ingress list`, `lep ingress get`.
- Logs: `lep log get --help`; actual log retrieval should be scoped as described below.

Avoid token-printing commands unless the user explicitly requests token output and the workspace/auth sub-skill confirms the redaction or handling policy.

## Destructive And High-Impact Command Catalog

Treat these as requiring read-first and explicit confirmation:

| Surface | Commands requiring confirmation | Why |
|---|---|---|
| Root/workspace local state | `lep login`, `lep logout`, `lep workspace login`, `lep workspace logout`, `lep workspace remove`, `lep workspace removeall` | Can create, switch, or delete local workspace session records. |
| Endpoints/deployments | `lep endpoint create`, `update`, `restart`, `stop`, `remove`; same through hidden `lep deployment ...` | Creates, changes, restarts, stops, or deletes cloud endpoints. |
| Jobs | `lep job create`, `clone`, `start`, `stop`, `stop-all`, `remove`, `remove-all` | Creates or changes job execution; bulk stop/remove can affect many jobs. |
| Pods | `lep pod create`, `stop`, `remove`, `ssh` | Creates/stops/deletes dev pods or opens an interactive shell session. |
| Ray clusters | `lep raycluster create`, `update`, `start`, `stop`, `remove`, `submit-job`, `stop-job` | Changes cluster capacity or Ray jobs. |
| Fine-tuning | `lep finetune create`, `delete` | Starts or deletes fine-tuning jobs. |
| Secrets | `lep secret create`, `remove` | Creates or deletes secret records. |
| Storage/file | `lep storage upload`, `download`, `mkdir`, `rm`, `rmdir`; same through `lep file ...` | Mutates remote storage or writes local files. `rmdir --recursive` is especially destructive. |
| Ingress | `lep ingress create`, `delete`, `add-endpoint`, `remove-endpoint`, `update-endpoint`, `set-endpoints` | Changes traffic routing. `set-endpoints` replaces the entire endpoint list and removes omitted endpoints. |
| Log/spec output | `lep log get --path`, `lep endpoint get --path`, `lep pod get --path`, `lep raycluster get --path` | Writes local files; confirm destination and overwrites. |

Creation commands are high-impact even when not “destructive”: they can allocate quota, create billable resources, publish routes, or persist secrets/configuration.

## Planning A Destructive Endpoint Removal Without Executing

For a user request like “remove endpoint `old-api`”:

1. Discover syntax: `lep endpoint remove --help`.
2. Read current state: `lep endpoint status -n old-api` or `lep endpoint get -n old-api`.
3. Confirm workspace context with a workspace read if not already established.
4. Present the planned command only:

```text
Planned command: lep endpoint remove -n old-api
Target: endpoint old-api in the selected workspace
Current state: <state from status/get>
Impact: deletes the endpoint and stops serving its routes.
Confirm exactly this deletion before I run it.
```

Do not run the remove command until the user explicitly confirms this single deletion.

## Output And Log Scoping

- Prefer default rich tables for human inspection (`list`, `status`, node/resource-shape commands).
- Use commands that naturally emit JSON for machine inspection, such as `lep endpoint get`, `lep pod get`, `lep raycluster get`, and `lep ingress get`; still confirm local `--path` writes.
- There is no guaranteed global `--output json` flag. Check the specific help before promising structured output.
- Scope logs narrowly:
  - Use `lep log get --help` to confirm current flags.
  - Select exactly one of endpoint, job ID, job name, replica, or supported history identifier.
  - Use UTC `--start` and `--end` when available; for jobs, the CLI can infer the job time range if start/end are omitted.
  - Use `--query` for targeted filtering and `--workers` only for bounded retrieval.
  - Avoid large log downloads through CLI; use the platform's log export workflow for large-volume archives.
- Confirm any local path before running `--path` or storage download/upload. Endpoint/pod/raycluster `get --path` accepts a directory or filename and writes a spec JSON. `log get --path` writes text logs. Storage download writes to the current directory when no local path is provided.
- Do not include raw credentials or token-bearing environment dumps in output summaries.

## Source Of Truth During Drift

If an installed command lacks a group or flag listed here, use the installed help output as authoritative. If a hidden group is absent, use the visible replacement (`endpoint` instead of `deployment`, or `storage`/`file` only if help confirms availability). Capture the mismatch in the task notes so the repo skill can be refreshed later.
