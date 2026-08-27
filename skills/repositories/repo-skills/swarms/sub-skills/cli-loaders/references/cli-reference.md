# CLI reference

## Command catalog

| Command | Purpose | Most relevant flags / inputs |
| --- | --- | --- |
| `init` | Scaffold a project workspace | `--dir` |
| `onboarding` | Alias for `setup-check` | `--verbose` |
| `get-api-key` | Open key retrieval flow | none |
| `check-login` | Verify auth state | none |
| `run-agents` | Load and run agents from YAML | `--yaml-file` |
| `load-markdown` | Load agents from markdown files | `--markdown-path`, `--concurrent` |
| `agent` | Create and run a custom agent | `--name`, `--description`, `--system-prompt`, `--task`, `--model-name`, `--interactive`, `--no-interactive`, `--max-loops`, `--temperature`, `--autosave`, `--streaming-on`, `--context-length`, `--marketplace-prompt-id`, `--mcp-url` |
| `chat` | Interactive agent chat | same family as `agent` |
| `upgrade` | Upgrade the installed package | none |
| `autoswarm` | Generate a swarm configuration and optional runner | `--task`, `--model`, `--output`, `--output-dir`, `--no-run` |
| `setup-check` | Validate environment and package readiness | `--verbose` |
| `llm-council` | Run the council workflow | `--task`, `--verbose` |
| `heavy-swarm` | Run the heavy swarm workflow | `--task`, `--loops-per-agent`, `--question-agent-model-name`, `--worker-model-name`, `--random-loops-per-agent`, `--verbose` |
| `tips` | Show curated tips | `--count`, `--category`, `--all` |
| `models` | Search or inspect available models | `--search`, `--info`, `--provider` |

## Parser facts

- The parser uses a custom help action rather than standard argparse help output.
- The command name is required.
- `max_loops` is parsed as text first and later converted, so the string `auto` is valid for the agent command family.
- `load-markdown` requires `--markdown-path`.
- `autoswarm` needs both a task and a model to be useful.

## Loader facts

### YAML configs

`load_yaml_safely()` validates a config into this shape:

- top-level `agents` list is required
- `swarm_architecture` is optional
- each agent should provide at least `agent_name` and `system_prompt`
- swarm metadata may include name, description, `swarm_type`, `task`, `flow`, `autosave`, `return_json`, and `rules`

### Markdown configs

`MarkdownAgentLoader` expects:

- YAML frontmatter at the top of the file
- a `name` and `description` in frontmatter, with the remaining body becoming the system prompt
- one file per agent, or a directory of such files

## Common command shapes

```bash
swarms agent --name Demo --description "Demo agent" --system-prompt "You are helpful" --task "Say hello"
swarms run-agents --yaml-file agents.yaml
swarms load-markdown --markdown-path ./agents
swarms autoswarm --task "Analyze quarterly sales" --model "gpt-4"
```

## Discovery commands

- `swarms setup-check` verifies the local environment.
- `swarms tips` surfaces command and environment tips.
- `swarms models` helps users find a usable provider model string before they run a live task.
