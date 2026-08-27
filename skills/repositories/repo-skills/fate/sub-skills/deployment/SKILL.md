---
name: deployment
description: "Install and deploy FATE through the documented PyPI, standalone
  Docker, Docker Compose, and host-package flows; explain service-backed
  startup, status, and smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Deployment

Use this sub-skill when the task is to bring FATE up, verify that its services are reachable, or choose a supported installation path.

## Covers
- PyPI install with or without the FATE-Flow service.
- Standalone Docker deployment.
- Host-package deployment.
- Docker Compose / all-in-one deployment.
- Basic port and process checks.
- High-level startup and status troubleshooting for `fate_flow`, `pipeline`, Docker, SSH, and the service wrappers referenced by the docs.

## Boundaries
- Safe by default: inspect, document, and verify.
- Do not run remote rollout commands, container teardown, or root OS mutation by default.
- Treat documented service-wrapper, host-mutation, Docker, and cluster rollout scripts as reference-only evidence; use the bundled deployment references and preflight helper instead of assuming a source checkout path exists.
- For service-free local module execution, use `../local-launchers/SKILL.md`.
- For training/predict recipes after deployment, use `../pipeline-workflows/SKILL.md`.
- For component CLI and task-schema work, use `../component-runtime/SKILL.md`.

## Start here
1. Read `references/deployment-guide.md` for install paths and the command matrix.
2. Read `references/cli-reference.md` for `fate_flow`, `pipeline`, `python -m fate.components`, and smoke checks.
3. Read `references/troubleshooting.md` when ports, Docker, SSH, or service startup fail.
4. Run `scripts/deployment_preflight.py` before choosing a path.

## Related links
- Root troubleshooting: `../../references/troubleshooting.md`
- Pipeline workflows: `../pipeline-workflows/SKILL.md`
- Component runtime: `../component-runtime/SKILL.md`
- Local launchers: `../local-launchers/SKILL.md`
