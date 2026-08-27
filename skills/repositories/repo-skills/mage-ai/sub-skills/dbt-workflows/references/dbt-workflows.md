# dbt workflows reference

## Setup expectations

Mage's dbt docs treat OSS dbt support as Docker-oriented. In practice, the workflow is:

1. Make sure the dbt extra is installed.
2. Add or open a project that contains a `dbt/` directory.
3. Configure the profile target that dbt should use inside Mage.
4. Select the model(s) to run or preview.
5. Run tests when needed.

## Common Mage/dbt block patterns

### Single model

- Choose a specific model file.
- Set the dbt profile target, such as `dev`.
- Mage compiles the selected model and can preview the SQL before execution.

### Selected models with exclusions

- Use a YAML dbt block and keep `--select` and `--exclude` on the same line as `--vars` when you need variables.
- Use the YAML block when you want explicit control over model selection syntax.

### Upstream block output

Mage can interpolate upstream block output into dbt SQL with `block_output(...)`.

Use this when an upstream Mage block decides which city, table, or label to query, which value to inject into the dbt model, or which dynamic path the model should follow.

## Variable interpolation

Mage/dbt workflows can see `var('name')` for Mage runtime or environment variables and `block_output(...)` for upstream Mage block results.

## Testing behavior

- `dbt run` is the execution path used when the pipeline runs.
- `dbt compile` is used for single-model preview.
- `dbt build` is the quickstart path that runs models, tests, snapshots, and seeds together.
- `dbt tests` should be treated as part of the pipeline quality gate when the user asks for validation.

## Supported connector families

The docs and setup guides highlight these dbt adapter families: BigQuery, ClickHouse, Core, Dremio, DuckDB, MySQL, PostgreSQL, Redshift, Snowflake, Spark, SQL Server, Synapse, and Trino.
