# Batch integration troubleshooting

## Common failures

### The docs or UI say data integrations are unsupported
- Data integrations are documented as Docker-oriented because of connector dependencies.
- If the task is not Docker-based, steer the user toward a simpler batch pipeline or a connector that is already installed.

### `io_config.yaml` is missing or a profile cannot be found
- The file belongs in the project root.
- Check that the profile name used by the block matches a top-level key in the file.
- Use `scripts/inspect_io_config.py` to confirm profile names and key presence without exposing secrets.

### Interpolated values do not resolve
- Verify the environment variable or Mage secret exists before the pipeline runs.
- Check that the interpolation syntax matches the target context: `env_var`, `variables`, or `mage_secret_var`.

### Credentials work locally but fail inside Docker
- Mount credential files as a volume.
- For local host databases reached from a Docker container, use `host.docker.internal`.

### `InvalidToken` or S3 auth errors
- An invalid `AWS_SESSION_TOKEN` entry in `io_config.yaml` can break S3 access.
- Remove the session token entry if the environment does not need it.

### A connector is not supported by the current flow
- Confirm whether the task is a batch integration or a streaming pipeline.
- Batch data integration routes should not be used for real-time source/sink flows.

### Stream/table prefixes are wrong
- Revisit `_patterns.destination_table` and the `variables('stream')` interpolation.
- Confirm the destination table override is applied in the source config, not in the destination config.

### The sync runs but nothing is written
- Check the selected stream list.
- Confirm the source catalog contains streams and the destination table/schema values are valid.
- Validate unique fields, bookmark fields, and replication method before rerunning.
