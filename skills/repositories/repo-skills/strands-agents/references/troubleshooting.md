# Cross-cutting troubleshooting

Use this reference for problems that span packages or are caused by environment, dependency, credential, browser, network, or infrastructure boundaries.

## Choose the right owner first

| Symptom | Likely route |
| --- | --- |
| Python import, provider extra, tool schema, MCP client, memory, session, sandbox, or pytest issue | `sub-skills/python-sdk/` |
| TypeScript export, npm workspace, peer dependency, browser bundle, package tarball, or Vitest issue | `sub-skills/typescript-sdk/` |
| MDX, snippets, frontmatter, sourceLinks, generated API docs, navigation, or site build issue | `sub-skills/docs-site/` |
| `strands-agents-mcp-server`, `search_docs`, `fetch_doc`, docs catalog/cache/sectioning issue | `sub-skills/mcp-server/` |
| API naming parity, public/internal boundary, logging, comments, or contribution process issue | `references/cross-sdk-parity-and-contribution.md` |

## Install and dependency failures

- Confirm the package owner before installing dependencies. Do not install all extras or all dev dependencies unless the selected workflow needs them.
- Python SDK base imports require the base package dependencies; provider modules may require extras such as `anthropic`, `openai`, `gemini`, `ollama`, `litellm`, `sagemaker`, `a2a`, `bidi`, or `cedar`.
- TypeScript and docs-site checks require npm dependencies. If `node_modules` is absent, either install the package/workspace dependencies intentionally or record Node checks as not run.
- Keep generated API output, build directories, caches, and verification artifacts out of runtime reasoning unless the task is specifically about them.

## Credentials, provider services, and network

- Default unit and smoke checks should avoid credentials, network, and long-lived services.
- Provider-backed Python or TypeScript integration tests require explicit API credentials and may need provider-specific extras.
- MCP server live-doc integration tests require network access to `strandsagents.com`; offline unit tests should run first.
- If credentials are missing, do not invent a pass. Record the skipped provider or network surface and the exact condition needed to verify it later.

## Browser, Docker, and AWS infrastructure

- Browser examples and browser test projects require Playwright/Chromium or a browser runtime. Keep them optional unless the task is browser-specific.
- Telemetry examples may require Docker or local tracing services. Do not run them as part of ordinary package validation.
- `test-infra/` provisions real AWS resources for a small subset of integration tests. Do not deploy it unless the task explicitly targets infrastructure or SSM-backed integration tests.
- Never set broad internal AWS test-infra flags outside the Strands team's internal account.

## Stale skill or checkout mismatch

Read `repo-provenance.md` when behavior differs from this skill. Refresh or repair the skill when any of these change materially:

- public exports, package entry points, or optional extras;
- Python or TypeScript source layout and subsystem names;
- docs authoring rules, frontmatter schema, snippet syntax, sourceLinks behavior, or API-generation scripts;
- MCP server tool return shapes, URL policy, cache/indexing behavior, or environment variables;
- test commands, supported runtimes, Node/Python floors, or infrastructure policy.

## Safe recovery pattern

1. Identify the owning sub-skill and read its troubleshooting reference.
2. Run the smallest smoke helper that does not require credentials, network, browser, Docker, or AWS.
3. Inspect the exact failing package metadata and command output.
4. Add only the dependency, extra, environment variable, or test fixture required by the selected workflow.
5. Re-run the focused check and record any remaining optional surfaces that were not exercised.
