# Scaffolding troubleshooting

## Template selection problems
### The template name is invalid
- Confirm the user is asking for a built-in template that exists in the catalog.
- If the user supplied a number, make sure the selection comes from the current `list` output.
- If the user supplied an alias or remote shorthand, treat it as a parsing problem, not a missing template.

### The source is remote but not recognized
- Try interpreting the input as `local@...`, `adk@...`, `adk-py@...`, or a full Git URL.
- If none of those fit, the user may actually want a local template path.

## Generation problems
### Project name or agent-directory is rejected
- Project names are normalized for cloud-friendly naming.
- Python agent directories must still be valid module names.
- Use the project-scaffolding reference for `--in-folder`, `--agent-directory`, and remote-template rules before guessing at a fix.

### `--base-template` triggers dependency prompts
- That is expected for remote templates.
- Explain that the override may add base-template dependencies to the generated project.

### A template claims data ingestion or sessions unexpectedly
- Some templates auto-enable those prompts by design.
- `agentic_rag` is the clearest example for data ingestion.
- Defer to the template catalog before telling the user the prompt is wrong.

## Environment/tooling problems
- If the user lacks `uvx`, the remote-template version-lock path may fail even when the template itself is valid.
- If the user cannot access the network, remote templates and ADK-samples browsing are not the right route.
- If the user only needs a local sanity check, use the bundled install helper instead of starting a generation run.
