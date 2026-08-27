# Headroom TypeScript SDK

Use this reference when the task is about the `headroom-ai` npm package rather than the Python CLI or proxy operations.

## Package facts

- Package name: `headroom-ai`
- Node engine: `>=18.0.0`
- Main exports come from `sdk/typescript/src/index.ts`.
- The SDK is an HTTP client and does not require the repo checkout at runtime.

## Core exports

### Compression and client

- `compress(messages, options)`
- `HeadroomClient`
- `simulate(...)`

### Format and conversion helpers

- `detectFormat`
- `toOpenAI`
- `fromOpenAI`
- `deepCamelCase`, `deepSnakeCase`, `snakeToCamel`, `camelToSnake`
- `parseSSE`, `collectStream`

### Hooks and shared context

- `CompressionHooks`
- `extractUserQuery`
- `countTurns`
- `extractToolCalls`
- `SharedContext`

### Filesystem path helpers

The TS SDK mirrors the Python `headroom.paths` contract for future local features. It exports helpers for config/workspace roots, savings ledgers, log paths, memory DB, plugins, deployments, and related state locations.

## Common recipes

### Basic compression

```typescript
import { compress } from "headroom-ai";

const result = await compress(messages, { model: "gpt-4o" });
console.log(result.tokensSaved);
```

### SharedContext

```typescript
import { SharedContext } from "headroom-ai";

const ctx = new SharedContext({ model: "gpt-4o", ttl: 3600, maxEntries: 100 });
await ctx.put("research", "large text block", { agent: "researcher" });
console.log(ctx.get("research"));
```

### CCR retrieval

```typescript
const result = await client.compress(messages, { model: "gpt-4o" });
for (const hash of result.ccrHashes) {
  const original = await client.retrieve(hash);
  console.log(original.originalTokens);
}
```

### Framework integrations

The repository examples cover:

- Vercel AI SDK middleware and streaming
- OpenAI and Anthropic adapters
- Tool-calling agents
- Simulation/dry-run flows
- Basic compression and shared-context handoffs

## When to use this reference

Read this file when you need to:

- explain the `headroom-ai` npm install path,
- route a user to the correct TS example,
- map a TypeScript error back to the SDK exports,
- or confirm that a task should use the TS SDK instead of the Python CLI/proxy.
