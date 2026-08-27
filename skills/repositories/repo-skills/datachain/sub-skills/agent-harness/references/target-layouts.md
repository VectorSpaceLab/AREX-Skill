# Target Layouts for DataChain Agent Skills

DataChain installs bundled skills into the directory convention of the selected
coding-agent target. The install command copies the selected skill directories
and, where the target supports command/rule files, writes a `datachain-<skill>`
command or instruction file.

## Commands

```bash
datachain skill list
datachain skill install [core,knowledge,jobs] --target <target> [--local]
datachain skill uninstall [core,knowledge,jobs] --target <target> [--local]
```

- Valid skills: `core`, `knowledge`, `jobs`. Omit the skill list to install or
  uninstall all three.
- Valid targets: `claude`, `cursor`, `codex`, `pi`, `copilot`.
- Global mode writes under the user's home directory.
- `--local` writes under the current working directory. Run it from the project
  root you want the agent to use.

Use [skill_layout_check.py](../scripts/skill_layout_check.py) to print the
resolved directories without mutating files.

## Layout Matrix

| Target | Global skill copy | Global command/rule files | Local skill copy | Local command/rule files | Notes |
| --- | --- | --- | --- | --- | --- |
| Claude | `~/.claude/skills/<skill>/` | none | `<project>/.claude/skills/<skill>/` | `<project>/.claude/commands/datachain-<skill>.md` | Claude command files are local-only; global install copies skills only. |
| Cursor | `~/.cursor/skills/<skill>/` | `~/.cursor/rules/datachain-<skill>.mdc` | `<project>/.cursor/skills/<skill>/` | `<project>/.cursor/rules/datachain-<skill>.mdc` | Cursor command files are transformed to `.mdc` rule frontmatter. |
| Codex | `~/.codex/skills/<skill>/` | none | `<project>/.codex/skills/<skill>/` | none | Codex target is skills-only. |
| Pi | `~/.pi/agent/skills/<skill>/` | `~/.pi/agent/prompts/datachain-<skill>.md` | `<project>/.pi/skills/<skill>/` | `<project>/.pi/prompts/datachain-<skill>.md` | Local Pi deliberately omits the `agent/` segment. |
| Copilot | `~/.copilot/skills/<skill>/` | `~/.copilot/instructions/datachain-<skill>.instructions.md` | `<project>/.datachain/skills/<skill>/` | `<project>/.github/instructions/datachain-<skill>.instructions.md` | Local Copilot uses canonical GitHub paths for instructions and `.datachain/skills` as the vendor skill copy. |

## Command and Instruction Behavior

- Installed `SKILL.md` files have the `{skill_dir}` placeholder resolved to the
  destination skill directory so command files can call bundled scripts directly.
- Cursor command files are transformed into `.mdc` rules with Cursor-compatible
  frontmatter and `alwaysApply: true`.
- Copilot instruction files strip the original skill frontmatter and prepend
  `applyTo: '**/*.py'`.
- Pi prompt files and Claude local command files use markdown command files.
- Codex does not get separate command files from `datachain skill install`.

## Safe Install Advice

1. Run `datachain skill list` to verify the CLI is importable and see supported
   target names.
2. Use the layout helper before the first install, especially for `--local`.
3. For project-local installs, `cd` to the intended project root first.
4. Do not store custom notes inside an installed DataChain skill directory; a
   reinstall may overwrite files and an uninstall removes the whole skill dir.
5. To repair stale placeholder paths, uninstall and reinstall in the same target
   and scope instead of hand-editing installed command files.

## Safe Uninstall Advice

- Uninstall with the same `--target` and `--local` choice used for install.
  A global uninstall will not remove project-local files, and a local uninstall
  in one project will not remove another project's files.
- When only one skill is problematic, uninstall that skill by name rather than
  all skills, for example `datachain skill uninstall knowledge --target cursor`.
- If a command/rule file exists but the skill directory is missing, uninstall is
  still the safest cleanup path because it removes both surfaces when present.
