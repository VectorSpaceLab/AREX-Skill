# dbt troubleshooting

## Common failures

### dbt support is missing
- Install the dbt extra before trying to use dbt blocks.
- The docs describe dbt support as Docker-oriented for OSS.

### A dbt model will not run
- Check the dbt profile target.
- Confirm the selected model file exists in the copied dbt project.
- Make sure upstream Mage blocks complete successfully before the dbt block runs.

### `block_output(...)` produces invalid SQL
- `block_output(...)` should resolve to a scalar or a SQL-safe string.
- If the upstream block returns structured data, use a `parse=` function to pull out the exact scalar you need.

### `--vars` or YAML selection syntax is malformed
- Keep `--select`, `--exclude`, and `--vars` together on the same line when using a YAML dbt block.
- Use JSON-shaped syntax for the variables object.

### The preview works but the run fails
- Preview uses compiled SQL; a live run uses the dbt execution path.
- Re-check model dependencies, profile credentials, and the selected target.

### External dbt repos are not loading
- Confirm the repo clone path and local project copy exist.
- Recreate the quickstart or re-sync the external repo if the copied project is stale.

### The adapter connector is unsupported
- Verify the selected adapter family is one of the supported dbt connectors listed in the bundled reference.
