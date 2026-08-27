# Streaming troubleshooting

## Common failures

### The source or sink tries to connect to a live service during tests
- The base source class calls `test_connection()` unless the environment is treated as test.
- Set `ENV=test` when you want the repo's streaming tests or local smoke checks to avoid live connection attempts.
- If you're writing a unit test, patch the connection check or the client constructor explicitly.

### Kafka source construction fails with missing topic or topics
- Provide either `topic` or `topics` in the source config.
- If you supply `offset`, also provide the partition list it expects.

### Kafka security settings fail
- Match `security_protocol` with the right credential block.
- `SSL` requires `ssl_config`.
- `SASL_SSL` and `SASL_PLAINTEXT` require `sasl_config`.
- For OAuth, make sure the OAuth token URL, client id, and client secret are all present.

### Kafka source or sink tests raise consumer or initialization errors
- A patched `init_client` may prevent the source from creating the consumer before connection testing.
- Patch the connection test too, or run under `ENV=test` so the live connection check is skipped.

### BigQuery writes fail
- The target table must already exist.
- Check that the `profile` points to the right `io_config.yaml` section.
- Confirm `table_id` and any required `overwrite_types` are correct.

### OpenSearch writes fail
- Verify the host URL and index name.
- If AWS auth is used, confirm the environment has valid AWS credentials and region information.

### CDC pipelines do not resume correctly
- Confirm replication slot, publication name, and optional `start_lsn` values.
- If using heartbeat settings, make sure the heartbeat table exists or can be created.

### The pipeline never consumes records
- Check the source `batch_size`, topic/stream name, and broker address.
- Make sure you are using the streaming route rather than the batch integration route.
