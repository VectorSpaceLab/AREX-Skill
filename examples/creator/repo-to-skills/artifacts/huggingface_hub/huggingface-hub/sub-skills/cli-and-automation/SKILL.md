---
name: cli-and-automation
description: "Routes reliable Hugging Face Hub CLI and shell automation, including hf output modes, authentication, file movement, repository and catalog operations, hosted jobs, extensions, and agent-skill generation. Use for hf command selection, JSON or quiet parsing, login and token handling, dry-run or confirmation planning, extensions, or compatible CLI skills."
disable-model-invocation: true
license: Apache-2.0
metadata:
  disco-role: operating
---

# CLI and Automation

Use this sub-skill when a researcher needs to select, explain, or safely
automate the `hf` command-line interface. Treat the installed executable's
`--help` as the release-specific authority: the generated CLI surface changes
with the installed `huggingface_hub` version.

## Trigger routes

Load this skill for:

- “what `hf` command/flag should I use?” and shell scripts around the Hub;
- human, JSON, quiet, or agent output, `jq`/pipeline parsing, or stderr hygiene;
- login, token selection, `HF_TOKEN`, auth state, or non-interactive operation;
- downloads, uploads, `hf cp`, bucket sync, URI/revision/type selection, or
  dry-run/plan/apply review;
- repos, branches, tags, models, datasets, Spaces, cards, search, papers,
  discussions, webhooks, cache, endpoints, buckets, Jobs, or sandboxes;
- trusted CLI extension install/update/remove/dispatch or extension authoring;
- `hf skills add`, `update`, `preview`, marketplace skills, or the implicit
  skill freshness check.

## First route: establish the executable

Read [CLI reference](references/cli-reference.md) before using a detailed
flag. Run only safe probes first:

```bash
command -v hf && hf --help
hf version
hf --version
```

`hf` is the supported entry point. `huggingface-cli` is a deprecated entry
point and may warn and exit instead of providing the old CLI. `tiny-agents` is
a separate MCP/agent CLI, not an alias for `hf`; inspect it with
`tiny-agents --help` and do not infer its syntax from this skill. If the
commands resolve to different installations, report the paths and use the
one intended by the current environment.

## Safe operating loop

1. Classify the request as read-only, local-only, Hub mutation, or hosted
   compute. Ask for the target namespace/repo and permission when a mutation
   is intended; placeholders are not authorization.
2. Check `hf <group> --help` and then `hf <group> <command> --help` for the
   installed version. Do not copy a flag from an older generated reference
   without checking help.
3. Select an explicit output mode for scripts. Parse **stdout only**; keep
   stderr visible for warnings, hints, errors, and progress diagnostics.
4. Supply credentials through the environment or a supported secret-file
   mechanism. Never print, echo, log, commit, or put a token in a URL.
5. For movement or deletion, preview first (`--dry-run`, `--plan`, or a
   read-only list), inspect the exact target and action set, then obtain
   confirmation before applying.
6. Pin `--repo-type`/`--revision` or encode them in one `hf://` URI. Never
   combine URI-encoded type/revision/path with duplicate positional/options.
7. Check exit status. For Jobs and Spaces, a streamed log ending is not proof
   of success; inspect or wait for the terminal status.
8. Record the command, selected version, output mode, target, and whether the
   operation was previewed. Redact credentials from logs.

## Progressive disclosure

- Use [CLI reference](references/cli-reference.md) for the command catalog,
  verified flags, aliases, output semantics, URI rules, safety boundaries, and
  the `skills`/extensions surface.
- Use [automation workflows](references/automation-workflows.md) for safe
  stdout/stderr pipelines, download dry runs, bucket plan/apply, job control,
  and mutation gates.
- Use [API reference](references/api-reference.md) only when output or the
  lightweight Click-compatible framework explains a surprising CLI behavior.
- Use [development](references/development.md) when generated CLI docs,
  static imports, or release-surface drift is involved.
- Use [troubleshooting](references/troubleshooting.md) for installation,
  auth, parsing, URI, network, extension, and generated-doc failures.
- Run the bundled read-only [help checker](scripts/check_cli_help.py) when
  entry-point health or a bounded help smoke test is useful. It accepts only a
  trusted executable named `hf`, bounded timeouts/probe counts, and exact
  allowlisted built-in command paths with no arguments; every invocation ends
  in `--help`. It never invokes a mutating command and always disables startup
  update checks for its child processes.

## Routing map

| Need | Route |
|---|---|
| Format, parse, auth, shell safety | CLI reference → automation workflows |
| Download/cache/read path | `downloads-and-storage` sibling, then this skill for CLI flags |
| Upload, repo CRUD, branches/tags, discussions | `hub-operations` sibling, with this skill for command routing |
| Models/datasets/Spaces catalog or cards | this skill; route inference endpoint details to its sibling |
| Jobs, sandboxes, buckets, cloud storage | this skill; use dry-run/plan gates |
| Python API rather than a terminal command | the relevant sibling/API skill |

This sub-skill does not replace the sibling operating skills for detailed
Python APIs, inference behavior, cache internals, or Hub mutation policy. It
owns the CLI boundary and automation contract.

## Non-negotiable safety rules

- An example that creates, uploads, deletes, changes visibility, changes a
  Space, manages a webhook, installs an extension/skill, launches compute, or
  applies a plan is a mutation. Use a clearly marked mutation example only
  after target and authorization are confirmed; prefer placeholders.
- `--yes` bypasses a confirmation gate; it does not make the target safe.
  Never add it merely to make a script non-interactive.
- `--format json` does not mean every command is non-interactive. In
  particular, login's browser/menu flow has restrictions; use an environment
  token for automation.
- `hf auth token` intentionally prints a secret. Treat it as a narrow,
  deliberate pipe, never as a diagnostic command.
- Do not use `hf cp` for local-to-local or unsupported bucket-to-repo copies;
  use the documented alternative. Do not pass a directory to single-file `cp`.
- `hf skills preview` produces generated target-side `hf-cli/SKILL.md`
  content. That generated file is distinct from this managed
  `huggingface-hub/sub-skills/cli-and-automation/` skill; do not overwrite or
  present one as the other.

## Verification targets

A useful route ends with observable evidence: help exits zero; stdout parses
under the selected mode; stderr remains separate; a dry-run/plan reports the
intended actions without payload mutation; refused confirmation exits non-zero;
and a final status command verifies the operation. For the difficult synthetic
case, use a fake CLI/API fixture or help-only invocation to exercise a
`hf download --dry-run --format json` parse, preserve a warning on stderr, and
prove that `hf repos delete` without `--yes` is refused before any delete API
call. Broad production-marked native tests do not establish this end-to-end
shell contract.
