# CLI reference

This page is a compact command map for the root router. Read the owning sub-skill for step-by-step workflows.

| Command | Owning sub-skill | Typical intent | Signals to look for |
| --- | --- | --- | --- |
| `create` | `project-scaffolding` | Create a new project from a built-in, local, or remote template | `create`, `template`, `local@`, `adk@`, `--prototype`, `--datastore`, `--session-type`, `--base-template`, `--in-folder` |
| `list` | `project-scaffolding` | Discover built-in templates or scan a local/remote source | `list`, `--adk`, `--source`, `template catalog`, `remote templates` |
| `enhance` | `project-maintenance` | Add Agent Starter Pack scaffolding to an existing project | `enhance`, `in-place`, `current directory`, `backup`, `base template`, `agent-directory` |
| `extract` | `project-maintenance` | Strip a scaffolded project down to a shareable core agent | `extract`, `shareable`, `minimal agent`, `dry-run`, `force overwrite` |
| `upgrade` | `project-maintenance` | Merge a generated project forward to a newer ASP version | `upgrade`, `asp_version`, `3-way merge`, `conflict`, `dry-run` |
| `setup-cicd` | `deployment-ops` | Provision CI/CD and Terraform for a generated project | `setup-cicd`, `staging`, `production`, `GitHub CLI`, `gcloud`, `Terraform`, `Cloud Build`, `GitHub Actions` |
| `register-gemini-enterprise` | `deployment-ops` | Register a deployed agent with Gemini Enterprise | `register-gemini-enterprise`, `Agent Engine`, `agent card`, `Cloud Run`, `GKE`, `deployment_metadata.json` |

## How to route quickly
- If the user is choosing a template or creating a new project, stay in `project-scaffolding`.
- If the user is changing an already-generated project, go to `project-maintenance`.
- If the user is wiring generated output into cloud infrastructure or Gemini Enterprise, go to `deployment-ops`.
- If the user only needs a sanity check that the package is installed, use `scripts/check_agent_starter_pack.py`.

## Common command-level cues
- `local@...` means a local template path.
- `adk@...` means a shortcut into the official ADK samples repository.
- `--auto-approve` removes interactive prompts but does not bypass missing tooling or cloud prerequisites.
- `--skip-checks` skips credential/Vertex checks for creation, not the rest of the workflow.
- `--dry-run` on maintenance commands is for previewing changes, not for generating a project.
