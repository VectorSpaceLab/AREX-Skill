# TypeScript Workflows

## Install And Build

```bash
npm install @memmachine/client
```

For source/development work in a checkout with the package sources, common
package scripts include:

```bash
npm install
npm run build
npm run test
npm run lint
npm run format:check
npm run docs
```

The source baseline requires Node `>=20.19.0`.

## Health Check

```ts
import MemMachineClient from '@memmachine/client'

const client = new MemMachineClient({
  base_url: process.env.MEMMACHINE_BASE_URL ?? 'https://api.memmachine.ai/v2',
  api_key: process.env.MEMMACHINE_API_KEY
})

console.log(await client.healthCheck())
```

Use a health check before live memory operations. For self-hosted servers,
confirm whether the base URL should end in `/api/v2` or another prefix.

## Add/Search/List/Delete

```ts
const project = client.project({ org_id: 'my-org', project_id: 'my-project' })
const memory = project.memory({ user_id: 'alice', agent_id: 'assistant', session_id: 'demo' })

const added = await memory.add('Alice prefers aisle seats.', {
  metadata: { category: 'travel' },
  types: ['episodic', 'semantic']
})

const search = await memory.search('What seating does Alice prefer?', {
  top_k: 5,
  filter: "metadata.category = 'travel'",
  expand_context: 0,
  agent_mode: false
})

const listed = await memory.list({ page_size: 10, page_num: 0, type: 'episodic' })
await memory.delete('episode-id', 'episodic')
```

Ask before delete calls. Use non-sensitive test content for smoke tests.

## Python To TypeScript Translation

| Python SDK | TypeScript client |
| --- | --- |
| `MemMachineClient(base_url=..., api_key=...)` | `new MemMachineClient({ base_url, api_key })` |
| `client.get_or_create_project(...)` | TS source baseline primarily exposes `client.project(context)` and project methods; create/get operations may be REST-level or version-specific. |
| `project.memory(metadata={...})` | `project.memory({ ...memoryContext })` |
| `memory.add(content, metadata={...})` | `memory.add(content, { metadata })` |
| `memory.search(query, limit=5)` | `memory.search(query, { top_k: 5 })` |
| `memory.list(memory_type=MemoryType.Episodic)` | `memory.list({ type: 'episodic' })` |
| `memory.delete_episodic(id)` | `memory.delete(id, 'episodic')` |

Check the installed TypeScript package version before relying on methods not
covered by the published type declarations.

## Safe Recipe Script

From this sub-skill directory:

```bash
node scripts/ts_client_recipe.mjs --print
node scripts/ts_client_recipe.mjs --live-health --base-url "https://api.memmachine.ai/v2"
```

`--print` is default and does not contact a server. `--live-health` contacts the
configured endpoint only.
