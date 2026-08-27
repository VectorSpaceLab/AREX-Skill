# Configuration and Resource API Reference

This reference focuses on Dagster's Pythonic configuration and resource APIs. Examples use `import dagster as dg`.

## Structured Config

Use `dg.Config` for schema-checked parameters on assets, ops, and config mappings. It is Pydantic-backed, so type annotations, defaults, `pydantic.Field`, enums, nested config objects, validators, and validation errors behave like Pydantic models with Dagster-specific config conversion.

```python
from pydantic import Field
import dagster as dg

class ExtractConfig(dg.Config):
    source_table: str
    limit: int = Field(default=100, gt=0)

@dg.asset
def raw_users(config: ExtractConfig) -> list[str]:
    return read_users(config.source_table, limit=config.limit)
```

Important details:

- Constructor validation happens when the config object is instantiated, before Dagster launch validation.
- `Config._convert_to_config_dictionary()` is internal; use `RunConfig(...).to_config_dict()` when you need a public conversion surface.
- Nested `Config` objects and `EnvVar` values convert recursively when placed inside `RunConfig`.
- `Config.to_config_schema()` and `Config.to_fields_dict()` exist for bridging into legacy APIs that still expect Dagster config schemas.

Use `dg.PermissiveConfig` when the top-level schema has known fields plus arbitrary extra keys.

```python
class VendorPayload(dg.PermissiveConfig):
    endpoint: str
    timeout_seconds: int = 30

payload = VendorPayload(endpoint="events", custom_vendor_flag=True)
assert payload.custom_vendor_flag is True
```

Prefer `PermissiveConfig` only for genuinely open-ended payloads. If all keys are known, use `Config` to catch typos.

## RunConfig Shape

`dg.RunConfig` accepts structured Python objects and converts them to the run config dictionary Dagster validates at launch.

```python
run_config = dg.RunConfig(
    ops={"raw_users": ExtractConfig(source_table="users", limit=500)},
    resources={"warehouse": WarehouseResource(account=dg.EnvVar("WAREHOUSE_ACCOUNT"))},
)

materialize_result = dg.materialize(
    [raw_users],
    resources={"warehouse": WarehouseResource.configure_at_launch()},
    run_config=run_config,
)
```

Public fields:

- `ops`: config for ops, assets, and graph/job node entries keyed by node or asset op name.
- `resources`: launch-time resource config keyed by resource key.
- `loggers`: logger config dictionary.
- `execution`: executor config dictionary.

`RunConfig.to_config_dict()` returns a dictionary with `loggers`, `resources`, `ops`, and `execution`. For structured config objects, the nested output includes the `config` wrapper required by Dagster's run config schema.

Common shapes:

```python
# Asset or op config from Python.
dg.RunConfig(ops={"my_asset": MyConfig(flag=True)})

# Equivalent raw dict shape for an op/asset.
{"ops": {"my_asset": {"config": {"flag": True}}}}

# Launch-time resource config from Python.
dg.RunConfig(resources={"client": ClientResource(base_url="https://example")})

# Equivalent raw dict shape for a resource.
{"resources": {"client": {"config": {"base_url": "https://example"}}}}
```

When writing code that creates config programmatically, prefer `RunConfig` so `EnvVar`, nested `Config`, enum values, defaults, and resource objects are converted consistently.

## EnvVar

Use `dg.EnvVar("NAME")` for string fields and `dg.EnvVar.int("NAME")` for integer fields. `EnvVar` is deliberately deferred: direct string or integer coercion raises an error because Dagster should resolve it during launch/resource initialization.

```python
class ApiConfig(dg.Config):
    token: str
    request_limit: int

run_config = dg.RunConfig(
    ops={
        "call_api": ApiConfig(
            token=dg.EnvVar("API_TOKEN"),
            request_limit=dg.EnvVar.int("API_REQUEST_LIMIT"),
        )
    }
)
```

Use `.get_value(default=...)` only when the value must be read outside Dagster's config system, such as a standalone utility script. Do not log the resolved value.

If an `EnvVar` appears as the literal environment variable name at runtime, the object was probably instantiated outside Dagster's resource management path. Put the sub-resource as a typed field on a `ConfigurableResource` or pass the resource through `Definitions`/`RunConfig` so Dagster initializes it.

