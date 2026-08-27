# Extensibility Reference

Use this reference when a user wants to add or design a custom Feast provider, offline store, online store, compute engine, data source, or integration adapter. For implementation inside the Feast repository, route test/lint/docs mechanics to `../../repo-development/SKILL.md`; this page focuses on design shape and public extension contracts.

## Extension Decision Tree

- Need a new storage system for historical retrieval or point-in-time joins: implement an `OfflineStore` and a matching config class.
- Need a new low-latency serving backend: implement an `OnlineStore` and matching config class.
- Need platform-controlled infra lifecycle or provider defaults: implement a `Provider` only after deciding store configs are insufficient.
- Need a new materialization execution backend: implement a `ComputeEngine` and config class.
- Need a new source object for tables/files/streams: implement a `DataSource` subclass or reuse existing source classes with a custom store.
- Need data validation behavior: use DQM/profiler APIs first; add lower-level validation only if store-specific schema handling is required.

## Naming and Configuration Contracts

Feast config lookup supports short selectors such as `redis`, `snowflake.offline`, and `ray.engine`. For third-party or private extensions, prefer fully qualified class paths in YAML unless the extension is being added to Feast itself.

The loader convention is important:

- Online store class path must end with `OnlineStore`; config class name is derived as `<ClassName>Config`.
- Offline store class path must end with `OfflineStore`; config class name is derived as `<ClassName>Config`.
- Compute engine class path must end with `Engine`; config class name is derived as `<ClassName>Config`.
- Config classes should inherit Feast's config base model when implemented inside Feast or mimic pydantic-compatible validation when external.

Example private class-path YAML:

```yaml
online_store:
  type: my_company.feast_ext.redis_cluster.RedisClusterOnlineStore
  connection_string: redis-1:6379,redis-2:6379,skip_full_coverage_check=true
```

## Custom Online Store Checklist

A new online store should define:

- `MyOnlineStoreConfig`: pydantic-style config with required service fields and safe defaults.
- `MyOnlineStore`: subclass/implement online store operations for online reads, writes, teardown/update, and optional async support.
- Serialization behavior compatible with Feast entity keys and values.
- Timestamp and feature view version handling that matches Feast online response expectations.
- Clear import errors that name the extra or package to install.
- Unit tests with fake clients before live service tests.
- Documentation snippets for `feature_store.yaml`, credential handling, and skipped live checks.

Design prompt for a future agent:

```text
Design a Feast OnlineStore implementation for <backend>. Include config fields, connection lifecycle, online read/write semantics, table/key layout, feature view version handling, async support choice, idempotent teardown/update behavior, optional dependency import errors, and the smallest tests needed before live integration tests.
```

Minimal YAML for a private store should use a class path until Feast adds a short selector:

```yaml
online_store:
  type: my_package.feast_online.MyOnlineStore
  host: ${MY_STORE_HOST}
  port: 1234
```

## Custom Offline Store Checklist

A new offline store should define:

- `MyOfflineStoreConfig`: connection, warehouse/catalog, staging, and output options.
- `MyOfflineStore`: point-in-time retrieval, feature view schema retrieval, saved dataset behavior where applicable, and write/read helpers when supported.
- Data source compatibility: either reuse existing `DataSource` subclasses or provide a new source with table/query/path fields.
- Timestamp semantics: event timestamp, created timestamp, timezone coercion, and field mapping.
- Efficient entity dataframe handling for both pandas dataframes and SQL strings if supported.
- A `RetrievalJob` implementation that can convert to dataframe/arrow and expose query text where applicable.
- Validation for unsupported modes with explicit errors.

Example private offline store YAML:

```yaml
offline_store:
  type: my_package.feast_offline.MyWarehouseOfflineStore
  account: ${WAREHOUSE_ACCOUNT}
  database: FEATURE_DB
  schema: PUBLIC
```

## Custom Compute Engine Checklist

A compute engine is appropriate when materialization or transformation work needs to run in Ray, Spark, Snowflake, Flink, Kubernetes, Lambda, or a private execution substrate.

A new engine should define:

- `MyEngineConfig`: scheduler/cluster/session/staging fields.
- `MyEngine`: methods for materialization jobs, historical retrieval only if supported, and cleanup.
- Serialization of registry artifacts and feature definitions into the remote execution environment.
- A job object that reports status, errors, and cancellation where the backend supports it.
- Compatibility matrix with offline and online stores, especially whether parallel online writes are safe.
- Failure messages for missing staging locations, bad credentials, unsupported feature view modes, and unavailable clusters.

YAML shape:

```yaml
batch_engine:
  type: my_package.feast_compute.MyEngine
  remote_path: s3://bucket/feast-jobs
  workers: 8
```

## Custom Provider Checklist

A provider owns platform-specific orchestration across registry, stores, and infra lifecycle. Do not introduce one merely to select a store. Prefer explicit store configs unless the platform needs to provision/update/delete cloud resources as a unit.

A provider design should specify:

- How `apply`, `plan`, and deletion map to infrastructure changes.
- Which offline/online stores and registry modes are supported.
- How credentials and projects are isolated.
- Which operations are no-ops vs destructive.
- How local development differs from production.
- Safe dry-run behavior and expected diffs.

## Optional Dependency Pattern

Integrations that import optional libraries should fail with actionable guidance. The common user-facing pattern is:

```text
ImportError or FeastExtrasDependencyImportError: missing package for backend '<extra>'. Install with pip install 'feast[<extra>]'.
```

Use `scripts/check_optional_extra.py --extras <name>` to preflight imports without touching services.

## Extension Acceptance Rubric

A design or implementation is ready when it answers:

- Which Feast config field selects it (`offline_store`, `online_store`, `batch_engine`, `provider`, or integration block)?
- Which package extra and import modules are required?
- What minimal YAML works without hard-coded secrets?
- Which Feast commands validate it before live service operations?
- What are the expected unsupported modes and error messages?
- Which sibling skill owns the next step if the user asks to retrieve, serve, or contribute upstream?
