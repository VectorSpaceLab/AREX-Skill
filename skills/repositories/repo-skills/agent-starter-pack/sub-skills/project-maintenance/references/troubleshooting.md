# Maintenance troubleshooting

## `enhance` problems
### The project structure looks wrong
- Confirm the user is pointing at the existing project root.
- Check whether the agent directory is the default `app` or a custom path.
- If the structure is clearly incompatible, ask whether the user wants to adapt the scope before proceeding.

### Backup creation fails
- Treat backup failures as a real risk to in-place modification.
- If the user is unwilling to continue without a backup, stop instead of pretending the run succeeded.

### Base-template override adds dependencies
- That is expected when the user chooses a different foundation.
- Explain that dependency prompts are part of the enhancement workflow, not an error.

## `extract` problems
### Unsupported language or layout
- The command is intended for the supported generated-project layouts.
- If the language is unsupported, direct the user back to the template catalog or ask whether they want a different path.

### The output already exists
- Use `--force` only when the user wants replacement.
- Otherwise suggest a new destination.

### Too much or too little scaffold is removed
- Verify the project really came from Agent Starter Pack.
- Use the maintenance workflow reference to decide whether the issue is with the source project, not the extractor.

## `upgrade` problems
### Missing ASP metadata or version marker
- A project without `asp_version` is not ready for upgrade.
- Explain how the upgrade command discovers the original version before comparing templates.

### Conflicts during merge
- Conflicts are expected when both the user and ASP changed the same file.
- Use the built-in conflict handling rather than inventing a blanket overwrite strategy.

### `uvx` is unavailable
- Version-locked regeneration depends on `uvx`.
- If `uvx` is missing, the environment or user setup must be fixed before an upgrade workflow can be trusted.

## General guidance
- Maintenance errors are usually about project state, not package importability.
- Use the root package sanity checker for install problems and this page for project-state problems.
