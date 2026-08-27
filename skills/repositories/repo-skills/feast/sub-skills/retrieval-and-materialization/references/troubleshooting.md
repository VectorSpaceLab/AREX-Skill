# Retrieval and Materialization Troubleshooting

## Install and import failures

Signals:

- `ModuleNotFoundError: No module named 'feast'`
- `feast: command not found`
- Optional dependency import errors for a cloud store, tensor conversion, or file format.

Actions:

```bash
python -c "import feast; print(feast.__version__)"
feast version
feast --help
```

If the package imports but a backend plugin fails, install the appropriate optional extra or choose a local file/SQLite workflow for validation. Keep backend selection and extras decisions in `../../integrations-and-extensibility/SKILL.md`.

## Feature repo and config failures

Signals:

- `feature_store.yaml` cannot be found.
- Registry path is missing or stale.
- `FeatureStore(repo_path=...)` points at a different repo than the CLI command.
- `get_online_features` fails after a registry cache refresh because the registry file moved or was deleted.

Actions:

```bash
pwd
ls feature_store.yaml
feast --help
feast plan
feast apply
```

Use the same repo path for `FeatureStore(repo_path="...")`, `feast --chdir ...`, and any materialization command. Route repo setup and registry lifecycle fixes to `../../feature-repos-and-cli/SKILL.md`.

## Historical retrieval nulls or wrong joins

Common causes:

- `entity_df` is missing `event_timestamp`.
- Entity join-key names do not match feature-view entity join keys.
- Feature rows are after the entity timestamp and correctly excluded.
- Feature rows are before the TTL window and correctly excluded.
- Source timestamp column is missing or configured incorrectly.
- The feature ref points to a different feature view or version than expected.

Checks:

```python
print(entity_df.columns)
print(entity_df[["driver_id", "event_timestamp"]].head())
print(training_df.columns)
print(training_df.isna().mean().sort_values(ascending=False).head())
```

For a tiny assertion-backed case, create two feature rows around one entity timestamp and assert Feast selects the latest feature row at or before that timestamp, not a future row.

## Online retrieval nulls

Common causes:

- Materialization was skipped.
- Materialization used a time window that did not include the source rows.
- Materialization wrote to a different online store path or service than retrieval reads.
- Feature view has `online=False`.
- Join-key values differ by name or type.
- Requested feature service uses precomputed vectors that were not built or are stale.
- Push ingestion wrote to a different push source or mode.

Checks:

```bash
feast materialize 2025-01-01T00:00:00 2025-01-02T00:00:00
feast materialize-incremental 2025-01-03T00:00:00
```

```python
online = store.get_online_features(
    features=["driver_hourly_stats:conv_rate"],
    entity_rows=[{"driver_id": 1001}],
).to_dict()
print(online)
```

Expected diagnostic pattern: output contains requested feature keys but values are null-like for missing online rows. If required join keys are absent, Feast raises a key error that names missing and provided join keys.

## Materialization failures

Common causes:

- Offline source file or table is missing.
- Offline source lacks a required join key column.
- Offline source lacks the configured event timestamp column.
- Backend credentials are absent or invalid.
- Optional store dependency is not installed.
- The date range is malformed or outside source data.

A local Feast E2E test verifies a failure mode where materialization fails when the Parquet source does not include the expected join key, raising a Feast join-key materialization error.

Actions:

```bash
feast materialize --help
feast materialize 2025-01-01T00:00:00 2025-01-02T00:00:00
```

For Python calls, use `datetime` objects and confirm timezone handling matches the source data.

## CLI/API misuse

Signals and fixes:

- Passing `start_date`/`end_date` together with `entity_df`: choose entity-dataframe retrieval or supported entity-less retrieval, not both.
- Passing a list of feature refs where a `FeatureService` object was intended: retrieve it with `store.get_feature_service("name")`.
- Using server endpoint patterns for SDK calls: route endpoint-specific work to `../../servers-and-remote/SKILL.md`.
- Using vector document APIs for normal features: route vector/RAG work to `../../rag-and-vector-search/SKILL.md`.

## Backend and credential failures

Signals:

- Cloud SDK credential errors.
- SQL connection failures.
- Missing service hosts or ports.
- Permission errors during offline scans or online writes.

Actions:

- Reproduce with a local file + SQLite repo when possible.
- Confirm optional extras and backend client packages are installed.
- Check `feature_store.yaml` points to the intended offline and online stores.
- Avoid broad service-backed tests unless credentials and safe test resources are explicitly available.

## DQM and monitoring failures

Signals:

- `feast validate` or `feast monitor` command errors.
- Validation reference or saved dataset not found.
- Unexpected null-rate, range, or freshness checks after retrieval.

Actions:

```bash
feast validate --help
feast monitor --help
feast saved-datasets --help
```

Start with retrieval-level assertions: row count, feature columns present, timestamp range, TTL behavior, and null-rate thresholds. Then debug validation-reference or monitoring configuration separately.

## Troubleshooting online nulls after skipped materialization

Use this sequence for the difficult case where historical retrieval works but online retrieval returns nulls:

1. Run historical retrieval for one entity and timestamp to prove the source data exists.
2. Inspect `feature_store.yaml` for online-store type/path.
3. Run `feast materialize <start> <end>` covering the source row timestamp.
4. Retrieve the same entity online.
5. If still null, confirm the feature view has `online=True`, the join-key type matches, and the same repo/config is used.
6. If using a feature service with `precompute_online=True`, rerun materialization or push for the affected entities and check for precomputed-vector errors.
