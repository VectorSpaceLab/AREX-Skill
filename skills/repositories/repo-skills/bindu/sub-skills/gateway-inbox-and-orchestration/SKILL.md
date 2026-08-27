---
name: gateway-inbox-and-orchestration
description: "Operate Bindu Gateway, recipes, peer auth, A2A planning, Inbox
  personal agents, contacts, demo peers, and webhooks."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Gateway, Inbox, and Orchestration

Use this sub-skill for Bindu Gateway `/plan`, multi-agent peer catalogs, recipes, stateless history/compaction, peer auth, send-and-poll behavior, Inbox UI, personal agents, contacts, demo peers, and webhooks.

## References and helper

- `references/gateway-workflows.md` — `/plan` request shape, peer catalog, stateless sessions, health, SSE, and send-and-poll.
- `references/inbox-workflows.md` — UI/API ports, personal-agent lifecycle, contacts, compose, demo peers, and webhooks.
- `references/recipes-and-auth.md` — recipe layout/frontmatter/permissions and peer auth modes.
- `references/troubleshooting.md` — Gateway/Inbox/auth/deadline/personal-agent failures.
- `scripts/make_gateway_plan_request.py` — emit a safe `/plan` JSON skeleton without secrets or network calls.

## Key facts

- Gateway is stateless per `/plan` request. The caller owns durable history and sends `history` plus `prior_summary` on the next call.
- Gateway inbound auth (`GATEWAY_API_KEY`) is separate from peer auth (`agents[].auth`).
- Recipes are lazy-loaded playbooks: only name/description are visible until `load_recipe` is used.
- Inbox dev UI uses port `3775`; API uses `3787`; personal/demo-agent flows may require OpenRouter and Hydra.
