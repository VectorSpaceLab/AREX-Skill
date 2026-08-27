# Asset Definition Workflows

Use these workflows to answer implementation, debugging, and local testing requests for Dagster assets and related definitions.

## Create or Repair an Asset Graph

1. Identify each business object that should be an asset key.
2. Use `@dg.asset` for one output per function; use `@dg.multi_asset` only when one compute step naturally produces several outputs.
3. Let function parameters express data dependencies when the downstream code consumes the upstream value.
4. Use `deps=[...]` for ordering-only dependencies or external/stub upstream assets.
5. Use `AssetIn` when the Python parameter name differs from the upstream asset key.
6. Put all assets into `dg.Definitions(assets=[...])` and resolve or materialize locally before suggesting deployment or CLI execution.

Dependency repair checklist:

- If Dagster reports a missing input, check whether the parameter name should match an upstream asset key.
- If the dependency is intentionally non-argument, move it to `deps=[...]` and remove the unused parameter.
- If an upstream key has a prefix or multi-component key, use `dg.AssetKey([...])` or `dg.AssetIn(key=...)` consistently.
- If a multi-asset has partial output dependencies, add `internal_asset_deps`.

## Build Definitions for a Project Module

For a single file, export one module-level `defs` object:

```python
import dagster as dg

@dg.asset
def upstream() -> int:
    return 1

@dg.asset
def downstream(upstream: int) -> int:
    return upstream + 1

all_assets = dg.define_asset_job("all_assets", selection="*")
defs = dg.Definitions(assets=[upstream, downstream], jobs=[all_assets])
```

For a package, prefer deterministic imports and `load_assets_from_modules`:

```python
import dagster as dg
from my_project import core_assets, report_assets

defs = dg.Definitions(
    assets=dg.load_assets_from_modules([core_assets, report_assets]),
    jobs=[dg.define_asset_job("reports", selection=dg.AssetSelection.groups("reports"))],
)
```

Do not hide network calls, credential reads, or expensive discovery at import time. Asset modules should define objects on import; execution-time side effects belong inside asset functions or resources.

## Define Asset Jobs and Selections

Use `define_asset_job` for asset-backed execution targets:

```python
import dagster as dg

core_job = dg.define_asset_job(
    name="core_job",
    selection=dg.AssetSelection.groups("core") - dg.AssetSelection.keys("legacy_asset"),
)

defs = dg.Definitions(assets=[...], jobs=[core_job])
job_def = defs.resolve_job_def("core_job")
```

Guidelines:

- Use `Definitions.resolve_job_def` to validate unresolved asset jobs.
- Use groups for broad routing and explicit keys for small surgical jobs.
- Use asset selection set operators to express include/exclude logic.
- Keep schedule/sensor attachment in the automation sub-skill unless the task only needs the target job object.

## Add Partitions and Backfill Policy

1. Choose the partition dimension: static, time-window, dynamic, or multi-partition.
2. Attach the `partitions_def` to every asset that shares the same partition space.
3. Use `context.partition_key` for one partition per run.
4. Use `context.partition_key_range` only with a backfill policy that allows one run to cover a range.
5. Add `backfill_policy=dg.BackfillPolicy.single_run()` when one run should process a partition range, or `multi_run(...)` when runs should be split.
6. Keep config/resource values separate from partition keys; route detailed config/resource work to `../../configuration-resources/SKILL.md`.

Example pattern:

```python
import dagster as dg

daily = dg.DailyPartitionsDefinition(start_date="2024-01-01")

@dg.asset(partitions_def=daily, backfill_policy=dg.BackfillPolicy.single_run())
def orders_daily(context: dg.AssetExecutionContext) -> str:
    start, end = context.partition_key_range.start, context.partition_key_range.end
    return f"processing {start} through {end}"
```

If a user asks for CLI backfill commands or daemon behavior, route to CLI or deployment/operations after clarifying the asset definition shape.

## Add Asset Checks

1. Define the asset first.
2. Add `@dg.asset_check(asset=asset_obj_or_key)` for one check per function.
3. Return `dg.AssetCheckResult(passed=..., metadata=...)`.
4. Include checks in `Definitions(asset_checks=[...])`.
5. For one compute function that emits both assets and checks, use `check_specs` and `AssetCheckSpec` with a multi-asset.

Test a check by materializing the asset/check set locally where possible, or by resolving the Definitions object to ensure the check targets the intended asset key.

## Unit Test Assets and Definitions

Use the smallest safe test target:

- Pure assets: `dg.materialize_to_memory([asset_a, asset_b])`.
- Assets needing resources: `dg.materialize([...], resources={...})` with lightweight fakes.
- Asset jobs: create `Definitions`, then `defs.resolve_job_def("job_name")`.
- Definition metadata assertions: `defs.resolve_all_asset_specs()`.
- Dependency graph assertions: inspect `AssetsDefinition.keys`, `dependency_keys`, and `asset_deps`.

Example smoke test:

```python
import dagster as dg

@dg.asset
def a() -> int:
    return 1

@dg.asset
def b(a: int) -> int:
    return a + 1

result = dg.materialize_to_memory([a, b])
assert result.success
assert result.output_for_node("b") == 2
```

Use the bundled `scripts/validate_defs_smoke.py` when the user asks for a quick imported-module check rather than a full test suite.

## Debug Missing Dependency Case

For a user with three assets and one missing dependency:

1. List expected asset keys and Python parameter names.
2. Check whether the missing parameter should be renamed to an upstream asset key.
3. If the dependency is intentionally external, model it as `SourceAsset`, `AssetSpec`, or `deps=[...]` depending on whether it is materializable in this code location.
4. Add a `Definitions` object and call `resolve_all_asset_specs()` or materialize a tiny subset.
5. Use `AssetSelection.keys(...)` to isolate the failing branch.

## Partitioned Backfill with Config/Resource Separation

For partitioned asset backfill guidance:

1. Keep partition dimensions in `partitions_def`.
2. Keep credentials, file roots, warehouse clients, and API clients in resources.
3. Keep per-run user parameters in config, not in partition keys.
4. Use `BackfillPolicy.single_run()` only when the asset body can process `context.partition_key_range` correctly.
5. Validate with a small date range and fake resources before suggesting production backfills.
