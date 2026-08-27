# Package overview

Agent Starter Pack is a Python CLI that bootstraps production-ready Google Cloud GenAI agent projects from templates.

## Public identity
- Distribution: `agent-starter-pack`
- Console entry point: `agent_starter_pack.cli.main:cli`
- Top-level commands: `create`, `enhance`, `extract`, `list`, `setup-cicd`, `upgrade`, `register-gemini-enterprise`
- Supported template languages: Python, Go, Java, TypeScript

## Quick read-only installation check
Use these when you only need to confirm the package is installed and importable:

```bash
uvx agent-starter-pack --help
agent-starter-pack --version
python scripts/check_agent_starter_pack.py
```

If you are working inside a prepared inspection environment, the helper script is the safest first check because it only imports the installed package and reports command metadata.

## Where the runtime logic lives
- `agent_starter_pack/cli/commands/` contains the user-facing commands.
- `agent_starter_pack/cli/utils/` contains template discovery, remote-template parsing, language detection, backup/merge, CI/CD, and cloud-auth helpers.
- `agent_starter_pack/agents/` holds the built-in template catalog.
- `agent_starter_pack/base_templates/` and `agent_starter_pack/deployment_targets/` define generated-project structure.

## Route map
- `project-scaffolding`: create/list/remote-template selection and first-run generation choices.
- `project-maintenance`: enhance/extract/upgrade and version-locked project upkeep.
- `deployment-ops`: CI/CD bootstrap, generated-project deployment commands, data ingestion, observability, and Gemini Enterprise registration.

## User-facing themes
- Project generation uses templates plus optional remote repositories.
- Generated projects are meant to be edited and then deployed with the generated `Makefile`.
- Deployment workflows are cloud-oriented and may require Google Cloud, GitHub, and Terraform tooling.
- The package is a template generator, not a runtime agent framework itself.
