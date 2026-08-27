# MiroFish overview and setup

## What MiroFish runs

MiroFish is a Flask + Vue application for document-grounded social simulation. It uses:

- A Python backend package named `mirofish-backend` requiring Python `>=3.11,<3.13`.
- Flask and Flask-CORS for `/api/*` endpoints.
- OpenAI-compatible LLM calls for ontology generation, profile/config generation, report planning, and report-agent reasoning.
- Zep Cloud SDK `3.25.0` for graph memory.
- OASIS/CAMEL packages for social-media simulation runtime.
- PyMuPDF plus charset fallback packages for seed document parsing.
- A Vue 3 + Vite frontend using axios, d3, vue-router, and vue-i18n.

The public app workflow is five steps:

1. Graph building.
2. Environment setup.
3. Simulation.
4. Report generation.
5. Deep interaction.

## Source deployment

Prerequisites:

| Tool | Version | Purpose |
| --- | --- | --- |
| Node.js/npm | Node 18+ | root and frontend scripts |
| Python | 3.11 or 3.12 | backend runtime |
| uv | current | backend environment management |

Typical setup:

```bash
cp .env.example .env
# edit .env with real keys
npm run setup:all
npm run dev
```

The root package scripts are:

| Command | Meaning |
| --- | --- |
| `npm run setup` | install root npm packages and frontend npm packages |
| `npm run setup:backend` | run `uv sync` in the backend package |
| `npm run setup:all` | install root/frontend/backend dependencies |
| `npm run backend` | run the Flask backend through `uv run python run.py` |
| `npm run frontend` | start the Vite frontend on host mode |
| `npm run dev` | start backend and frontend together with `concurrently` |
| `npm run build` | build the frontend bundle |

Default local ports:

- Frontend: `3000`.
- Backend: `5001`.

Backend health check:

```bash
curl http://localhost:5001/health
```

Expected response:

```json
{"status": "ok", "service": "MiroFish Backend"}
```

## Docker deployment

Create `.env`, then start:

```bash
docker compose up -d
```

The compose service exposes ports `3000` and `5001`, reads root `.env`, and bind-mounts backend uploads so user-generated artifacts survive container restarts.

The Docker image installs Node.js, npm, uv, root npm dependencies, frontend npm dependencies, and the backend uv lock before copying the full app.

## Required configuration

```env
LLM_API_KEY=...
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL_NAME=qwen-plus
ZEP_API_KEY=...
```

`LLM_BASE_URL` and `LLM_MODEL_NAME` are OpenAI-compatible provider settings. The README recommends Alibaba Bailian/Qwen-plus, but the backend can use any provider with OpenAI SDK-compatible chat completions.

`ZEP_API_KEY` must be a Zep Cloud key. MiroFish does not support self-hosted Zep endpoint overrides and reports `ZEP_API_URL` as a configuration error.

Optional acceleration settings should be omitted entirely when unused:

```env
LLM_BOOST_API_KEY=...
LLM_BOOST_BASE_URL=...
LLM_BOOST_MODEL_NAME=...
```

## Backend runtime knobs

| Variable | Default | Purpose |
| --- | --- | --- |
| `FLASK_HOST` | `0.0.0.0` | backend bind host |
| `FLASK_PORT` | `5001` | backend port |
| `FLASK_DEBUG` | `False` | Flask debug/reloader mode |
| `OASIS_DEFAULT_MAX_ROUNDS` | `10` | simulation default round count |
| `REPORT_AGENT_MAX_TOOL_CALLS` | `5` | report-agent tool-call cap |
| `REPORT_AGENT_MAX_REFLECTION_ROUNDS` | `2` | report-agent reflection cap |
| `REPORT_AGENT_TEMPERATURE` | `0.5` | report-agent model temperature |

## Quick sanity checks

Use root script:

```bash
python scripts/mirofish_config_check.py --env-file .env
python scripts/mirofish_config_check.py --base-url http://localhost:5001
```

Then follow sub-skill-specific smoke paths:

- `graph-build`: validate ontology payload shape before custom ontology edits.
- `simulation-setup`: validate Twitter/Reddit profile file formats.
- `simulation-run`: verify action-log JSONL helper behavior.
- `reporting`: summarize report log directories without starting a service.
