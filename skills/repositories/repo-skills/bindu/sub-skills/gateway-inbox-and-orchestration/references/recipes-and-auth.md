# Recipes and Auth

## Recipes

Recipes are Markdown playbooks with frontmatter:

```yaml
---
name: multi-agent-research
description: When a task should be decomposed across multiple peers.
tags: [research]
triggers: [multi-agent]
---
```

Layouts can be flat (`recipes/foo.md`) or bundled (`recipes/foo/RECIPE.md` plus sibling scripts/reference files). Recipe names must be unique and should not start with `call_`. The planner sees metadata first and loads full bodies only through `load_recipe`.

## Peer auth modes

| Mode | Meaning |
|---|---|
| `none` | No outbound auth headers. |
| `bearer` | Literal bearer configured in catalog; avoid logging it. |
| `bearer_env` | Bearer token read from Gateway environment variable. |
| `did_signed` | Gateway signs A2A body with its DID and supplies OAuth bearer through auto Hydra provider or `tokenEnvVar`. |

Gateway inbound `GATEWAY_API_KEY` is separate from peer auth.
