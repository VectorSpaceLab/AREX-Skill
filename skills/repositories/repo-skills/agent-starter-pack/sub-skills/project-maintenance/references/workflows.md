# Maintenance workflows

## Enhance an existing project
Use `enhance` when the user wants to add Agent Starter Pack scaffolding to a project that already exists.

Typical flow:
1. Confirm the project looks compatible enough to template in place.
2. Detect the current project name, agent directory, language, and saved configuration if present.
3. Decide whether the user wants the current base template or a different one.
4. Create a backup before modifying files.
5. Run the equivalent of `create --in-folder` using the existing project as the target.

Common `enhance` signals:
- `--name`
- `--base-template`
- `--agent-directory`
- `--deployment-target`
- `--datastore`
- `--session-type`
- `--auto-approve`
- `--dry-run`
- `--force`
- `--prefer-new`

## Extract a minimal shareable agent
Use `extract` when the user wants to remove deployment scaffolding and keep just the agent core.

Expected behavior:
- keep the agent directory and core logic
- keep the trimmed `pyproject.toml`
- generate a minimal `Makefile` and `README.md`
- remove deployment, frontend, notebook, and other scaffolding directories
- regenerate the appropriate lock file for the supported language

Current scope note:
- The extractor is aimed at the generated Python and Go project layouts.
- If the user is asking about Java or TypeScript generated output, verify whether they actually mean a different maintenance step instead of assuming `extract` applies.

Signals that belong here:
- `extract`
- `--source`
- `--dry-run`
- `--force`
- sharing or minimal-agent language

## Upgrade a generated project
Use `upgrade` when the user wants to move a project to a newer ASP release.

Core model:
- The old template represents what the project looked like when it was generated.
- The new template represents what the latest ASP release would generate.
- The current project is compared against both to decide what can be auto-updated, preserved, added, removed, or conflicted.

Important behavior:
- Agent code and environment config are preserved rather than blindly overwritten.
- Dependency files are merged specially.
- `--dry-run` previews the result without applying changes.
- `--auto-approve` applies non-conflicting changes automatically.

## Language-awareness
Maintenance commands can behave differently by language.
- Python projects use `pyproject.toml` and `uv` locking.
- Go projects use `.asp.toml`, `go.mod`, and `go mod tidy`.
- Other supported languages may use different saved metadata and project layouts in the enhancement flow.

## When to expect trouble
- The project is missing ASP metadata.
- The project has no `asp_version` marker.
- The backup step fails or the user declines it.
- The current project directory does not look like a generated ASP project.
- A merge conflict needs a human decision.
