# CLI and loader workflows

## 1. Validate the environment

Use `setup-check` first when the user is unsure whether the package is ready.

```bash
swarms setup-check --verbose
```

What to look for:

- Python version support
- package importability
- environment variables
- workspace setup
- obvious missing dependencies

## 2. Create and run a single agent from the CLI

```bash
swarms agent \
  --name "Researcher" \
  --description "Collects and summarizes facts" \
  --system-prompt "You are a careful researcher" \
  --task "Summarize the repository" \
  --model-name "gpt-5.4"
```

Use this when the user wants a quick command-line agent instead of writing Python.

## 3. Run agents from YAML

A minimal YAML shape:

```yaml
agents:
  - agent_name: DemoAgent
    system_prompt: You are a concise assistant.
    model_name: gpt-5.4
    max_loops: 1
```

Use `run-agents` when a task should be described declaratively.

## 4. Load agents from markdown

A minimal markdown shape:

```markdown
---
name: DemoAgent
description: Demo markdown agent
model_name: gpt-5.4
max_loops: 1
---
You are a concise assistant.
```

Use `load-markdown` when the user already has markdown-based agent files or wants a Claude Code–style frontmatter layout.

## 5. Generate a swarm with autoswarm

`autoswarm` first generates a configuration and optionally runs it immediately.

- Use `--no-run` when the user only wants the generated file.
- Use `--output` or `--output-dir` to control where the generated script lands.
- Keep the model string explicit so the generated swarm is reproducible.

## 6. Discovery and diagnostics

- `tips` helps users learn the command surface.
- `models` helps users pick a compatible provider/model string.
- `get-api-key` and `check-login` are for auth bootstrap, not for running a task.

## Loader validation habit

When a user provides YAML or markdown, validate the file shape before trying a live run. That separates syntax or schema errors from provider or model errors.