## ConfigurableResource

Use `dg.ConfigurableResource` for reusable external systems and shared dependencies. It is both structured config and a Dagster resource definition.

```python
import dagster as dg

class WriterResource(dg.ConfigurableResource):
    prefix: str

    def output(self, text: str) -> None:
        print(f"{self.prefix}{text}")

@dg.asset
def greeting(writer: WriterResource) -> None:
    writer.output("hello")

defs = dg.Definitions(
    assets=[greeting],
    resources={"writer": WriterResource(prefix="dev: ")},
)
```

Use `configure_at_launch()` when resource values must be supplied per run.

```python
defs = dg.Definitions(
    assets=[greeting],
    resources={"writer": WriterResource.configure_at_launch()},
)

result = defs.resolve_implicit_global_asset_job_def().execute_in_process(
    run_config=dg.RunConfig(resources={"writer": WriterResource(prefix="test: ")})
)
```

Override `create_resource(self, context)` when user code should receive a different runtime object than the config model.

```python
class ClientResource(dg.ConfigurableResource):
    base_url: str
    token: str

    def create_resource(self, context: dg.InitResourceContext) -> ApiClient:
        return ApiClient(base_url=self.base_url, token=self.token)

@dg.asset
def users(client: dg.ResourceParam[ApiClient]) -> None:
    client.fetch_users()
```

Lifecycle hooks are available on configurable resources when setup or teardown must run under Dagster's resource system:

- `setup_for_execution(self, context)` initializes clients, pools, or caches.
- `teardown_after_execution(self, context)` releases resources.
- `yield_for_execution(self, context)` can wrap setup/teardown as a context manager-style generator.

Keep pure Python construction in `create_resource`; reserve lifecycle hooks for effects that must happen per run.

## ResourceDependency

Nested `ConfigurableResource` fields can be declared directly. Use `dg.ResourceDependency[T]` when the dependency is a plain Python object, callable, legacy resource value, or other object that should be treated as a resource dependency instead of config data.

```python
from collections.abc import Callable
import dagster as dg

class PostfixWriter(dg.ConfigurableResource):
    writer: dg.ResourceDependency[Callable[[str], None]]
    postfix: str

    def output(self, text: str) -> None:
        self.writer(f"{text}{self.postfix}")
```

For nested resources with secrets, prefer typed fields on the parent resource so Dagster manages initialization and `EnvVar` resolution.

```python
class Credentials(dg.ConfigurableResource):
    token: str

class ApiResource(dg.ConfigurableResource):
    credentials: Credentials
    base_url: str

    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.credentials.token}"}

api = ApiResource(
    credentials=Credentials(token=dg.EnvVar("API_TOKEN")),
    base_url="https://example",
)
```

## ConfigurableIOManager

Use `dg.ConfigurableIOManager` when the IO manager itself is the runtime object and implements `handle_output` and `load_input`.

```python
import dagster as dg

class MemoryIOManager(dg.ConfigurableIOManager):
    namespace: str

    def handle_output(self, context: dg.OutputContext, obj: object) -> None:
        store[(self.namespace, tuple(context.asset_key.path))] = obj

    def load_input(self, context: dg.InputContext) -> object:
        return store[(self.namespace, tuple(context.asset_key.path))]
```

If the configured object should vend a separate IO manager instance, subclass `dg.ConfigurableIOManagerFactory` and implement `create_io_manager(self, context)`.

## Testing Resource Wiring

Choose the smallest test harness that proves the behavior:

```python
# Pure config validation.
config = ExtractConfig(source_table="users", limit=10)
assert config.limit == 10

# Direct resource behavior when Dagster lifecycle is irrelevant.
writer = WriterResource(prefix="unit: ")
writer.output("hello")

# Resource initialization and launch-time config.
defs = dg.Definitions(
    assets=[greeting],
    resources={"writer": WriterResource.configure_at_launch()},
)
assert defs.resolve_implicit_global_asset_job_def().execute_in_process(
    run_config=dg.RunConfig(resources={"writer": WriterResource(prefix="test: ")})
).success
```

Use `dg.build_resources` for tests that need initialized resource values without running a job. Use `dg.build_init_resource_context` for tests of resource factory methods or lifecycle code that need an `InitResourceContext`.
