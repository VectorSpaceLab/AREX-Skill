---
name: open-assistant
description: "Use Open-Assistant repository guidance for backend task APIs, OA
  JSONL data utilities, Next.js contribution/chat UI, and local inference
  services."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Open-Assistant repo skill

Use this repo skill when a task involves the LAION Open-Assistant repository: data-collection backend APIs, shared protocol schemas, OA JSONL exports, the Next.js website/task UI, or the local inference server/worker/chat stack. The upstream project is completed, so prefer targeted maintenance, debugging, local development, and data/inference workflow support over broad product-roadmap changes.

## First decisions

1. **Check staleness**: read [`references/repo-provenance.md`](references/repo-provenance.md) before assuming this skill matches a checkout. If the commit, package versions, service layout, or major evidence paths changed, run `refresh-repo-skill`.
2. **Orient in the repo**: read [`references/setup-and-architecture.md`](references/setup-and-architecture.md) for the selected source scope, Docker profiles, service boundaries, and excluded heavy areas.
3. **Review managed routing**: inspect [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json) when you need the structured scenario metadata that keeps repo-skills-router placement aligned with this skill.
4. **Diagnose shared failures**: read [`references/troubleshooting.md`](references/troubleshooting.md) for cross-cutting Docker, Python, Node, secrets, and boundary-handoff issues.
5. **Run a safe layout check** when a checkout is available:

   ```bash
   python scripts/check_open_assistant_stack.py --repo-root <repo-root>
   ```

## Setup at a glance

Use the smallest stack that matches the task:

- Backend and OA data utilities: `python -m pip install -r backend/requirements.txt` followed by `python -m pip install -e 'oasst-shared[dev]' -e 'oasst-data[dev]'`.
- Website work: from `website/`, run `npm ci` before `npm run lint`, `npm run typecheck`, or Jest/Cypress checks.
- Inference server/worker inspection: `python -m pip install -r inference/server/requirements.txt` for server imports and lightweight route checks. Keep `_lorem` for CPU-only plumbing checks before any real model config.
- Full local stack debugging: use the Docker compose profile that matches the layer you are touching rather than starting every service.

Minimal verification once a checkout is available:

```bash
python scripts/check_open_assistant_stack.py --repo-root <repo-root>
```

## Route by task

| User intent | Go to | Why |
| --- | --- | --- |
| FastAPI backend, task lifecycle, `/api/v1/tasks`, messages/users/stats/text labels, backend settings, DB export/import, shared Python API client, or backend errors | [`sub-skills/backend/SKILL.md`](sub-skills/backend/SKILL.md) | Owns backend API semantics, `oasst_shared` protocol models, `oasst_data`, and safe OA JSONL tooling. |
| OA JSONL files, message trees, flatten/filter/split operations, backend exports, data schema validation | [`sub-skills/backend/SKILL.md`](sub-skills/backend/SKILL.md) | Owns bundled `oasst_jsonl_tool.py` and data-format reference. |
| Next.js website, contribution task pages, label/rank/reply UI, frontend API client, chat UI, Prisma, NextAuth, Jest, Cypress, Storybook, feature flags, or localization | [`sub-skills/website/SKILL.md`](sub-skills/website/SKILL.md) | Owns browser/Next layer, website package scripts, UI route maps, tests, and locale helpers. |
| Inference FastAPI server, websocket workers, text client, `_lorem`/`distilgpt2` smoke paths, model config names, SSE chat events, plugins, safety server, GPU sizing/OOM | [`sub-skills/inference/SKILL.md`](sub-skills/inference/SKILL.md) | Owns inference services, model registry, worker protocol, and generation troubleshooting. |
| Docker profile confusion, local stack selection, service boundaries, or whether a task crosses backend/website/inference | [`references/setup-and-architecture.md`](references/setup-and-architecture.md) | Summarizes profiles, service ownership, and handoff boundaries. |

## Safe bundled scripts

- [`scripts/check_open_assistant_stack.py`](scripts/check_open_assistant_stack.py): read-only repo layout/package/profile checker.
- Backend helper scripts:
  - [`sub-skills/backend/scripts/check_backend_python.py`](sub-skills/backend/scripts/check_backend_python.py)
  - [`sub-skills/backend/scripts/oasst_jsonl_tool.py`](sub-skills/backend/scripts/oasst_jsonl_tool.py)
- Website helper scripts:
  - [`sub-skills/website/scripts/run_frontend_checks.sh`](sub-skills/website/scripts/run_frontend_checks.sh)
  - [`sub-skills/website/scripts/find_missing_locales.py`](sub-skills/website/scripts/find_missing_locales.py)
- Inference helper script:
  - [`sub-skills/inference/scripts/check_inference_config.py`](sub-skills/inference/scripts/check_inference_config.py)

Scripts that accept `--repo-root` are intended for a user's current checkout, not for this skill's original construction checkout.

## Scope boundaries

Included in this generated skill:

- Backend REST API, settings, task lifecycle, DB export/import semantics, shared Python schemas/API client, and `oasst_data` JSONL utilities.
- Website local dev, task UI, chat UI integration, frontend API client behavior, tests, Prisma, feature flags, and localization.
- Inference server/worker/text-client/safety stack, model config registry, worker websocket protocol, SSE events, plugin parsing, and GPU sizing guidance.

Excluded from this generated skill run:

- `model/` training, reward modeling, RLHF, evaluation, pretokenization, and large-model export tools. These require a separate model-training extension because they involve heavy `torch`/DeepSpeed/FlashAttention/model/dataset/GPU dependencies.
- Production deployment, Ansible, infrastructure operations, and credentials-bound systems.
- Exploratory notebooks and historical analysis artifacts.
- Docusaurus docs-site maintenance except where it informs setup boundaries.

## Operating cautions

- Do not start Docker services, download model weights, run GPU workers, call Hugging Face APIs, mutate databases, or run production/infrastructure scripts unless the user explicitly asks and accepts resource, credential, and rollback requirements.
- Keep backend, website, and inference symptoms separate. Report the exact failing layer, command/route, status/body, and environment signals when routing to another sub-skill.
- Use `_lorem` for no-download inference plumbing checks before attempting real model configurations.
- Use safe JSONL file helpers before any DB import/export workflow. Real DB import is mutating unless a dry-run rollback is explicitly selected.
