---
name: mirofish
description: "Use MiroFish's Flask and Vue social-simulation engine to build Zep
  graphs from documents, prepare OASIS simulations, run them, and generate
  interactive reports."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# MiroFish

Use this repo skill when a task names MiroFish or asks for a document-to-graph-to-social-simulation workflow with Zep Cloud graph memory, OASIS/CAMEL agents, Twitter/Reddit-style simulations, generated prediction reports, or report-agent interaction.

MiroFish is a full-stack app, not a small library call. The normal operating sequence is:

1. Build a Zep graph from seed PDFs, Markdown, or text.
2. Prepare simulation artifacts from graph entities.
3. Run and monitor a parallel/Twitter/Reddit OASIS simulation.
4. Generate a report and interact with the Report Agent.

## Route by task

- Use [sub-skills/graph-build/SKILL.md](sub-skills/graph-build/SKILL.md) for seed-file upload, ontology generation, Zep graph build, graph data inspection, project/task state, graph reset, and graph deletion.
- Use [sub-skills/simulation-setup/SKILL.md](sub-skills/simulation-setup/SKILL.md) for simulation creation, entity filtering, profile/persona generation, `simulation_config.json`, setup status, setup downloads, and setup-format validation.
- Use [sub-skills/simulation-run/SKILL.md](sub-skills/simulation-run/SKILL.md) for start/stop/close-env, run status, timelines, actions, posts, comments, agent stats, interviews, IPC, and graph-memory updater finalization.
- Use [sub-skills/reporting/SKILL.md](sub-skills/reporting/SKILL.md) for report generation, progress/section/log polling, download/delete, Report Agent chat, and report-side graph tools.

## Read or run the root material

- Read [references/overview-and-setup.md](references/overview-and-setup.md) before installing, starting, containerizing, or configuring a MiroFish deployment.
- Read [references/architecture-and-state.md](references/architecture-and-state.md) to understand the backend services, frontend steps, local artifact directories, state transitions, and handoffs between sub-skills.
- Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import, API key, port, provider, Zep Cloud, Docker, and frontend/backend issues.
- Read [references/repo-provenance.md](references/repo-provenance.md) to see the source revision and evidence baseline used to build this skill.
- Read [references/repo-routing-metadata.json](references/repo-routing-metadata.json) only when updating managed repo-skill router metadata.
- Run `python scripts/mirofish_config_check.py --help` to inspect the bundled environment and service-health checker; run it with `--env-file .env` or `--base-url http://localhost:5001` from a deployment workspace.

## Minimal deployment check

```bash
cp .env.example .env
# fill LLM_API_KEY and ZEP_API_KEY
npm run setup:all
npm run dev
```

Expected local service URLs:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:5001`
- Health check: `GET /health` returns `{"status":"ok","service":"MiroFish Backend"}`

For Docker deployment, create `.env` first and then run `docker compose up -d`; the image exposes the same frontend/backend ports and persists backend uploads under the bind-mounted upload directory.

## Configuration essentials

Required:

- `LLM_API_KEY`: OpenAI-compatible LLM provider key.
- `ZEP_API_KEY`: Zep Cloud key.

Common optional settings:

- `LLM_BASE_URL` and `LLM_MODEL_NAME`: default to OpenAI-compatible behavior when omitted.
- `LLM_BOOST_*`: optional faster model for selected expensive paths; omit the variables entirely when unused.
- `FLASK_HOST`, `FLASK_PORT`, `FLASK_DEBUG`: backend server behavior.
- `OASIS_DEFAULT_MAX_ROUNDS`: default runtime round count.
- `REPORT_AGENT_MAX_TOOL_CALLS`, `REPORT_AGENT_MAX_REFLECTION_ROUNDS`, `REPORT_AGENT_TEMPERATURE`: Report Agent limits.

Do not set `ZEP_API_URL`; MiroFish intentionally supports Zep Cloud only and rejects self-hosted Zep URL overrides.

## Operating guardrails

- Keep live Zep Cloud validation manual. Credentialed graph validation can create/delete cloud graphs and is not part of normal skill smoke checks.
- Treat GPU availability as optional for this skill. The selected automated verification scope is CPU-only because MiroFish's public workflows are service/API orchestration, not required CUDA kernels.
- Do not run long OASIS launchers as casual smoke tests. Use setup checks and short unit/native candidates first; start simulations only when the user explicitly wants runtime execution.
- Do not edit generated report or simulation artifact files while the backend is running unless the referenced sub-skill says the artifact is safe to inspect or regenerate.
