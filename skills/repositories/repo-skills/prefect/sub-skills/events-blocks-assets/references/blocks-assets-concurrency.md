# Blocks Assets Variables And Concurrency

Use this reference for server-backed operational primitives that workflows read or mutate: blocks, variables, assets, materialization metadata, and concurrency limits.

## Blocks

Blocks are typed, server-backed configuration documents. The Python class defines behavior and schema; the Prefect API stores block types, schemas, and block documents. The class itself is not stored in the API, so load a document from the same class or a compatible class in code.

### Core API

`Block.save` and `Block.load` have these shapes in Prefect 3.6.24:

```python
Block.save(self, name: str | None = None, overwrite: bool = False, client=None) -> UUID
Block.load(name: str, validate: bool = True, client=None) -> Block
```

Basic custom block:

```python
from prefect.blocks.core import Block

class WarehouseConfig(Block):
    account: str
    database: str
    schema_name: str = "PUBLIC"

config = WarehouseConfig(account="prod", database="analytics")
config.save("analytics-prod", overwrite=True)

loaded = WarehouseConfig.load("analytics-prod")
assert loaded.database == "analytics"
```

Load forms:

```python
WarehouseConfig.load("analytics-prod")
Block.load("warehouse-config/analytics-prod")
Block.load_from_ref({"block_document_slug": "warehouse-config/analytics-prod"})
```

Operational requirements:

- Saving and loading block documents contact the configured Prefect API or Cloud workspace.
- Saving a custom block document automatically registers the block type/schema if needed; explicit registration is still useful for UI discoverability before any document exists.
- `overwrite=False` protects existing documents; use `overwrite=True` deliberately for rotations or schema migrations.
- `validate=False` lets a newer local class load an older document with missing fields, then set missing fields and save with `overwrite=True`.
- `get_block_placeholder()` requires the instance to have been saved and raises for unsaved blocks.

### Secret Fields And Notification Blocks

For credentials or webhook URLs, prefer Pydantic secret-aware fields or built-in notification/webhook blocks:

```python
from pydantic import SecretStr
from prefect.blocks.core import Block

class ApiCredentials(Block):
    base_url: str
    token: SecretStr
```

Built-in notification and webhook block types include `slack-webhook`, `ms-teams-webhook`, `discord-webhook`, `pager-duty-webhook`, `opsgenie-webhook`, `custom-webhook`, and related notification blocks. Automations refer to notification/webhook block documents by `block_document_id`; they cannot use an unsaved in-memory block object.

### Register Custom Blocks

```bash
prefect block register --module my_package.blocks
prefect block register --file my_block.py
```

Use registration when a block type should appear in the UI before a document is saved, or when updating a block schema. Integration-provided block types may require installing the integration package in the runtime that loads and uses the block.

## Variables

Variables are named mutable JSON values shared across flows and tasks. They are less structured than blocks and do not provide custom behavior or secret-field schema.

Python API:

```python
from prefect.variables import Variable

Variable.set("batch_size", 500, tags=["etl"], overwrite=True)
batch_size = Variable.get("batch_size", default=100)
```

Async variants are `Variable.aset`, `Variable.aget`, and `Variable.aunset`. Server/API requirements are the same as blocks.

CLI:

```bash
prefect variable set batch_size 500 --overwrite --tag etl
prefect variable get batch_size
prefect variable ls --limit 100
prefect variable unset batch_size
```

Use variables for workflow-facing settings that change independently of deployments, such as thresholds, feature flags, table names, or small JSON values. Use parameters for per-run values. Use blocks for credentials, typed config, behavior, and UI-managed reusable documents.

## Assets And Materialization

Assets represent materialized data and lineage. The primary APIs are `Asset`, `AssetProperties`, `materialize`, and `add_asset_metadata`.

```python
from prefect import flow
from prefect.assets import Asset, AssetProperties, add_asset_metadata, materialize

sales_asset = Asset(
    key="s3://warehouse/sales/daily.parquet",
    properties=AssetProperties(
        name="Daily sales",
        description="Curated daily sales dataset",
        owners=["analytics-team"],
        url="https://example.invalid/datasets/sales",
    ),
)

@materialize(sales_asset, asset_deps=["s3://warehouse/raw/orders.parquet"])
def build_sales() -> int:
    rows = 42
    sales_asset.add_metadata({"rows": rows, "quality": "checked"})
    return rows

@flow
def pipeline():
    build_sales()
```

Key facts:

