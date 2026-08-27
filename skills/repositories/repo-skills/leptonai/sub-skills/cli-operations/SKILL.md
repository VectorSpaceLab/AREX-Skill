---
name: cli-operations
description: "Discover and operate the LeptonAI lep CLI safely, including
  command-tree help, aliases, abbreviations, output handling, and read-first
  mutation gates."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# CLI Operations

Use this sub-skill when the task is about the global `lep` command line itself: discovering commands, checking the installed CLI version, orienting to command groups, interpreting help output, handling hidden aliases or click abbreviations, scoping logs/output, or planning whether a command is read-only, mutating, or destructive.

Do **not** use this sub-skill for credential setup details, resource-specific create/update recipes, or Python SDK calls. Route those to the neighboring workspace/auth, workload-management, storage/secrets/ingress, or SDK sub-skills after this sub-skill has established the safe CLI plan.

## Load These References

- Start with [references/cli-command-map.md](references/cli-command-map.md) to discover top-level groups, hidden compatibility aliases, and abbreviation behavior.
- Use [references/safety-and-output.md](references/safety-and-output.md) before any command that can mutate cloud resources, local CLI state, remote file storage, or local files.
- Use [references/troubleshooting.md](references/troubleshooting.md) when `lep` is missing, help is ambiguous, a blank option is rejected, a version warning appears, read-only commands hit auth/network errors, or destructive confirmation is unclear.
- For a safe local command-tree snapshot, run the bundled script:

```bash
python scripts/lep_help_snapshot.py --groups endpoint workspace job pod ingress storage file --json
```

The script runs only `lep --version`, `lep --help`, and selected `lep <group> --help` commands with a timeout; it strips common credential environment variables and does not call live workspace APIs.

## Operating Protocol

1. Verify the installed CLI surface with `lep --version`, `lep --help`, and the relevant `lep <group> --help` before relying on a command or flag.
2. Expand hidden aliases and abbreviations to full command names in any plan or final command. Do not use abbreviated commands for mutations.
3. Classify the requested operation: help/version, read-only, local-state mutation, cloud mutation, destructive cloud mutation, remote file mutation, local file write, or interactive session.
4. For reads, use the narrowest command that answers the question and avoid token-printing commands unless the user explicitly asks for them.
5. For every mutation or destructive operation, read current state first when possible, then present the exact command, target resource, intended workspace, observed state, and one-sentence impact. Execute only after explicit confirmation for that single target.
6. For logs and file-output options, scope by resource name, replica/job/time/query/path before running, and confirm local write destinations.
7. If help output or the installed version disagrees with these references, treat the installed `lep` help as authoritative and update the plan accordingly.
