# Store, Provider, Compute Engine, and Extra Matrix

Feast resolves integration backends from `feature_store.yaml` through `RepoConfig`. The current verified `RepoConfig` accepts `provider`, `registry`, `online_store`, `offline_store`, `batch_engine`, `openlineage`, `mlflow`, and `data_quality_monitoring`. Default local-style values are `provider: local`, `offline_store: dask`, `online_store: sqlite`, and `batch_engine: local` when not overridden.

## Selection Workflow

1. Identify the task boundary: storage backend, compute engine, import/integration, or extension design.
2. Pick the smallest extra set that unlocks the selected backend. Prefer `feast[extra1,extra2]` over `feast[ci]` or `feast[dev]` for user environments.
3. Draft `feature_store.yaml` with explicit `offline_store.type`, `online_store.type`, and `batch_engine.type` when non-default.
4. Validate without services first: `feast --help`, `feast validate`, `feast plan`, and `python scripts/check_optional_extra.py --extras ...`.
5. Only then run service-backed operations such as `feast apply`, `feast materialize`, or server commands.

## Common Backend Extras

| Need | YAML selector or API area | Minimal Feast extra(s) | Important Python imports checked by helper |
| --- | --- | --- | --- |
| Redis online store | `online_store.type: redis` | `redis` | `redis`, `redis.asyncio` |
| Snowflake offline store | `offline_store.type: snowflake.offline` | `snowflake` | `snowflake.connector` |
| Snowflake online store | `online_store.type: snowflake.online` | `snowflake` | `snowflake.connector` |
| Snowflake compute engine | `batch_engine.type: snowflake.engine` | `snowflake` | `snowflake.connector` |
| BigQuery / Datastore / Bigtable | `offline_store.type: bigquery`, `online_store.type: datastore` or `bigtable` | `gcp` | `google.cloud.bigquery`, `google.cloud.datastore`, `google.cloud.bigtable` |
| Redshift / DynamoDB / Athena | `offline_store.type: redshift` or `athena`, `online_store.type: dynamodb` | `aws` | `boto3`, `aiobotocore` |
| Spark offline or compute | `offline_store.type: spark`, `batch_engine.type: spark.engine` | `spark` | `pyspark` |
| Ray offline or compute | `offline_store.type: ray`, `batch_engine.type: ray.engine` | `ray` | `ray`, `datasets` |
| Flink compute | `batch_engine.type: flink.engine` | `flink` | `pyflink` |
| DuckDB offline | `offline_store.type: duckdb` | `duckdb` | `ibis`, `duckdb` |
| Postgres online/offline | `online_store.type: postgres`, `offline_store.type: postgres` | `postgres` or `postgres-c` | `psycopg` |
| MySQL online | `online_store.type: mysql` | `mysql` | `pymysql` |
| Trino offline | `offline_store.type: trino` | `trino` | `trino`, `regex` |
| ClickHouse offline | `offline_store.type: clickhouse` | `clickhouse` | `clickhouse_connect` |
| Couchbase offline/online | `offline_store.type: couchbase.offline`, `online_store.type: couchbase.online` | `couchbase` | `couchbase` |
| Cassandra online | `online_store.type: cassandra` | `cassandra` | `cassandra` |
| HBase online | `online_store.type: hbase` | `hbase` | `happybase` |
| Hazelcast online | `online_store.type: hazelcast` | `hazelcast` | `hazelcast` |
| Elasticsearch online | `online_store.type: elasticsearch` | `elasticsearch` | `elasticsearch` |
| SingleStore online | `online_store.type: singlestore` | `singlestore` | `singlestoredb` |
| Oracle offline | `offline_store.type: oracle` | `oracle` | `ibis` Oracle backend |
| dbt import | `feast dbt ...` | `dbt` | `dbt_artifacts_parser` |
| MLflow tracking | `mlflow.enabled: true` | `mlflow` | `mlflow` |
| OpenLineage emission | `openlineage.enabled: true` | `openlineage` | `openlineage.client` |
| Great Expectations DQM | `data_quality_monitoring` plus validation-enabled views | `ge` | `great_expectations` |

Vector backends such as FAISS, Milvus, MongoDB, Qdrant, Postgres/pgvector, and SQLite vector belong primarily to `../../rag-and-vector-search/SKILL.md`; use this matrix only to select extras (`faiss`, `milvus`, `mongodb`, `qdrant`, `postgres`, or `sqlite_vec`).

