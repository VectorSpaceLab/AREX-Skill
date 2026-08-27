# TypeScript API Reference

## Main classes

### `Memori`

```ts
new Memori({
  conn?: ConnFactory,
  embeddingModel?: string,
  dialect?: 'sqlite' | 'postgresql' | 'cockroachdb' | 'mysql',
})
```

Use `conn` to enable BYODB storage. Omit it for cloud-only usage.

### `MemoriRequestScope`

A per-request wrapper returned by `memori.forRequest(options)`.
It carries its own `entityId`, `processId`, and session while sharing the
parent engine and storage manager.

## Important methods

| Method | Purpose |
| --- | --- |
| `memori.attribution(entityId, processId?)` | Set the attribution context on the shared instance |
| `memori.recall(query)` | Fetch relevant memories |
| `memori.resetSession()` | Start a new session |
| `memori.setSession(id)` | Resume a session |
| `memori.forRequest(options)` | Create a request-scoped view for concurrent servers |
| `memori.llm.register(client)` | Register a direct LLM client for hooks |
| `memori.augmentation.wait(timeoutMs?)` | Wait for queued augmentation work to settle |
| `memori.config.storage.build()` | Run storage migrations when a connection is configured |
| `scope.llm.register(client)` | Register a client on a request-scoped view |
| `scope.recall(query)` | Recall memories from a request scope |
| `scope.integrate(IntegrationClass)` | Attach a supported integration wrapper |

## Request-scope rule

Use `forRequest({ entityId, processId, sessionId })` in web servers and other
concurrent apps so identities do not bleed across requests.

## Storage rule

If you created a `Memori({ conn: ... })` instance, call
`await memori.config.storage!.build()` during startup before the first request.
