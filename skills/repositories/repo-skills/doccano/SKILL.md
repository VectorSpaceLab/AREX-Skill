---
name: doccano
description: "Operate doccano for text annotation, dataset import/export,
  auto-labeling, deployment, and repo maintenance."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# doccano

doccano is a text annotation platform with a Django backend, a Nuxt frontend, and CLI/deployment entry points for local, Docker, and cloud use.

Use this skill when a task mentions doccano itself, project/label/member workflows, dataset import or export, auto-labeling, deployment, or repository maintenance for this checkout.

## How to route

| Route | Read when |
| --- | --- |
| `sub-skills/setup-and-deploy/` | You need install, initialize, run, package, Docker, or cloud deployment guidance. |
| `sub-skills/project-annotation/` | You need project creation, label setup, members, comments, annotation, cloning, or metrics. |
| `sub-skills/data-transfer/` | You need dataset import/export formats, validation, encodings, or format-specific troubleshooting. |
| `sub-skills/auto-labeling/` | You need template selection, request testing, response mapping, label mapping, or auto-labeling activation. |

## Start here

- New users usually start with `sub-skills/setup-and-deploy/SKILL.md`.
- If the request is about the running app, route to the workflow sub-skill that matches the task family first, then read the shared references listed below.
- If the request is about editing the source checkout, package build, or tests, keep `python-repository-maintenance` in mind and start with `sub-skills/setup-and-deploy/SKILL.md` for the build/runtime entry points.

## Safe minimal check

Use the installed package and CLI before deeper work:

```bash
pip install doccano
python -I -c "import backend; import backend.cli; print(backend.__file__)"
doccano --help
```

If the package was already installed, `python -m pip check` is a useful follow-up health check.

## Shared references

- Read `references/overview.md` for the repo map and major surfaces.
- Read `references/task-types.md` when you need the supported project types or their annotation shapes.
- Read `references/cli-reference.md` for the command list and environment variables.
- Read `references/troubleshooting.md` for cross-cutting install, runtime, and validation failures.
- Read `references/repo-provenance.md` before deciding whether the skill is stale.
- Read `references/repo-routing-metadata.json` when you need the routing contract consumed by repo-skills-router.
- Use `scripts/cli-smoke.sh` for a fast install-and-CLI sanity check.

## Working rules

- Keep runtime guidance self-contained inside this skill tree.
- Do not point future agents back to the original checkout for commands that can be bundled here.
- Prefer the nearest sub-skill for workflow details and keep this router short.
- Use the repo-maintenance scenario only for source edits, tests, packaging, or contributor workflows.
