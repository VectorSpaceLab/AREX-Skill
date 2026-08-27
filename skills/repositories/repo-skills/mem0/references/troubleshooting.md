# Mem0 Cross-cutting Troubleshooting

Use this reference when a Mem0 task spans SDKs, CLI, services, plugins, or configuration and the immediate owner is unclear.

## Wrong Surface Selected

| Symptom | Likely correction |
| --- | --- |
| User asks for Python/TypeScript app code but answer uses shell commands | Route to `sub-skills/sdk-memory/SKILL.md`. |
| User asks for `mem0 add/search` terminal behavior but answer uses SDK snippets | Route to `sub-skills/cli-memory/SKILL.md`. |
| User asks for vector store/LLM/embedder config and answer only shows CRUD | Route to `sub-skills/provider-configuration/SKILL.md`. |
| User asks about Docker dashboard/API keys/MCP hosting and answer uses hosted Platform client | Route to `sub-skills/self-hosted-openmemory/SKILL.md`. |
| User asks about Vercel AI SDK or editor plugin config and answer uses generic SDK | Route to `sub-skills/integrations-plugins/SKILL.md`. |

## Install and Import Failures

- Python SDK: install `mem0ai`, import from `mem0`.
- Python CLI: install `mem0-cli`, run `mem0`.
- TypeScript SDK: install `mem0ai`, import hosted client from `mem0ai` and OSS `Memory` from `mem0ai/oss`.
- Node CLI: install `@mem0/cli`, run `mem0`.
- Vercel provider: install `@mem0/vercel-ai-provider` with compatible AI SDK packages.

If imports fail after installation, check the active Python/Node environment first. Multiple packages share the public word “mem0,” so verify distribution/package name and import path separately.

## API Keys and Secrets

- Hosted Platform SDK/CLI/plugin calls need a Mem0 API key.
- OSS local `Memory()` may need provider keys such as OpenAI/Anthropic/Gemini depending on configured LLM/embedder.
- Self-hosted server needs deployment secrets such as `JWT_SECRET`, database password, provider keys, and generated API keys.
- Never print raw keys. Redact values in diagnostics and prefer environment variables or secret managers.

## Memory Scope Problems

Common empty-search causes:

- Add and search used different `user_id`, `agent_id`, `run_id`, app, or project scope.
- Search used top-level entity kwargs where the current SDK expects `filters`.
- Add is asynchronous on the target surface and search happened too soon.
- `threshold`, `top_k`, categories, metadata filters, or graph flags are too restrictive.
- Hosted Platform and self-hosted/OpenMemory base URLs or auth modes were mixed.

## Destructive Operations

Confirm before:

- `delete_all`, entity cascade delete, or global memory deletion.
- `reset` on OSS memory stores.
- Self-hosted volume wipes, backup restores, admin password resets, or request-log pruning.
- Hook installers or plugin commands that rewrite agent/editor config.

## Safe Diagnostic Order

1. Identify surface: SDK, provider config, CLI, self-hosted/OpenMemory, or integration/plugin.
2. Verify installed package name, import path, runtime version, and environment.
3. Check API/provider keys are present without printing them.
4. Confirm memory scope and filters.
5. Run bundled read-only validators or `--help` commands.
6. Run live add/search only in a safe non-production scope after approval.
