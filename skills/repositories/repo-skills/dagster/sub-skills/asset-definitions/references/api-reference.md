# Asset Definitions API Reference

This reference distills the Dagster public API surface for assets, jobs, Definitions, partitions, checks, metadata, and local tests. Use `import dagster as dg` unless matching an existing project style.

## Core Definition Objects

| Need | API | Notes |
| --- | --- | --- |
| Single asset | `@dg.asset` | Function name becomes the asset key by default. Inputs infer upstream dependencies by parameter name. |
| Multiple assets from one function | `@dg.multi_asset` | Use `outs={"name": dg.AssetOut(...)}` and optionally `can_subset=True`. |
| Asset check | `@dg.asset_check` | Return `dg.AssetCheckResult(passed=..., metadata=...)`; include in `Definitions(asset_checks=[...])`. |
| Multi-asset check | `@dg.multi_asset_check` | Use when one function evaluates checks for multiple assets. |
| Op | `@dg.op` | Building block for jobs or graph-backed assets; not automatically an asset. |
| Graph | `@dg.graph` | Compose ops and convert to jobs or graph-backed assets. |
| Job | `@dg.job` | Direct executable graph of ops; include in `Definitions(jobs=[...])`. |
| Asset job | `dg.define_asset_job` | Produces an unresolved asset job that is resolved by `Definitions`. |
| Repository unit | `dg.Definitions` | Bundle assets, jobs, schedules, sensors, resources, asset checks, and executors. |

## Assets

Common `@dg.asset` arguments:

- `name` or `key`: override the default asset key.
- `deps`: declare upstream dependencies that are not function parameters, including strings, `AssetKey`, `AssetDep`, or asset definitions.
- `ins`: map input names to `dg.AssetIn(key=..., partition_mapping=..., metadata=...)`.
- `group_name`: group assets in the UI and selections.
- `partitions_def`: attach static, daily, hourly, weekly, monthly, dynamic, or multi-partitions.
- `backfill_policy`: control single-run or multi-run backfill behavior for partitioned assets.
- `metadata`, `tags`, `owners`, `kinds`, `code_version`, `description`: annotate asset specs.
- `io_manager_key` and `required_resource_keys`: route to configuration/resources guidance when resource details dominate the task.

Minimal asset graph:

```python
import dagster as dg

@dg.asset(owners=["team:data"], kinds={"python"}, metadata={"priority": "gold"})
def raw_orders() -> list[dict[str, object]]:
    return [{"id": 1, "amount": 10.0}]

@dg.asset(deps=[raw_orders], code_version="v1")
def order_count(raw_orders: list[dict[str, object]]) -> int:
    return len(raw_orders)

defs = dg.Definitions(assets=[raw_orders, order_count])
```

Use parameter dependencies when the downstream computation needs the upstream value. Use `deps=[...]` when the dependency is ordering-only or the value is loaded some other way.

## Multi-Assets

Use `@dg.multi_asset` when one compute step materializes multiple asset keys.

```python
import dagster as dg

@dg.multi_asset(
    outs={"users": dg.AssetOut(), "orders": dg.AssetOut()},
    can_subset=True,
)
def extract_tables(context: dg.AssetExecutionContext):
    if "users" in context.selected_output_names:
        yield dg.Output([{"id": 1}], output_name="users")
    if "orders" in context.selected_output_names:
        yield dg.Output([{"id": 10}], output_name="orders")
```

For partial dependencies between outputs, use `internal_asset_deps` so Dagster knows which output depends on which inputs or sibling outputs. If checks are attached to multi-assets, ensure check specs remain selectable with the intended asset outputs.

## Asset Checks

Asset checks are definition-time objects and run-time evaluations. Keep them close to the asset they validate unless they need separate ownership.

```python
import dagster as dg

@dg.asset
def customers() -> list[str]:
    return ["alice"]

@dg.asset_check(asset=customers, name="non_empty")
def customers_non_empty(customers: list[str]) -> dg.AssetCheckResult:
    return dg.AssetCheckResult(
        passed=len(customers) > 0,
        metadata={"row_count": len(customers)},
        severity=dg.AssetCheckSeverity.ERROR,
    )

defs = dg.Definitions(assets=[customers], asset_checks=[customers_non_empty])
```

Use `dg.AssetCheckSpec` with `@dg.multi_asset` when the check is produced by the same compute function as assets, and use `dg.AssetCheckKey` only when lower-level selection or assertion logic needs explicit keys.

## Jobs and Selections

`dg.define_asset_job` creates an asset job by selection. It is commonly placed in `Definitions(jobs=[...])` with the selected assets.

