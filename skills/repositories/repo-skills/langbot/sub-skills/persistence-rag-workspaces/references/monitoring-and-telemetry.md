# Monitoring and Telemetry

Monitoring routes expose overview, token statistics, messages, LLM/tool and
embedding calls, sessions, errors, exports, and feedback stats. They are
permission-scoped and Workspace-aware.

## Resource Stats

`/healthz` includes runtime resource stats from the `Application`: task manager,
query pool, model manager, runtime registries, message aggregation buffers,
MCP sessions/tasks, blocking executor, event loop, and persistence/database
pool counters.

## Retention and Limits

Config contains retention and limit knobs for completed tasks, log chars,
active user tasks, session history, websocket history, monitoring query limits,
export rows, cleanup batches, and response limits. When changing monitoring or
resource accounting, check both limits and export/security behavior.

## Telemetry Boundary

Telemetry should not leak secrets or tenant data. Cloud/Space telemetry toggles
and monitoring export routes should respect permissions and deployment mode.
Use focused monitoring tenancy tests for changes in this area.
