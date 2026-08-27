---
name: autogpt
description: "Route AutoGPT Platform self-hosting, backend, frontend, and legacy
  Classic agent work to focused operating guidance."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# AutoGPT

Use this skill for the AutoGPT monorepo. Start by deciding whether the task is
for the current **AutoGPT Platform** or the unsupported **Classic** suite.
Platform is the maintained self-hosted product; Classic is retained for
educational and historical use and has known dependency/security limitations.

## Quick routing

| If the task involves | Read next |
| --- | --- |
| Docker Compose, `.env` setup, local services, self-host upgrade, ports, or local LLM configuration | [platform-stack](sub-skills/platform-stack/SKILL.md) |
| FastAPI routes, graph execution, blocks, integrations, Prisma, model catalog, backend CLI, or Python tests | [platform-backend](sub-skills/platform-backend/SKILL.md) |
| Next.js pages, Builder/Copilot/Library/Marketplace UI, generated API hooks, Tailwind/design system, or frontend tests | [platform-frontend](sub-skills/platform-frontend/SKILL.md) |
| `autogpt`/`serve` CLI, Forge, workspace permissions, or `direct-benchmark` | [classic-agents](sub-skills/classic-agents/SKILL.md) |

For a backend endpoint plus a UI consumer, begin with `platform-backend`, then
use `platform-frontend` for the generated hook and screen work. For local
end-to-end validation, also read `platform-stack` before starting services.

## Operating sequence

1. Confirm the product surface and the smallest affected package.
2. Read the selected sub-skill and its linked references before changing code.
3. Preserve the repository's branch, secret, test, and formatting rules.
4. Choose the narrowest safe validation first; do not start Docker services,
   browser tests, benchmarks, migrations, or credentialed workflows merely to
   inspect them.
5. Escalate to cross-surface validation only when the task actually crosses a
   backend/frontend, API/schema, or runtime boundary.

## Fast orientation

- AutoGPT Platform combines a Python backend, a Next.js frontend, shared Python
  libraries, Docker services, visual agent graphs, blocks, integrations, and a
  marketplace.
- The Platform's standard local stack uses Docker Compose; the backend and
  frontend can also run separately for active development.
- Classic is one Poetry project containing `autogpt`, `forge`, and
  `direct_benchmark`. Treat it as unsupported and avoid presenting it as the
  recommended path for new production work.

Read [repository map](references/repository-map.md) for package boundaries and
common change locations. Read [contributor guidance](references/contributor-guidance.md)
when a task will modify code or documentation. Read
[cross-cutting troubleshooting](references/troubleshooting.md) for setup,
secrets, service, and version failures.

## Public setup anchors

Use the package-specific sub-skills for complete setup. Minimal public commands
are:

```bash
cd autogpt_platform && make init-env && make start-core
cd autogpt_platform/backend && poetry install
cd autogpt_platform/frontend && corepack enable && pnpm install
cd classic && poetry install
```

Run only the commands needed for the chosen surface. Do not combine Platform
backend and Classic dependencies into one Python environment unless a task
explicitly asks for that experiment.

## Safe reusable helper

Run `python scripts/autogpt_repo_probe.py --repo <checkout>` to identify the
major AutoGPT surfaces and missing host tools without starting services or
editing the checkout. Use `--json` when another tool needs structured output.

## Scope limits

This operating graph describes the checked source revision recorded in
[repo provenance](references/repo-provenance.md). It does not provide secrets,
managed-cloud access, external provider credentials, model downloads, or a
promise that Classic dependencies are safe or maintained.
