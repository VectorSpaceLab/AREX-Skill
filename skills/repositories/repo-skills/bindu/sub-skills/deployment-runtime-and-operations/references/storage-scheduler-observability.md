# Storage, Scheduler, and Observability

## Storage

- Memory storage: development, tests, single-process agents; data lost on stop.
- Postgres storage: persistence, multi-pod/distributed services, long-term tasks. The implementation uses SQLAlchemy async and can scope schemas by DID.

Legacy rows with `owner_did IS NULL` may need a dry-run owner backfill before strict ownership enforcement:

```bash
python scripts/backfill_owner_did.py --owner-did did:bindu:legacy --dry-run
```

## Scheduler

- Memory scheduler: in-process queue for local work.
- Redis scheduler: distributed queue for production/multi-worker. It backs off on Redis receive errors to avoid tight-loop CPU burn.

## Observability

Bindu supports OpenTelemetry SDK/exporters, FastAPI/httpx instrumentation, optional OpenInference auto-instrumentation for detected agent/LLM frameworks, Sentry, health, and metrics. For OTLP endpoints, verify the expected path for the vendor; Langfuse-style endpoints often require a specific `/api/public/otel/v1/traces` path.
