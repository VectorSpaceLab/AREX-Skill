# CLI Troubleshooting

## `lep` Is Missing

Symptoms:

```text
lep: command not found
No such file or directory: 'lep'
```

Actions:

1. Confirm whether the LeptonAI package CLI is installed and exposed on `PATH`:

   ```bash
   command -v lep
   lep --version
   ```

2. If missing, ask the user to install or expose the package CLI. The public install command is:

   ```bash
   pip install -U leptonai
   ```

3. Do not run live Lepton operations through guessed scripts or source checkout paths. Re-run `lep --help` after installation.

## Empty String Option Rejected

The CLI applies a global click guard that rejects empty or whitespace-only strings provided on the command line. This applies to single string options and repeated string options.

Symptoms:

```text
Invalid value for '--name' / '-n': must not be empty or only whitespace. Omit the flag instead of passing an empty string.
Invalid value for '--name' / '-n': contains empty value(s). Remove empty items.
```

Actions:

- Omit optional flags instead of passing `""`.
- For required flags such as names, ask the user for a real value.
- For repeated options, remove the empty item and keep only non-empty values.
- Re-run `lep <group> <subcommand> --help` to confirm whether the option is optional or required.

## Command Ambiguity Or Abbreviation Surprise

Symptoms:

```text
Error: 'fi' is ambiguous: file, finetune
Error: 'l' is ambiguous: log, login, logout
Error: No such command '...'
```

Why it happens:

- The CLI allows ordered-subsequence abbreviations only when exactly one command matches.
- Hidden aliases can participate in matching, so visible help may not show every ambiguity.

Actions:

1. Run `lep --help` and the relevant full group help.
2. Replace abbreviations with full command names in plans and execution commands.
3. If a hidden alias caused confusion, prefer the visible canonical command when possible: `endpoint` over hidden `deployment`; use `storage` or `file` only after `lep <alias> --help` confirms availability.
4. Never execute a mutating command through an abbreviation.

## Version Check Warning

Symptoms:

```text
A newer version of leptonai (...) is available. You are using (...). Run `pip install -U leptonai` to upgrade.
```

Meaning:

- The CLI performs a best-effort package version check against PyPI at a cache interval.
- Network failures during this check are ignored by the CLI.
- The warning can appear before normal command output and does not by itself mean the command failed.

Actions:

- Check the command exit status separately.
- Use `lep --version` to record the installed version.
- If behavior or flags differ from these references, trust installed help and consider refreshing the repo skill after upgrade.

## Network Or Auth Failure From A Read-Only Command

Symptoms can include unauthorized/forbidden/not-found workspace messages, connection failures, DNS failures, socket errors, or API client errors after a read-only command such as `workspace status`, `endpoint list`, or `ingress list`.

Actions:

1. Do not retry mutations. Stay in read-only mode.
2. Confirm the CLI surface still works with `lep --help` and `lep workspace --help`.
3. Use workspace/auth handling to check workspace selection and login status. Do not print raw tokens in the CLI transcript or final answer.
4. If the error is a sandboxed network or DNS/socket issue, report the exact non-secret error and ask whether the user wants to retry in an environment with network access.
5. If the error is `401`, `403`, or workspace-not-found, route to workspace/auth troubleshooting instead of inventing credentials or switching workspaces.

## Destructive Command Confirmation Is Unclear

Symptoms:

- User asks for deletion/removal/stop/update but does not name a resource.
- User says “yes” without the command, workspace, or target being restated.
- A bulk command such as `job remove-all`, `job stop-all`, or `ingress set-endpoints` could affect more resources than expected.
- A storage path is ambiguous, relative, or could delete a directory recursively.

Actions:

1. Stop before mutation.
2. Run or request a read-only state check when possible.
3. Restate the exact full command, workspace, target(s), current state, and impact.
4. Ask for explicit confirmation for that one command and target set.
5. For bulk commands, enumerate the filters and require confirmation that the filter set is complete. For `ingress set-endpoints`, list every endpoint that will remain; omitted endpoints will be removed.
6. If the user only wants a plan, provide the plan and explicitly state that no live command was run.

## Hidden Storage Or Deployment Commands Not Shown In Top Help

Symptoms:

- `lep --help` does not list `deployment`, `storage`, or `file`.
- The user asks for older `lep deployment ...` or `lep file ...` syntax.

Actions:

```bash
lep deployment --help
lep storage --help
lep file --help
```

If help succeeds, use the command set shown there. Prefer visible `endpoint` for endpoint/deployment operations when writing new instructions. If neither storage alias works, route storage questions to the storage/secrets/ingress sub-skill and note the installed CLI version mismatch.
