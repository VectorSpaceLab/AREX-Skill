# Feature Definition Troubleshooting

Start with safe local import/validation before suggesting `feast apply` or retrieval. Use `../scripts/validate_feature_definitions.py` for a definitions file.

## Import and Optional Extra Failures

Symptoms:

- `ModuleNotFoundError: No module named 'feast'`
- `ImportError` for provider modules such as BigQuery, Snowflake, Redis, Kafka, Spark, or Ray
- Definition file import hangs or performs network/backend work

Actions:

- Confirm Feast is installed in the active Python environment: `python -c "import feast; print(feast.__version__)"`.
- Keep definition modules side-effect-light: object construction at import time is OK; `FeatureStore.apply`, `materialize`, retrieval calls, network clients, and server startup should be under `if __name__ == '__main__':` or separate scripts.
- If a provider source import fails, install the relevant Feast extra or route extra/backend selection to `../../integrations-and-extensibility/SKILL.md`.
- If apply/CLI lifecycle is requested after import succeeds, route to `../../feature-repos-and-cli/SKILL.md`.

## Constructor and Type Errors

Common causes:

- Passing positional arguments to keyword-only constructors.
- Using native Python types (`int`, `float`, `str`) instead of Feast types (`Int64`, `Float32`, `String`).
- Using multiple entity join keys.
- Reusing the same source column for `timestamp_field` and `created_timestamp_column`.
- Passing a plain `FileSource` to `StreamFeatureView` instead of a stream source or `PushSource`.

Expected signals:

- `TypeError: ... takes 1 positional argument but ... were given` for keyword-only constructors.
- `ValueError: An entity may only have a single join key` for multiple entity keys.
- `ValueError: Please do not use the same column for 'timestamp_field' and 'created_timestamp_column'.`
- `ValueError: Stream feature views need a stream source...` for invalid stream source type.

Fix pattern:

```python
# Bad: Entity("driver", ["driver_id"])
# Good:
driver = Entity(name="driver", join_keys=["driver_id"], value_type=ValueType.INT64)
```

## Schema and Inference Problems

Symptoms:

- Selected feature projection is missing after inference.
- `SpecifiedFeaturesNotPresentError`, `RegistryInferenceFailure`, or assertion failures during feature service inference.
- Materialization validation reports missing columns or warning-level type mismatch.

Actions:

- Prefer explicit `schema=[Field(...)]` when defining feature views used by feature services.
- Check physical source column names against `Field.name`, entity join key, and timestamp columns.
- Use `field_mapping` only for feature columns that differ between source and Feast names.
- If `enable_validation=True`, expect data-dependent checks during materialization; route execution failures to `../../retrieval-and-materialization/SKILL.md`.

## TTL and Online/Offline Mismatches

Symptoms:

- User expects online freshness but uses `ttl=timedelta(0)` or omits materialization/retrieval workflow.
- Historical joins are too broad or expensive.
- Derived or batch definitions do not write where expected.

Actions:

- Explain that `ttl=timedelta(0)` means values live forever and may make historical queries expensive.
- Set TTL based on maximum acceptable feature staleness for online serving and point-in-time joins.
- Set `online=True` for views intended for online retrieval/materialization.
- Set `offline=True` and `sink_source` only when derived/batch outputs should be written offline.
- Route actual materialization and retrieval verification to `../../retrieval-and-materialization/SKILL.md`.

## Vector Field Mistakes

Symptoms:

- Vector search fails later, vector index not created, or vector store rejects dimensions.
- Definitions compare equal despite vector index/metric drift.

Checks:

- `Field(..., vector_index=True)` should include `vector_length > 0`.
- Vector dtype should be array/list-like, commonly `Array(Float32)`.
- `vector_search_metric` should match the target vector store capability, for example cosine-style metrics when supported.
- Do not rely on `Field.__eq__` to compare `vector_index` or `vector_search_metric`; equality currently ignores those fields but compares `vector_length`.

If the user asks for document retrieval, nearest-neighbor queries, or RAG wiring, route to `../../rag-and-vector-search/SKILL.md` after fixing the definition.

## ODFV Failures

Symptoms and fixes:

- `Either 'sources' or 'input_schema' must be provided`: add `sources=[...]` or `input_schema=[Field(...)]`.
- `Source names must be unique`: rename request sources or avoid duplicate source/projection names.
- `Singleton mode is only supported with mode='python'`: change mode to `python` or set `singleton=False`.
- `OnDemandFeatureView must have a valid feature_transformation`: provide a UDF, `udf_string` plus callable, or `feature_transformation` unless using aggregations.
- `OnDemandFeatureView configured with write_to_online_store=True must have at least one entity`: add entities or use read-time transformation.
- Aggregation column not found in `input_schema`: add the column to `input_schema` or fix the aggregation column name.

Debugging steps:

```python
for obj in [my_odfv]:
    obj.ensure_valid()
    obj.to_proto()
```

## Feature Service Precompute Errors

Symptom:

```text
FeatureService '...' has precompute_online=True but contains OnDemandFeatureView '...' with write_to_online_store=False
```

Fix options:

- Set `precompute_online=False` for the service.
- Change the ODFV to `write_to_online_store=True` only if the transformed values should be produced during ingestion and entities/sources support it.
- Split the service into a low-latency precomputed service and a read-time-transform service.

## Stream and Batch Transformation Errors

Stream definition failures:

- Source must be `KafkaSource`, `PushSource`, or custom source.
- Aggregations require `timestamp_field`.
- Tiling hop size must be smaller than the minimum aggregation window.
- Stream APIs are experimental and may warn at import/construction time outside test mode.

Batch definition failures:

- Missing `sink_source` can be a modeling issue when the expected output is an offline derived dataset.
- Defaults for `online` and `offline` differ by constructor/decorator; set both explicitly to avoid surprises.
- Backend compute engine errors belong to `../../integrations-and-extensibility/SKILL.md` or `../../retrieval-and-materialization/SKILL.md` depending on whether the user is selecting/installing a backend or running materialization.

## Safe Validation Workflow

1. Run `python path/to/validate_feature_definitions.py path/to/features.py`.
2. Fix import errors and constructor exceptions first.
3. Review discovered object names and types to catch accidental missing exports.
4. Fix local validation findings from `ensure_valid`, `validate`, and `to_proto`.
5. Only then route to apply/plan or retrieval/materialization skills.

Expected successful validator output includes lines like:

```text
Imported definitions module: features
Discovered Feast objects: 5
- FeatureView: customer_stats
- FeatureService: risk_v2
No blocking validation errors found.
```

Expected failure output includes `ERROR` lines with object names or an import traceback summary. The script intentionally avoids side-effectful Feast operations.
