---
name: retrieval-and-materialization
description: "Use for Feast offline/historical retrieval, online retrieval,
  point-in-time joins, materialization, push ingestion, saved datasets, local
  retrieval checks, and DQM/monitoring basics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Feast Retrieval and Materialization

Use this sub-skill when the user asks to retrieve training data, batch-score features, fetch online features for inference, materialize feature views into an online store, push streaming rows, save historical datasets, or diagnose null/stale retrieval results.

## Route first

- Use this skill for `FeatureStore.get_historical_features`, `get_online_features`, `materialize`, `materialize_incremental`, `push`, entity rows, feature refs, `FeatureService` retrieval, local file offline stores, and SQLite online stores.
- Route feature object modeling, `Entity`, `FeatureView`, `FeatureService`, `PushSource`, and field schema questions to `../feature-definitions/SKILL.md`.
- Route feature repo initialization, `feature_store.yaml`, `feast apply`, `feast plan`, registry paths, and CLI repo lifecycle to `../feature-repos-and-cli/SKILL.md`.
- Route feature server, offline server, registry server, REST/gRPC, TLS, auth, and remote serving endpoints to `../servers-and-remote/SKILL.md`.
- Route vector document retrieval, `retrieve_online_documents`, vector stores, and RAG retrievers to `../rag-and-vector-search/SKILL.md`.

## Fast workflow

1. Confirm the feature repo is applied and the registry is readable.
2. For historical retrieval, build an entity dataframe with join keys and `event_timestamp`, or use supported entity-less `start_date`/`end_date` retrieval.
3. Select features with either a `FeatureService` or feature refs such as `driver_hourly_stats:conv_rate`.
4. For online retrieval, materialize the needed feature views first, then call `get_online_features(...).to_dict()` or `.to_df()`.
5. If results are null, stale, or missing columns, check join keys, timestamp windows, TTL, materialization range, online-store config, and feature-view `online=True` settings.

## References

- `references/api-reference.md` for SDK and CLI retrieval/materialization calls.
- `references/workflows.md` for historical, online, push, saved dataset, and DQM flows.
- `references/data-formats.md` for entity rows, entity dataframes, feature refs, outputs, and local stores.
- `references/troubleshooting.md` for common failures and validation signals.
- `scripts/local_retrieval_smoke.py` for a safe local repo checker and command planner.
