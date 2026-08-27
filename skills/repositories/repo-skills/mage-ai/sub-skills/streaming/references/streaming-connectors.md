# Streaming connectors reference

## Streaming pipeline shape

A streaming pipeline has three logical roles: source, transformer, and sink.

## Supported source families

- ActiveMQ
- Amazon SQS
- Azure Event Hub
- Google Cloud Pub/Sub
- InfluxDB
- Kafka
- NATS
- Kinesis
- RabbitMQ
- MongoDB

## Supported sink families

- ActiveMQ
- Amazon S3
- Azure Data Lake
- BigQuery
- ClickHouse
- Druid
- DuckDB
- Dummy
- Elasticsearch
- Google Cloud Pub/Sub
- Google Cloud Storage
- InfluxDB
- Kafka
- Kinesis
- MongoDB
- Microsoft SQL Server
- MySQL
- OpenSearch
- OracleDB
- PostgreSQL
- RabbitMQ
- Redshift
- Snowflake
- Trino

## Runtime and executor settings

Useful pipeline-level settings for streaming:

- `executor_count`
- `executor_type: k8s`
- source `batch_size`
- `include_metadata`
- checkpoint paths

## Kafka source/sink notes

Kafka source config highlights: `bootstrap_server`, `consumer_group`, `topic` or `topics`, `api_version`, `batch_size`, `include_metadata`, `security_protocol`, `ssl_config`, `sasl_config`, `serde_config`, and `offset`.

Kafka sink config highlights: `bootstrap_server`, `topic`, `api_version`, `security_protocol`, `ssl_config`, `sasl_config`, `batch_size`, and `timeout_ms`.

## CDC and structured streaming notes

The PostgreSQL CDC docs expose a detailed streaming source shape with host, port, database, user, password, replication slot and publication name, optional schema/table filters, start LSN resume support, heartbeat table support, and optional SSL settings.

## Sink-specific patterns

### BigQuery

- Uses the Storage Write API.
- The target table must already exist.
- `profile` comes from `io_config.yaml`.
- `config.table_id` controls the target table.
- `dead_letter` can route failed rows to a file or table.

### OpenSearch

- Needs a host and index name.
- Defaults to AWS auth when `http_auth` is `@awsauth`.

## Safe validation

- Validate the connector type before attempting to create the source or sink.
- Confirm the extra package group `mage-ai[streaming]` is installed.
- Ensure the live broker or service exists before running an actual pipeline.
