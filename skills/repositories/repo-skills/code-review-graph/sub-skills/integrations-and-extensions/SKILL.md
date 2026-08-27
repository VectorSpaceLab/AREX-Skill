---
name: integrations-and-extensions
description: "Handle code-review-graph custom languages, embeddings, wiki,
  registry, daemon, GitHub Action, and eval workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Integrations and Extensions

Use this sub-skill for advanced or optional workflows: custom parser languages, semantic embeddings, wiki generation, multi-repo registry and daemon support, GitHub Action integration, and evaluation/benchmark guidance.

## Start here

1. Confirm the requested feature is truly optional or integration-focused.
2. Read the narrow reference for the exact surface.
3. Install only the extra needed for that surface, not `all` by default.

Read [references/custom-languages.md](references/custom-languages.md) for `.code-review-graph/languages.toml` workflows. Read [references/embeddings.md](references/embeddings.md) for semantic-search and provider behavior. Read [references/registry-and-daemon.md](references/registry-and-daemon.md) for multi-repo registry, watch daemon, and repo listing. Read [references/github-action.md](references/github-action.md) for PR review automation. Read [references/eval.md](references/eval.md) for benchmark/reproduction guidance. Read [references/troubleshooting.md](references/troubleshooting.md) when an optional dependency, provider, grammar, daemon state, or eval run fails.

## Route by task

| User task | Do this |
| --- | --- |
| "Add a custom language" | Edit `.code-review-graph/languages.toml` and rebuild the graph. |
| "Enable semantic search" | Install the embeddings extra, then run the embedding workflow. |
| "Generate wiki pages" | Use the wiki generation workflow after communities exist. |
| "Register multiple repos" | Use the registry/daemon commands. |
| "Run a PR review in CI" | Use the GitHub Action pattern and the bundled PR renderer. |
| "Reproduce benchmarks" | Follow the eval reference and be prepared for expensive, repo-clone-heavy work. |

## Optional dependency policy

Only install an optional extra when the task requires it:

- `code-review-graph[embeddings]` for local sentence-transformers embeddings.
- `code-review-graph[google-embeddings]` for Google Gemini embeddings.
- `code-review-graph[communities]` for igraph-based community detection.
- `code-review-graph[wiki]` for Ollama-backed wiki summaries.
- `code-review-graph[eval]` for benchmark and report helpers.
- `code-review-graph[enrichment]` for deeper Python call-resolution enrichment.

Do not install `all` unless the user explicitly wants every optional feature in one environment.

## Safe starting points

- Custom language users should start with a small `.code-review-graph/languages.toml` and a rebuild.
- Embedding users should confirm provider/environment variables before enabling cloud providers.
- Registry/daemon users should ensure each registered repository has a valid graph or watchable checkout.
- GitHub Action users should prefer the split analysis/comment workflow for fork safety.

## Boundaries

- For installation and server setup, use `install-and-setup`.
- For diff review and PR comments, use `review-changes`.
- For structural exploration, search, and refactor previews, use `graph-exploration`.

## Verification anchors

Native tests that ground this route include custom-language tests, embeddings tests, registry and daemon tests, wiki tests, eval tests, and PR workflow security tests. Some of these are optional or service-backed; record unverified optional capabilities explicitly instead of implying full support.