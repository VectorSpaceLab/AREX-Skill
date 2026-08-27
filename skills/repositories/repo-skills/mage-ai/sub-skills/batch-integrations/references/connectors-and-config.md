# Batch integration connectors and config

## High-level workflow

A batch data integration pipeline usually has one source block, one or more stream/config blocks that describe what to sync, one destination block, and a trigger to run the sync.

The pipeline uses a shared `io_config.yaml` file at the project root for credentials and connection settings.

## Config loading

Common loaders and helpers:

- `ConfigFileLoader(repo_path/io_config.yaml, profile)`
- `EnvironmentVariableLoader()`
- `get_repo_path()` to find the active project root when building block templates

Interpolation is supported in integration config, schema config, and destination config.

| Syntax | Meaning |
| --- | --- |
| `{{ env_var('NAME') }}` | Read from environment variables |
| `{{ variables('name') }}` | Read from pipeline/runtime variables |
| `{{ mage_secret_var('secret') }}` | Read from Mage secrets |

## Connector families

The repo's source and destination registries include many connectors. Group them mentally by workflow rather than by package path.

### SQL-oriented source families

- BigQuery
- Doris
- Microsoft SQL Server
- MySQL
- OracleDB
- PostgreSQL
- Redshift
- Snowflake

### Common non-SQL source families

- Airtable
- Amazon S3
- Amplitude
- API
- Azure Blob Storage
- Chargebee
- Commercetools
- Couchbase
- Datadog
- Dremio
- DynamoDB
- Facebook Ads
- Freshdesk
- Front
- GitHub
- Google Ads
- Google Analytics
- Google Cloud Storage
- Google Search Console
- Google Sheets
- HubSpot
- Intercom
- Knowi
- LinkedIn Ads
- Monday
- MongoDB
- Mode
- Outreach
- Paystack
- Pipedrive
- Postmark
- PowerBI
- Salesforce
- SFTP
- Stripe
- Tableau
- Teradata
- Twitter Ads
- Zendesk

### Common destinations

- Amazon S3
- BigQuery
- ClickHouse
- Delta Lake on Azure or S3
- Doris
- Elasticsearch
- Google Cloud Storage
- Kafka
- MongoDB
- Microsoft SQL Server
- MySQL
- OpenSearch
- OracleDB
- PostgreSQL
- Redshift
- Salesforce
- Snowflake
- Teradata
- Trino

## Schema and stream configuration knobs

Data integration streams usually need you to decide which fields are selected, which fields are unique, which fields are bookmark fields, which fields are replicated incrementally or as a full table, how duplicate records are handled, and whether the stream should be processed in parallel.

## Common table-prefix pattern

To prefix destination tables, use the `_patterns.destination_table` field in the source config. The prefix can interpolate the current stream name through `variables('stream')`.

## Validation expectations

- The project root should contain `io_config.yaml`.
- The selected profile should exist in that file.
- The source and destination types should be supported by the configured connector family.
- Any credentials referenced through env vars or secrets should be present before the pipeline is run.