## Store Selectors

### Offline Store Families

- Local/default: `dask`, `file`, `duckdb`.
- Cloud warehouse: `bigquery`, `snowflake.offline`, `redshift`.
- SQL/IBIS/contrib: `postgres`, `trino`, `mssql`, `oracle`, `clickhouse`, `couchbase.offline`.
- Distributed engines as stores: `spark`, `ray`.
- Remote client: `remote` routes offline retrieval to an offline server; for deployment details use `../../servers-and-remote/SKILL.md`.

Minimal local example:

```yaml
project: demo
provider: local
registry: data/registry.db
offline_store:
  type: dask
online_store:
  type: sqlite
  path: data/online_store.db
```

### Online Store Families

- Local/default: `sqlite`.
- Low-latency cache: `redis`, `hazelcast`.
- Cloud managed stores: `dynamodb`, `datastore`, `bigtable`, `snowflake.online`.
- SQL/document/vector-capable stores: `postgres`, `mysql`, `cassandra`, `hbase`, `elasticsearch`, `singlestore`, `couchbase.online`, `mongodb`, `qdrant`, `milvus`.
- Composition/remote: `hybrid`, `remote`.

Redis example:

```yaml
online_store:
  type: redis
  connection_string: localhost:6379,db=0
```

Snowflake offline + Redis online minimal planning example:

```bash
pip install 'feast[snowflake,redis]'
python scripts/check_optional_extra.py --extras snowflake redis
```

```yaml
project: fraud_features
provider: local
registry: data/registry.db
offline_store:
  type: snowflake.offline
  account: ${SNOWFLAKE_ACCOUNT}
  user: ${SNOWFLAKE_USER}
  password: ${SNOWFLAKE_PASSWORD}
  warehouse: FEAST_WH
  database: FEATURE_DB
  schema: PUBLIC
online_store:
  type: redis
  connection_string: redis.internal:6379,db=0,ssl=true
batch_engine:
  type: local
```

Use environment variable expansion or secret injection outside the file where possible; do not hard-code service credentials.

## Compute Engines

`batch_engine` controls materialization computation. Local is default; non-local engines need both YAML and their extra.

| Engine | YAML selector | Extra | Good fit | Key caveats |
| --- | --- | --- | --- | --- |
| Local | `local` | none beyond base install | Local/small materialization | Runs in the client process. |
| Ray | `ray.engine` | `ray` | Parallel materialization and remote Ray clusters | Python version constraints differ; configure remote path/cluster resources before scale-up. |
| Spark | `spark.engine` | `spark` | Spark dataframes and Spark-backed materialization | Requires a working Spark runtime/session. |
| Snowflake | `snowflake.engine` | `snowflake` | Snowflake/Snowpark in-warehouse materialization | Requires warehouse/database/schema and stage setup permissions. It does not own generic historical retrieval. |
| Flink | `flink.engine` | `flink` | Flink DAG execution and streaming-style compute | `flink` extra pins a compatible `pyarrow` range; avoid mixing with environments requiring newer `pyarrow`. |

Examples:

```yaml
batch_engine:
  type: ray.engine
  remote_path: s3://my-bucket/feast/ray-jobs
```

```yaml
batch_engine:
  type: spark.engine
  partitions: 8
```

```yaml
batch_engine:
  type: snowflake.engine
  account: ${SNOWFLAKE_ACCOUNT}
  user: ${SNOWFLAKE_USER}
  password: ${SNOWFLAKE_PASSWORD}
  warehouse: FEAST_WH
  database: FEATURE_DB
  schema: PUBLIC
```

```yaml
batch_engine:
  type: flink.engine
```

## Providers

`provider: local` is the safe default for most explicit store combinations. Cloud provider shortcuts exist historically, but for portable generated guidance prefer explicit `offline_store`, `online_store`, and `batch_engine` sections. A custom provider is appropriate only when a platform needs to own infra lifecycle operations beyond configuring stores; see `extensibility.md`.

## Validation Commands

```bash
feast version
feast validate
feast plan
python scripts/check_optional_extra.py --extras snowflake redis
```

Expected helper output is one line per import group, with `OK` for installed modules or `MISSING` plus a `pip install 'feast[extra]'` suggestion. `feast validate` should fail fast on bad YAML selectors before attempting retrieval or materialization.
