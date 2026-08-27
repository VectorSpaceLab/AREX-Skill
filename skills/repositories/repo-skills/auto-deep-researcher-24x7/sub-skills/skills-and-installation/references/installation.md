# Installation and ownership reference

This reference describes the observed installer contract. It is intentionally
self-contained: use it to decide whether an operation is safe without opening
source files or relying on an external artifact.

## Source discovery

The installer treats the repository's `skills/` directory as a source root. It
sorts its immediate children and selects only directories containing
`SKILL.md`. The current source set is exactly:

```text
auto-experiment
conf-search
daily-papers
experiment-status
gpu-monitor
obsidian-sync
paper-analyze
progress-report
```

A deeper directory is not discovered. This matters for generated output: a
nested `skills/disco/<repo-skill>` tree is an active generated root, not an
extra source skill to flatten into the eight-command set.

## `python install.py` behavior

The public install command has no interactive confirmation and defaults to the
user's Claude and Codex directories. Therefore it is a mutating operation and
must be preceded by an explicit user request. Its effective order is:

1. Build the source set from immediate `skills/` children.
2. Preflight every Codex destination. For each destination that already exists,
   require the ownership marker `.deep-researcher-installed`.
3. Create the Claude `commands/` directory and copy each source `SKILL.md` to a
   same-named `.md` command file. Existing Claude command files are replaced;
   Claude has no ownership marker or refusal gate.
4. Create the Codex `skills/` directory. For every source skill, remove an
   existing *marked* destination, copy the complete source skill directory, and
   rewrite only its copied `SKILL.md` with Codex-compatible frontmatter.
5. Write `.deep-researcher-installed` in each installed Codex skill directory.
6. Copy top-level Python files from the repository's `core/` and `gpu/`
   directories into a runtime bundle under each of the two agent homes. Copy
   `config.yaml` only when that bundle does not already have one.
7. Print the installed counts and the eight Claude `/name` and Codex `$name`
   entry points.

The conflict preflight runs before the Claude copy, so an unmarked Codex
collision should leave the Claude command destination untouched. The installer
has no rollback transaction for failures after that preflight: if a later copy
or runtime-bundle step fails, inspect the resulting temporary or user-approved
state before retrying. An already marked Codex destination is installer-owned
and is replaced during a rerun.

## Claude versus Codex rendering

Claude receives the source text verbatim. This preserves any source-only
frontmatter such as `argument-hint` and preserves the source body, including
examples that show `/skill-name`.

Codex receives a transformed copy:

- The source YAML frontmatter must begin at byte zero with `---`, contain a
  closing `---`, and parse as a mapping.
- Only `name`, `description`, `license`, `allowed-tools`, and `metadata` survive
  into the rendered frontmatter. Unsupported keys, including `argument-hint`,
  are dropped.
- The YAML is re-emitted in source insertion order and the original body is
  left-stripped.
- A blockquote is inserted before the body: invoke explicitly as
  `$<name>` when needed; source documentation may show `/<name>` because the
  same skill also powers Claude slash commands.
- Supporting files are copied as files. `agents/openai.yaml` is Codex UI/export
  metadata and must not be copied into a generated source reference or treated
  as the operating body.

The eight current source `SKILL.md` files use only `name` and `description`
in frontmatter. Their exact names/descriptions are recorded in the source
integration reference.

## Uninstall behavior

The public uninstall command is also mutating and requires an explicit request.
For each currently discovered source skill it:

- unlinks the same-named Claude command if it exists, regardless of whether a
  user edited or replaced it;
- removes the same-named Codex skill directory only if the ownership marker is
  present; and
- removes the per-agent runtime bundle directory when present.

The marker gate protects Codex skill directories but does not protect Claude
command files or the runtime bundle. A missing source skill is not discovered,
so its old installed command is not selected by the loop. An unmarked Codex
collision is left intact by uninstall.

## Safe temporary verification

A safe rehearsal must never rely on default home paths. Build a tiny temporary
fixture with:

- one or more immediate source skill directories and minimal `SKILL.md` files;
- optional `agents/openai.yaml`, `core/*.py`, `gpu/*.py`, and `config.yaml`;
- separate temporary Claude and Codex destination directories.

Invoke the installer API with explicit fixture paths, then assert:

1. Claude receives unchanged source text.
2. Codex receives the marker and transformed text, without unsupported
   frontmatter keys.
3. an unmarked pre-existing Codex destination raises a conflict before Claude
   is written;
4. a marked destination can be replaced; and
5. uninstall preserves an unmarked Codex destination and removes only the
   marked destination and runtime bundle.

Use the read-only `scripts/check_skill_layout.py` for source discovery and
nested-root checks. Do not bundle or invent a home-mutating installer.
