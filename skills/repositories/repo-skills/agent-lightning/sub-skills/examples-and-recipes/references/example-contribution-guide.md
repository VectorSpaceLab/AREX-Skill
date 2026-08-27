# Example contribution guide

## Purpose

Use this when adding or maintaining an Agent Lightning example.

## Required README content

Every example should include a README with:

- purpose and target workflow,
- setup prerequisites and optional dependency groups,
- smoke-test instructions maintainers can run quickly,
- expected inputs, outputs, and external services,
- an **Included Files** section listing every file and its role.

Example shape:

```markdown
## Included Files

| File | Role |
| --- | --- |
| `agent.py` | Defines the trainable agent and task schema. |
| `train.py` | Runs the trainer with selected algorithm and resources. |
| `README.md` | Setup, smoke test, and troubleshooting instructions. |
```

## Example script style

- Keep runnable modules self-contained.
- Add a module-level docstring with CLI usage.
- Document important educational classes/functions with concise docstrings.
- Add inline comments only where they clarify non-obvious control flow.
- Avoid hard-coded secrets, absolute paths, generated checkpoints, large downloads, or unbounded training defaults.

## CI and badge expectations

For a new example that should be tracked by CI:

1. Add a workflow named `examples-<name>.yml` under `.github/workflows/`.
2. Register the badge in the example badge aggregation workflow set when applicable.
3. Keep the CI mode bounded: small datasets, short runtime, no uncontrolled service cost.
4. Mark optional suites so they can be skipped when credentials, GPU, Mongo, Docker, or external services are unavailable.

## Dependency documentation

State whether the example needs:

- base package only,
- `apo`, `verl`, `mongo`, or `weave` extras,
- torch/vLLM/TRL/Unsloth dependency groups,
- `agents`, `langchain`, `rag`, `tinker`, `image`, or `sql` groups,
- OpenAI-compatible, Azure, Anthropic, Tinker, or W&B credentials,
- GPU/CUDA, Docker, Ray, Node/npm, or large datasets.

## Testing guidance

- Prefer small assertion-backed smoke tests.
- Use pytest markers for optional backends such as `openai`, `gpu`, `agentops`, `mongo`, `llmproxy`, `weave`, or `prometheus` where appropriate.
- Make it possible to validate at least import/config/help behavior without external services.
- Do not create fake stubs for external dependencies unless necessary for bounded testing.

## Documentation and style reminders

- Use Google-style docstrings for public functions/classes.
- Keep line length near the repository convention.
- Use snake_case for Python modules and functions.
- Use lowercase hyphenated CLI flags.
- For docs, keep commands copyable and avoid links that require local absolute paths.

## Safety checklist before running a full example

- Did the user authorize external API use or cost?
- Is the required GPU/service/data available?
- Is the target environment separate from the minimal CPU environment when heavy dependencies are involved?
- Are cleanup actions explicit and non-destructive by default?
- Are secrets passed through environment variables or provider config rather than printed?
