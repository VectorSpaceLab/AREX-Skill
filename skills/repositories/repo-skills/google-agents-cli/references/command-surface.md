# Command Surface and Safe Inspection

This reference records the installed `agents-cli` command families verified for `google-agents-cli` 1.3.1. Use the sub-skills for workflow details; use this file for routing and quick command discovery.

## Top-Level Commands

| Command | Purpose | Primary sub-skill |
| --- | --- | --- |
| `agents-cli setup` | Install Agents CLI skills into detected coding-agent targets | `workflow` |
| `agents-cli update` | Force reinstall Agents CLI skills into detected coding-agent targets | `workflow` |
| `agents-cli login` | Authenticate with Google Cloud or AI Studio | `workflow`, `deploy`, `publish` |
| `agents-cli info` | Show project configuration, paths, and CLI version | `workflow` |
| `agents-cli create` | Alias for project creation from templates | `scaffold` |
| `agents-cli scaffold create` | Create a new ADK project | `scaffold` |
| `agents-cli scaffold enhance` | Add deployment/CI-CD/infrastructure to an existing project | `scaffold`, then `deploy` |
| `agents-cli scaffold upgrade` | Upgrade a scaffolded project to a newer Agents CLI template | `scaffold` |
| `agents-cli install` | Install project dependencies | `workflow` |
| `agents-cli lint` | Run code quality checks | `workflow` |
| `agents-cli playground` | Start local playground | `workflow`, `deploy` |
| `agents-cli run` | Run one prompt locally or against a deployed URL | `workflow`, `deploy` |
| `agents-cli eval ...` | Generate, grade, analyze, compare, optimize evals and metrics | `eval` |
| `agents-cli deploy` | Deploy the scaffolded project | `deploy` |
| `agents-cli infra single-project` | Provision single-project infrastructure such as observability resources | `deploy`, `observability` |
| `agents-cli infra cicd` | Provision CI/CD infrastructure | `deploy` |
| `agents-cli publish gemini-enterprise` | Register deployed agents with Gemini Enterprise | `publish` |
| `agents-cli data-ingestion` | Removed stub; RAG is now recipe-based | `adk-code` |

## Safe Discovery Commands

These are safe to run in a prepared environment because they only inspect parsers or local project metadata:

```bash
agents-cli --version
agents-cli --help
agents-cli scaffold --help
agents-cli eval --help
agents-cli deploy --help
agents-cli publish gemini-enterprise --help
agents-cli info
python scripts/inspect_cli_tree.py --depth 3
```

`agents-cli info` is read-only, but its output is most useful from inside a scaffolded project. Avoid copying local absolute paths from `info` output into public documentation.

## Commands Requiring Care

| Command | Why careful | Before running |
| --- | --- | --- |
| `agents-cli scaffold create` | Creates a new project directory | Confirm project name, path, template, deployment target, and whether prototype-first is desired |
| `agents-cli scaffold enhance` | Mutates an existing project | Confirm target directory, agent directory, and requested additions |
| `agents-cli deploy` | Creates/updates cloud resources | Confirm GCP project/region/target, auth, cost, and deployment intent |
| `agents-cli infra single-project` / `infra cicd` | Provisions Terraform resources | Confirm projects, repo ownership, state strategy, credentials, and cost |
| `agents-cli publish gemini-enterprise` | Registers/updates a deployed agent | Confirm Gemini Enterprise app, registration type, endpoint/runtime ID, and IAM |
| `agents-cli update` / `setup` | Writes skills into coding-agent directories | Confirm the target agent/tool if the user cares about exact destinations |

## Installed-Package Inspection Pattern

When command behavior is unclear, inspect the installed Click tree rather than guessing:

```bash
python scripts/inspect_cli_tree.py --json --depth 4
```

For source-level implementation details, the generated sub-skills already distill the relevant repo evidence; future users should not need the original checkout for normal operation.
