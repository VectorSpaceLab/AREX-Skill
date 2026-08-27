# Asset Definitions Troubleshooting

Use this guide for Dagster asset, job, `Definitions`, partition, asset check, selection, and local materialization failures.

## Install or Import Fails

Symptoms:

- `ModuleNotFoundError: No module named 'dagster'`
- Public APIs such as `Definitions`, `asset`, or `define_asset_job` are unavailable.
- Importing a user module runs external work or credential checks.

Actions:

1. Confirm the active environment can run `python -c "import dagster as dg; print(dg.__version__)"`.
2. Keep examples on public `dagster` APIs, not private `dagster._core` imports, unless diagnosing Dagster internals.
3. If optional integrations are missing, keep this sub-skill focused on pure Dagster definitions and route integration-specific setup elsewhere.
4. Move network calls, database clients, and file discovery out of module import time and into asset functions or resources.

## Definitions Does Not Load

Common causes:

- The module does not expose a `dg.Definitions` object.
- Assets are defined but not included in `Definitions(assets=[...])`.
- An unresolved asset job is not included with the assets it selects.
- Import-time side effects raise before Dagster can load the module.

Fix pattern:

```python
import dagster as dg

@dg.asset
def my_asset() -> int:
    return 1

my_job = dg.define_asset_job("my_job", selection="*")
defs = dg.Definitions(assets=[my_asset], jobs=[my_job])
```

Validate by importing the module and calling `defs.resolve_all_asset_specs()` or `defs.resolve_job_def("my_job")`.

## Missing Dependency or Invalid Asset Key

Symptoms:

- A downstream asset input has no matching upstream asset.
- Selection by key finds no assets.
- A multi-asset subset fails or requires unexpected inputs.

Actions:

1. Compare Python parameter names to upstream asset keys.
2. Use `dg.AssetIn(key=...)` when names intentionally differ.
3. Use `deps=[...]` for dependencies that should not be passed as arguments.
4. Use `dg.AssetKey(["prefix", "name"])` for multi-component keys, not slash-delimited strings unless the existing project already uses string selection syntax.
5. For `@dg.multi_asset`, verify `outs`, `internal_asset_deps`, and `can_subset` match the intended subset behavior.

## Asset Job Resolution Confusion

Symptoms:

- `get_job_def` warns or does not return the expected asset job.
- A job from `define_asset_job` appears unresolved.

Explanation and fix:

- `dg.define_asset_job` returns an unresolved asset job until it is attached to `Definitions` with the relevant assets.
- Prefer `defs.resolve_job_def("job_name")` for asset jobs.
- Use direct `@dg.job` only for op graphs that do not rely on asset selection.

## Selection Matches Too Much or Too Little

Actions:

1. Start with `dg.AssetSelection.keys("asset_name")` for exact keys.
2. Use `dg.AssetSelection.groups("group_name")` only when assets are assigned the expected `group_name`.
3. Compose selections with `|`, `&`, and `-`; keep expressions simple enough to explain.
4. Resolve the job through `Definitions` to catch selection errors before handing off to CLI or deployment flows.
5. Remember that asset checks may be selected with or alongside assets depending on the job/check setup.

## Materialize or Unit Test Fails

Symptoms:

- `materialize_to_memory` fails because an asset expects a custom IO manager.
- Asset code needs resources, config, or optional packages.
- The test materializes an asset without its upstream dependencies.

Actions:

1. Use `materialize_to_memory` only for pure assets that can use in-memory IO.
2. Use `materialize(..., resources={...})` when resources are required.
3. Include upstream dependencies in the asset list or use source/stub assets for external upstreams.
4. Replace external services with fakes or small local data in tests.
5. Route detailed resource/config construction to `../../configuration-resources/SKILL.md`.

## Partition or Backfill Fails

Symptoms:

- `context.partition_key` is unavailable.
- A single-run backfill processes only one partition.
- A partitioned downstream asset cannot map upstream partitions.

Actions:

1. Ensure the asset has `partitions_def=...`.
2. Use `context.partition_key` for one partition per run and `context.partition_key_range` only when a range is expected.
3. Add `backfill_policy=dg.BackfillPolicy.single_run()` only when the code explicitly handles a partition range.
4. For multi-partitions, inspect dimension names and access the date/static components deliberately.
5. For cross-partition dependencies, use an explicit partition mapping and keep the smallest reproducible example.

## Asset Check Fails or Is Not Found

Actions:

1. Confirm the check is included in `Definitions(asset_checks=[...])`.
2. Confirm `@dg.asset_check(asset=...)` targets the asset key or asset object that exists in the same Definitions context.
3. Return `dg.AssetCheckResult`, not a bare boolean.
4. Include metadata such as row counts or thresholds to make failures diagnosable.
5. For multi-asset checks, ensure `AssetCheckSpec` names and asset targets are unique.

## API Misuse Boundaries

- If the user asks how to run `dagster asset materialize` or configure a workspace, route to `../../cli-local-development/SKILL.md`.
- If the user asks how to pass credentials or environment variables, route to `../../configuration-resources/SKILL.md`.
- If the user asks how to trigger assets on schedules, sensors, or declarative automation, route to `../../automation-schedules-sensors/SKILL.md`.
- If the user asks about run launchers, code locations, or production backfills, route to `../../deployment-operations/SKILL.md`.
