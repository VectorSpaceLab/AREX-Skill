---
name: bindu
description: "Operate the Bindu agent microservice framework: Python bindufy
  agents, A2A protocol, security, gRPC SDKs, deployment, Gateway, and Inbox."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Bindu Repo Skill

Use this skill when a task is about building, running, integrating, or troubleshooting Bindu: a Python-first framework that turns AI handlers into DID-identified A2A-speaking microservices, with optional Hydra auth, DID signatures, mTLS, x402 payments, gRPC language SDKs, boxd runtime deployment, a Gateway planner, and an operator Inbox UI.

## Start with a safe install check

Install the public package in the target environment when needed:

```bash
python -m pip install bindu
```

When a user is working with an installed Bindu package, first confirm the package and CLI surface without starting a server:

```bash
python scripts/check_bindu_install.py --json
```

If the user is editing a Bindu checkout, run project-native commands only after reading the relevant sub-skill and respecting repo maintenance rules in `references/repo-maintenance.md`.

## Route by task

| User intent | Read |
|---|---|
| Write a Python agent, call `bindufy()`, validate config/handler shape, send A2A JSON-RPC, poll tasks, expose public skills, or interpret negotiation | `sub-skills/agent-authoring-and-a2a/SKILL.md` |
| Configure or debug Hydra OAuth, DID keys/signatures, private skill catalogs, mTLS, x402 payments, payment sessions, or auth/payment errors | `sub-skills/security-identity-and-payments/SKILL.md` |
| Register TypeScript or other language agents, debug core `:3774`, callback gRPC, proto drift, generated stubs, or SDK heartbeat/handler responses | `sub-skills/grpc-and-language-sdks/SKILL.md` |
| Use `bindu serve`, `bindu deploy`, runtime-boxd, source packaging, secret exclusion, storage/scheduler, migrations, observability, tunneling, or maintainer commands | `sub-skills/deployment-runtime-and-operations/SKILL.md` |
| Operate Bindu Gateway `/plan`, recipes, peer catalogs/auth, send-and-poll orchestration, Inbox UI, personal agent, contacts, demo peers, or webhooks | `sub-skills/gateway-inbox-and-orchestration/SKILL.md` |

## Root references

- `references/capability-map.md` maps Bindu features to sub-skills, bundled references, and verification evidence.
- `references/troubleshooting.md` covers cross-cutting install/import, generated-code, port, optional-service, and routing problems.
- `references/repo-maintenance.md` summarizes repository contribution rules, native commands, and generated-code boundaries.
- `references/repo-provenance.md` records the source snapshot and evidence paths used to create this skill.
- `references/repo-routing-metadata.json` is structured router metadata for managed repo-skill import tooling.

## Root helper

- `scripts/check_bindu_install.py` verifies the installed distribution, important imports, CLI entry point, and optional environment signals. It does not start servers, contact networks, read secrets, or require the original repository checkout.

## Safety boundaries

- Do not hand-edit generated gRPC stubs. Edit `proto/agent_handler.proto` in a checkout and regenerate with the documented commands.
- Do not commit `.env`, key, wallet, cert, or token files. Use `.env.example` with allowlist pragmas only when the repo's secret scanner requires it.
- Do not run live Hydra, x402 chain, boxd cloud, OpenRouter, Postgres, Redis, or step-ca workflows unless the user has provided credentials/services and explicitly wants those side effects.
- Prefer dry-run, help, import, and tiny-fixture checks before long-running servers or deployment.
- Use `app_settings` for Bindu config and `get_logger(__name__)` for logging when editing the repository.