- `Asset(key=...)` requires a valid asset key; string keys are accepted directly by `@materialize` and `asset_deps`.
- `AssetProperties` supports `name`, `url`, `description`, and `owners`; description length is limited.
- `@materialize(*assets, by=None, **task_kwargs)` wraps a function as a materializing Prefect task and accepts normal task options such as `persist_result`, `cache_policy`, and `asset_deps`.
- `materialize` requires at least one asset argument; calling it with no assets raises `TypeError`.
- `Asset.add_metadata()` and `add_asset_metadata()` must run inside a materializing task’s asset context; outside that context they raise a runtime error.
- Asset properties supplied at runtime overwrite existing properties for that asset; include all properties you want to preserve.
- Use string keys when referencing assets produced by another workflow, and full `Asset` objects when defining metadata for an external or authoritative asset.

Asset events include `prefect.asset.referenced`, `prefect.asset.materialization.succeeded`, and `prefect.asset.materialization.failed`. They appear in the event system and can drive automations when a server or Cloud event pipeline is configured.

## Global Concurrency Limits

Global concurrency limits apply to any Python operation and are managed by server-side named limits. They differ from deployment/work-pool/work-queue limits owned by `../deployments-workers/SKILL.md`.

Create and inspect limits:

```bash
prefect global-concurrency-limit create database-pool --limit 5
prefect global-concurrency-limit create api-rate --limit 10 --slot-decay-per-second 1.0
prefect global-concurrency-limit ls --output json
prefect global-concurrency-limit inspect database-pool --output json
prefect global-concurrency-limit disable database-pool
prefect global-concurrency-limit enable database-pool
```

`global-concurrency-limit` has alias `gcl`.

Sync context:

```python
from prefect.concurrency.sync import concurrency, rate_limit

with concurrency("database-pool", occupy=1, timeout_seconds=30, strict=True):
    run_database_query()

rate_limit("api-rate", occupy=1, timeout_seconds=10, strict=True)
```

Async context:

```python
from prefect.concurrency.asyncio import concurrency, rate_limit

async with concurrency(["database-pool", "vendor-api"], occupy=1, strict=True):
    await call_shared_resource()

await rate_limit("api-rate", occupy=1, timeout_seconds=10, strict=True)
```

Public context signature:

```python
concurrency(
    names: str | list[str],
    occupy: int = 1,
    timeout_seconds: float | None = None,
    max_retries: int | None = None,
    lease_duration: float = 300,
    strict: bool = False,
    holder: ConcurrencyLeaseHolder | None = None,
    raise_on_lease_renewal_failure: bool | None = None,
)
```

Behavior to remember:

- The context acquires slots when entering and releases them when exiting.
- `occupy` reserves that many slots from every named limit.
- `timeout_seconds` bounds acquisition wait time; timeouts raise an acquisition timeout error.
- `strict=True` raises if the named limit does not exist; `strict=False` logs a warning and skips acquisition when missing.
- A lease is renewed while the context is active; default lease duration is 300 seconds.
- `raise_on_lease_renewal_failure=None` follows `strict`; set it explicitly for long-running operations that should tolerate or fail on renewal problems.
- `rate_limit` requires the server-side limit to have a non-zero `slot_decay_per_second`.
- Slot acquisition emits `prefect.concurrency-limit.acquired` and release emits `prefect.concurrency-limit.released` when event emission is active.

## Tag-Based Task Concurrency Limits

Older task-tag concurrency limits are managed separately:

```bash
prefect concurrency-limit create database 3
prefect concurrency-limit inspect database --output json
prefect concurrency-limit delete database
```

Use tag limits when throttling Prefect task runs by tag. Use global concurrency limits when throttling arbitrary Python operations or when you need explicit `concurrency()` / `rate_limit()` calls in code.

## Choosing The Primitive

| Need | Prefer | Why |
| --- | --- | --- |
| Stable credentials or typed reusable config | Block | Schema, secret fields, UI document management, custom behavior |
| Small mutable JSON setting | Variable | Lightweight name/value storage and simple CLI/Python access |
| Per-run input | Flow/task parameter | Captured with each run and does not mutate global workspace state |
| Event-driven response | Automation | Server/Cloud evaluates events and runs actions |
| Track data lineage/materialization | Asset | Emits asset/reference/materialization events and metadata |
| Limit shared resource usage | Global concurrency limit | Works around arbitrary code sections with slot leases |
| Limit task runs by tag | Tag concurrency limit | Task-run specific and tag-driven |

## Server And Optional Dependency Requirements

- Blocks, variables, concurrency limits, automations, and event stream operations require a reachable Prefect API or Cloud workspace.
- Some block types appear in the UI but require an integration package in the runtime that loads or uses them, for example cloud-provider or database blocks.
- Notification/webhook blocks require saved block documents before automation actions can reference them.
- Asset materialization is authored in task code; UI visibility, lineage, health, and automations around asset events require server or Cloud event ingestion.