```python
import dagster as dg

all_assets_job = dg.define_asset_job("all_assets", selection="*")
core_job = dg.define_asset_job(
    "core_assets",
    selection=dg.AssetSelection.groups("core") | dg.AssetSelection.keys("order_count"),
)

defs = dg.Definitions(assets=[raw_orders, order_count], jobs=[all_assets_job, core_job])
resolved = defs.resolve_job_def("core_assets")
```

Selection options include strings, asset definitions, asset keys, groups, and `AssetSelection` expressions. Use `AssetSelection.all()` or ``"*"` for all materializable assets, `AssetSelection.keys(...)` for explicit keys, and set operations (`|`, `&`, `-`) for composed selections. When a job is built from `define_asset_job`, treat it as unresolved until attached to a `Definitions` object.

## Ops, Graphs, and Graph-Backed Assets

Use ops and jobs for imperative task graphs that are not asset-first. Use graph-backed assets when a composed graph should produce one or more asset keys.

```python
import dagster as dg

@dg.op
def fetch_rows() -> list[int]:
    return [1, 2, 3]

@dg.op
def count_rows(rows: list[int]) -> int:
    return len(rows)

@dg.graph
def count_graph():
    return count_rows(fetch_rows())

row_count_asset = dg.AssetsDefinition.from_graph(count_graph)
defs = dg.Definitions(assets=[row_count_asset])
```

For a simple asset, prefer `@dg.asset`. Reach for `@dg.op`/`@dg.graph` when the graph shape needs reusable op composition, explicit inputs/outputs, or a direct `@dg.job`.

## Partitions and Backfills

Common partition definitions:

- `dg.StaticPartitionsDefinition(["us", "eu"])` for a fixed key set.
- `dg.DailyPartitionsDefinition(start_date="2024-01-01")` for daily time windows.
- `dg.HourlyPartitionsDefinition`, `WeeklyPartitionsDefinition`, and `MonthlyPartitionsDefinition` for other time grains.
- `dg.DynamicPartitionsDefinition(name="customers")` when partition keys are stored in the Dagster instance.
- `dg.MultiPartitionsDefinition({"date": daily, "region": static})` for Cartesian partition dimensions.

Example with single-run backfill policy:

```python
import dagster as dg

daily = dg.DailyPartitionsDefinition(start_date="2024-01-01")

@dg.asset(
    partitions_def=daily,
    backfill_policy=dg.BackfillPolicy.single_run(),
)
def daily_orders(context: dg.AssetExecutionContext) -> int:
    partition_key = context.partition_key
    return len(partition_key)
```

Use `context.partition_key` for one selected partition, `context.partition_key_range` when a single run handles a range, and resource/config patterns when each partition needs environment-specific external access.

## Definitions Patterns

A `Definitions` object is the public module-level object most Dagster loaders expect.

```python
import dagster as dg

assets = [raw_orders, order_count]
jobs = [dg.define_asset_job("core", selection=dg.AssetSelection.all())]
defs = dg.Definitions(assets=assets, jobs=jobs)
```

Useful methods for local validation:

- `defs.resolve_job_def("job_name")`: resolve a direct job or unresolved asset job.
- `defs.get_assets_def("asset_key")`: fetch an `AssetsDefinition` without resolving the whole repository when possible.
- `defs.resolve_all_asset_specs()`: inspect the resolved asset specs for keys, groups, metadata, owners, and kinds.
- `defs.get_unresolved_schedule_def(...)` and `defs.get_unresolved_sensor_def(...)`: schedule/sensor-specific, route deeper automation work elsewhere.

Module loading helpers are useful for larger projects:

```python
import dagster as dg
from my_project import assets

defs = dg.Definitions(
    assets=dg.load_assets_from_modules([assets]),
    jobs=[dg.define_asset_job("all_assets")],
)
```

Use module loading when assets are spread across files, but keep imports deterministic and side-effect free so local validation and code-location loading are reliable.

## Local Materialization and Tests

For pure Python assets without external services:

```python
import dagster as dg

result = dg.materialize_to_memory([raw_orders, order_count])
assert result.success
assert result.output_for_node("order_count") == 1
```

For assets requiring resources or IO managers, use `dg.materialize([...], resources={...})` or construct a `Definitions` object and resolve jobs. Keep resource and config design in the configuration/resources sub-skill.

## Metadata and Events

Inside an asset, emit metadata through returns, `context.add_output_metadata`, or typed results.

```python
import dagster as dg

@dg.asset
def scored_table(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    context.add_output_metadata({"rows": 10})
    return dg.MaterializeResult(metadata={"quality": "ok"})
```

Use `dg.Output(..., metadata=...)` in `@multi_asset`, and use `dg.AssetMaterialization` only when working at lower-level event APIs or op/job workflows.
