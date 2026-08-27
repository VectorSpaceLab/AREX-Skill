# Install and Distribution Reference

## Platform Layouts

ARIS installs skills project-locally. The official installers use symlinks where supported and maintain manifests so reconcile/uninstall never touches unrelated user files.

| Host | Skill destination in a user project | Manifest | Notes |
| --- | --- | --- | --- |
| Claude Code / Cursor / Trae / Antigravity | `.claude/skills/<skill-name>` | `.aris/installed-skills.txt` | Mainline `skills/<name>/SKILL.md` layout. The installer also manages `.aris/tools` for helper lookup and can update `CLAUDE.md`. |
| Codex CLI | `.agents/skills/<skill-name>` | `.aris/installed-skills-codex.txt` | Uses `skills/skills-codex/` mirrors. Optional Claude-review and Gemini-review overlays can replace selected mirrors. |
| GitHub Copilot CLI | `.github/skills/<skill-name>` | `.aris/installed-skills-copilot.txt` | Uses mainline skills because Copilot CLI supports `SKILL.md` semantics directly. |
| Standalone ARIS-Code | ARIS-Code-managed bundle | ARIS-Code runtime state | Treat as a separate CLI distribution. Check the user's installed ARIS-Code release before assuming current README defaults. |

## Install Decision Pattern

1. Confirm the target research project path and host platform.
2. Confirm whether ARIS should install all skills, a group subset, a skill subset, or only reconcile an existing manifest.
3. Use dry-run or read-only inspection first when the project already has skill directories.
4. Run the official installer from the user's chosen ARIS checkout or release, not from this generated skill directory.
5. Restart the host agent after changing MCP server configuration; MCP settings are loaded at startup.

## Common Installer Flags

- `--list-groups`: print the skill-group catalog and exit.
- `--groups A,B`: install whole groups from the catalog.
- `--skills X,Y`: add explicit skills; dependencies are pulled from the catalog unless excluded.
- `--exclude X,Y`: mark skills as declined and remove them on reconcile when applicable.
- `--all`: install every upstream skill.
- `--dry-run`: show the plan without writes.
- `--quiet`: avoid prompts; abort if an unsafe prompt would be required.
- `--add-new`: during reconcile, accept upstream skills not yet installed.
- `--skip-new`: during reconcile, leave new upstream skills uninstalled without marking them declined.
- `--replace-link NAME`: replace a conflicting symlink only for that specific skill name.
- `--adopt-existing NAME`: for the Claude installer, adopt a pre-existing symlink that already points at the expected upstream target.
- `--uninstall`: remove only manifest-owned entries.

## Safety Invariants

- Do not overwrite real files or directories during create.
- Do not delete symlinks that are outside the configured ARIS checkout.
- Do not delete symlinks that are not listed in the relevant manifest, except for the special `.aris/tools` symlink when it exactly matches the managed target.
- Treat `.aris/`, host skill roots, and host skill directories as unsafe if they are themselves unexpected symlinks.
- Manifest writes are atomic and installer runs serialize through a lock directory.
- A crash should leave the previous manifest intact; rerun reconcile rather than manually deleting unknown paths.

## Verification Hints

Use the bundled read-only doctor before and after installation:

```bash
python scripts/aris_project_doctor.py --project /path/to/research-project
```

For a no-mutation preview, prefer the official installer `--dry-run` mode. For repo maintenance, run installer tests with temporary fixtures rather than manually testing on a real research project.
