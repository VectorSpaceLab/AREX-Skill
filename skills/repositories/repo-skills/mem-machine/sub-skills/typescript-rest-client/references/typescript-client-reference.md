# TypeScript Client Reference

The TypeScript REST client is published as `@memmachine/client`. It wraps Axios
and exports client, project, memory, and API error classes/types.

## Imports

```ts
import MemMachineClient, {
  MemMachineClient as NamedClient,
  MemMachineAPIError
} from '@memmachine/client'
```

The package builds CommonJS and ESM outputs. Use the import style supported by
your Node/TypeScript configuration.

## Client Options

```ts
const client = new MemMachineClient({
  base_url: 'https://api.memmachine.ai/v2',
  api_key: process.env.MEMMACHINE_API_KEY,
  timeout: 60000,
  max_retries: 3
})
```

Defaults in the source baseline:

| Option | Default | Meaning |
| --- | --- | --- |
| `base_url` | `https://api.memmachine.ai/v2` | API prefix used by Axios. Override for self-hosted servers. |
| `api_key` | unset | Adds `Authorization: Bearer <key>` when provided. |
| `timeout` | `60000` | Request timeout in milliseconds. |
| `max_retries` | `3` | Retry count for network/idempotent and 429/5xx failures. |
| `adapter` | proxy-aware auto choice | If proxy env vars are set, the source baseline may choose Axios fetch adapter. |

## MemMachineClient Methods

```ts
client.project({ org_id: 'org', project_id: 'project' })
client.getProjects()
client.getMetrics()
client.healthCheck()
```

`getProjects`, `getMetrics`, and `healthCheck` throw `MemMachineAPIError` on
API failures after error normalization.

## Project And Memory

```ts
const project = client.project({ org_id: 'my-org', project_id: 'my-project' })
const memory = project.memory({ user_id: 'alice', agent_id: 'assistant' })
```

Project context is separate from memory context. Keep both explicit to avoid
cross-user/session leakage.

## Memory Methods

```ts
await memory.add('Alice prefers aisle seats.', {
  producer: 'user',
  role: 'user',
  produced_for: 'assistant',
  episode_type: 'message',
  metadata: { category: 'travel' },
  types: ['episodic', 'semantic']
})

const result = await memory.search('travel preferences', {
  top_k: 5,
  filter: "metadata.category = 'travel'",
  expand_context: 1,
  score_threshold: 0.2,
  agent_mode: false,
  types: ['episodic', 'semantic']
})

const page = await memory.list({
  page_size: 20,
  page_num: 0,
  filter: "metadata.category = 'travel'",
  type: 'episodic'
})

await memory.delete('episode-id', 'episodic')
```

`memory.getContext()` returns the combined project and memory context.

## Error Type

`MemMachineAPIError` is thrown for normalized API/client errors. Catch it around
live calls:

```ts
try {
  await memory.search('travel preferences')
} catch (err) {
  if (err instanceof MemMachineAPIError) {
    console.error(err.message)
  }
  throw err
}
```

Do not log request payloads containing secrets or private memory content unless
redacted.
