# Self-hosting troubleshooting

## Embedding mismatch

**Symptom:** startup fails because the embedding dimension does not match the
stored schema.

**Likely cause:** the deployment changed `EMBEDDING.VECTOR_DIMENSIONS` or the
physical schema was created with a different value.

**Recovery:**

1. Confirm the configured dimension.
2. Confirm the existing vector column dimensions.
3. Reconcile the deployment before restarting the API or worker.

## Database or schema errors

**Symptom:** the API or worker cannot connect to the database, or startup says
a table or column is missing.

**Likely cause:** missing database, wrong credentials, wrong schema, or an
incomplete migration.

**Recovery:**

- Check the database URI.
- Check the configured schema.
- Confirm migrations ran to completion.

## Redis or queue errors

**Symptom:** cache initialization or queue health checks fail.

**Likely cause:** Redis is unreachable or misconfigured.

**Recovery:**

- Confirm Redis is running and reachable.
- Check any queue or cache host/port values.
- Restart the worker after the backend is healthy.

## Vector-store mode confusion

**Symptom:** the deployment behaves like pgvector when an external store was
expected, or vice versa.

**Likely cause:** the vector-store type is mis-set or the deployment was
configured with a stale environment.

**Recovery:**

- Check `VECTOR_STORE.TYPE`.
- Check whether the deployment is supposed to use the inline store or an
  external store.
- Re-run the read-only runtime helper after changing config.

## Queue lag

**Symptom:** messages are accepted, but the memory view looks stale.

**Likely cause:** background processing is behind, not broken.

**Recovery:**

- Inspect queue status.
- Confirm the worker is alive.
- Wait for the background path to finish before expecting the representation to
  change.

## Secret and key issues

**Symptom:** the deployment starts, but client auth or provider-backed paths
fail later.

**Likely cause:** API key, base URL, or provider secrets are missing.

**Recovery:**

- Re-check the environment variables.
- Re-check the server config that the CLI or SDK consumes.
- Use the CLI `doctor` path or the runtime helper to confirm the values.
