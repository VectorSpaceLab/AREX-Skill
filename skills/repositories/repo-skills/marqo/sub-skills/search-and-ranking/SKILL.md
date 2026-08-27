---
name: search-and-ranking
description: "Marqo tensor, lexical, hybrid, recommend, filters, ranking
  controls, score modifiers, facets, collapse, recency, sort, and
  relevance-cutoff workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Search and Ranking

Use this sub-skill for Marqo query construction, ranking knobs, filters, facets, collapse, recency, sort, relevance cutoff, weak-and / second-phase behavior, recommend payloads, and safe request builders.

## Route elsewhere

- Public HTTP route wiring, auth, and response mapping → `../documents-and-api/`
- Index schema, field types, and collapse-field configuration → `../index-and-vespa/`
- Vectorisation, model loading, and `/vectorise` internals → `../inference-and-models/`

## Open first

1. `references/search-recipes.md`
2. `references/ranking-parameters.md`
3. `references/filter-and-modifier-reference.md`
4. `references/troubleshooting.md`
5. `scripts/search_payload_examples.py`

## Operating rules

- Start from the smallest valid payload, then add one ranking feature at a time.
- Prefer camelCase payload examples because they match the public request shape.
- Keep examples offline; the bundled script prints JSON only and does not call Marqo or Vespa.
- When a request mixes search, recommend, or filter logic, use the bundled references before trying to improvise a payload.

## What this sub-skill owns

- Tensor, lexical, hybrid, multimodal, and custom-vector search payloads
- Recommendation payloads built from document ids and interpolation
- Search filters, score modifiers, boost handling, and custom score rerank keys
- Search ranking controls: `alpha`, `rrfK`, rerank depth, weak-and, second phase, recency, sort, collapse, facets, and relevance cutoff
- Failure recovery when a payload is valid JSON but invalid for the chosen search method
