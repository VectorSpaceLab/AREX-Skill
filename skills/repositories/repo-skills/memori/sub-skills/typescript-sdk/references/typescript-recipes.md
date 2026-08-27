# TypeScript Recipes

## Quick start

```bash
npm install @memorilabs/memori
```

## Provider and driver reminders

- The package expects Node `>=20.19.0`.
- Peer dependencies are optional for some providers, but the relevant driver or
  SDK must still be installed when the chosen recipe uses it.
- Cloud mode needs the Memori API key environment variable.
- BYODB mode needs a connection factory and a supported dialect.

## Common recipes

| Recipe | Shape | Notes |
| --- | --- | --- |
| Cloud | `new Memori()` + `memori.llm.register(openaiClient)` | set `MEMORI_API_KEY` |
| SQLite | `new Memori({ conn: () => db, dialect: 'sqlite' })` | call `storage.build()` once |
| PostgreSQL | `new Memori({ conn: () => pool, dialect: 'postgresql' })` | install `pg` |
| MySQL | `new Memori({ conn: () => connection, dialect: 'mysql' })` | install `mysql2` |
| CockroachDB | `new Memori({ conn: () => pool, dialect: 'cockroachdb' })` | install `pg` and the Cockroach-compatible path |

## Short server pattern

```ts
const memori = new Memori({ conn: () => pool, dialect: 'postgresql' });
await memori.config.storage!.build();

app.post('/chat', async (req, res) => {
  const scope = memori.forRequest({
    entityId: req.user.id,
    processId: 'api',
    sessionId: req.body.sessionId,
  });
  scope.llm.register(openai);
  res.json(await scope.recall(req.body.query));
});
```

## Practical rule

Keep the request-scoped view at the edge of the web handler and keep the shared
Memori instance at application startup.
