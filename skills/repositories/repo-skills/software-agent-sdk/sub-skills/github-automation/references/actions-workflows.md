# GitHub Actions Workflows

## Prompt runner pattern

The prompt runner accepts either:

- a `PROMPT_STRING` environment variable, or
- a `prompt_location` CLI argument pointing to a local file or URL.

It must not accept both at once.

Typical steps:

1. Load the prompt from the selected location.
2. Build `LLM` from `LLM_API_KEY`, `LLM_MODEL`, and optional `LLM_BASE_URL`.
3. Create the default CLI-friendly agent with `get_default_agent(cli_mode=True)`.
4. Create `Conversation(agent=..., workspace=os.getcwd())`.
5. Send the prompt and run the conversation.

## TODO scanner pattern

- Scan source files for a configurable identifier such as `TODO(openhands)`.
- Skip test/example paths and unsupported extensions.
- Return structured JSON records with file path, line, and description.

## Example report renderer

- Load per-example JSON result files.
- Normalize status, duration, and cost fields.
- Render a markdown table and summary for a workflow run.

## When to use these helpers

- CI jobs that need a deterministic prompt runner.
- Repo automation that turns TODOs into work items.
- Workflow summaries that need a concise report artifact.
