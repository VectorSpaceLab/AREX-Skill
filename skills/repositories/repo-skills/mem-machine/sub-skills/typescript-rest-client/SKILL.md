---
name: typescript-rest-client
description: "Use the @memmachine/client TypeScript REST client for
  Node/TypeScript project and memory operations, client defaults, API errors,
  build/test workflows, and self-hosted/cloud base URL troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TypeScript REST Client

Use this sub-skill when a task names `@memmachine/client`, TypeScript/Node,
`MemMachineClient`, `MemMachineProject`, `MemMachineMemory`, Axios errors,
Jest tests, npm build/lint/format, or a TypeScript app that adds/searches
MemMachine memories.

## Route Within This Sub-skill

- Read [typescript-client-reference.md](references/typescript-client-reference.md)
  for classes, methods, constructor options, defaults, and option names.
- Read [workflows.md](references/workflows.md) for install, project/memory
  operations, live/self-hosted base URL selection, build/test, and Python-to-TS
  translation patterns.
- Read [troubleshooting.md](references/troubleshooting.md) for Node/npm, ESM/CJS,
  proxy, Axios/API, base URL, auth, and option-name failures.
- Run [ts_client_recipe.mjs](scripts/ts_client_recipe.mjs) to print a safe
  TypeScript recipe or optionally run a live health check when explicit live
  arguments are supplied.

## Quick Pattern

```ts
import MemMachineClient from '@memmachine/client'

const client = new MemMachineClient({
  base_url: 'https://api.memmachine.ai/v2',
  api_key: process.env.MEMMACHINE_API_KEY
})

const project = client.project({ org_id: 'my-org', project_id: 'my-project' })
const memory = project.memory({ user_id: 'alice', agent_id: 'assistant' })
await memory.add('Alice prefers aisle seats.', {
  metadata: { category: 'travel' },
  types: ['episodic', 'semantic']
})
const result = await memory.search('What seating does Alice prefer?', { top_k: 5 })
```

## Important Defaults

- Package: `@memmachine/client`.
- Node engine in the source baseline: `>=20.19.0`.
- Constructor default `base_url`: `https://api.memmachine.ai/v2`.
- Constructor default `timeout`: `60000` ms.
- Constructor default `max_retries`: `3`.
- Proxy environment variables can make the client choose a fetch adapter.

For a self-hosted server, confirm the correct REST prefix. A self-hosted FastAPI
server commonly exposes `/api/v2`, while the TS client's cloud default ends in
`/v2`. Set `base_url` to the exact prefix that makes `/health` and
`/memories/search` resolve correctly.

## Cross-links

- Use [python-sdk-and-cli](../python-sdk-and-cli/SKILL.md) for Python SDK/CLI
  equivalents and shared memory/filter concepts.
- Use [server-configuration-and-memory-engines](../server-configuration-and-memory-engines/SKILL.md)
  for self-hosted server setup, REST/MCP, storage, and provider resources.
- Use [integrations-and-migration](../integrations-and-migration/SKILL.md) for
  OpenClaw/no-code/platform integrations and migration workflows.
