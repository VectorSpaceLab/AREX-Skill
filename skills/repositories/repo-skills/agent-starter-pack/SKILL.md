---
name: agent-starter-pack
description: "Routes Agent Starter Pack tasks to the right workflow for
  creating, maintaining, and deploying generated agent projects."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Agent Starter Pack

Use this repo skill for the `agent-starter-pack` Python package and CLI. It helps future agents choose templates, generate projects, maintain generated output, and wire projects into deployment and Gemini Enterprise workflows.

## First check
If you only need to confirm that the package is installed and importable, use the bundled helper first:

```bash
python scripts/check_agent_starter_pack.py
```

For a quick command discovery check, also run:

```bash
agent-starter-pack --help
```

## Route map

| User intent | Go here |
| --- | --- |
| Create a new project, compare templates, or parse a remote template | `sub-skills/project-scaffolding/SKILL.md` |
| Enhance, extract, or upgrade an existing generated project | `sub-skills/project-maintenance/SKILL.md` |
| Set up CI/CD, deploy a generated project, inspect observability, configure data ingestion, or register with Gemini Enterprise | `sub-skills/deployment-ops/SKILL.md` |

## Read these shared references
- `references/package-overview.md` for package identity, install guidance, and the command family map.
- `references/cli-reference.md` for the command-to-subskill mapping.
- `references/template-catalog.md` for the built-in agent/template list.
- `references/troubleshooting.md` for cross-cutting install, import, and CLI issues.
- `references/repo-provenance.md` for the source snapshot used to build this skill.

## How to navigate
1. Identify whether the user is starting from a blank slate or an existing project.
2. Decide whether the question is about template selection, project maintenance, or cloud deployment.
3. Read the owning sub-skill’s workflow reference before giving command details.
4. If the user asks about a cloud prerequisite or generated Makefile target, switch to deployment-ops instead of staying in the root router.

## What this skill is not
- It is not a runtime agent framework.
- It is not a source-repo maintenance guide for the ASP checkout itself.
- It does not import or execute the generated skill here.

## Safety notes
- Generated projects can vary by language, deployment target, and template family.
- Remote templates and cloud setup may require network or credentials; do not treat those as default-safe checks.
- Do not assume the same commands exist in every generated project; use the template catalog and generated-project references to confirm.
