# Configuration and Resource Workflows

Use these workflows when implementing or debugging Dagster config/resources in repository code.

## Convert Legacy Dict Config to Pythonic Config

1. Identify the existing raw run config shape. For ops/assets, look under `ops: <node>: config:`. For resources, look under `resources: <key>: config:`.
2. Create a `dg.Config` class for each stable schema. Use defaults for optional values and `pydantic.Field` for descriptions, bounds, aliases, or validation metadata.
3. Replace raw Python run config construction with `dg.RunConfig` while preserving the same keys.
4. Replace secret literals with `dg.EnvVar("NAME")` or `dg.EnvVar.int("NAME")` inside the structured object.
5. Compare `RunConfig(...).to_config_dict()` with the previous dict shape in a unit test before changing execution code.

Template:

```python
class LoadConfig(dg.Config):
    table: str
    batch_size: int = 1000
    api_token: str

run_config = dg.RunConfig(
    ops={
        "load_customers": LoadConfig(
            table="customers",
            batch_size=500,
            api_token=dg.EnvVar("CUSTOMER_API_TOKEN"),
        )
    }
)
```

Avoid passing `EnvVar` into an unstructured raw dict. Use structured `Config`/`RunConfig` so Dagster converts the value to the supported environment-variable config representation.

## Add a ConfigurableResource

1. Define a `dg.ConfigurableResource` with typed fields for configuration.
2. Put user-facing methods on the resource when the resource object itself is useful to assets/ops.
3. Override `create_resource` only when assets/ops should receive a separate client or adapter object.
4. Register the resource in `dg.Definitions(resources={...})` with a stable key matching the asset/op parameter name.
5. Use `configure_at_launch()` if schedules, sensors, UI launchpad, or tests need per-run values.

Template:

```python
class WarehouseResource(dg.ConfigurableResource):
    account: str
    database: str

    def query(self, sql: str) -> list[dict[str, object]]:
        return run_query(account=self.account, database=self.database, sql=sql)

@dg.asset
def daily_orders(warehouse: WarehouseResource) -> None:
    warehouse.query("select * from orders")

defs = dg.Definitions(
    assets=[daily_orders],
    resources={
        "warehouse": WarehouseResource(
            account=dg.EnvVar("WAREHOUSE_ACCOUNT"),
            database="analytics",
        )
    },
)
```

## Add Nested Resources

Use nested resources when multiple resources share credentials, clients, or state.

```python
class CredentialsResource(dg.ConfigurableResource):
    username: str
    password: str

class ApiResource(dg.ConfigurableResource):
    credentials: CredentialsResource
    base_url: str

    def auth_header(self) -> dict[str, str]:
        return {"Authorization": f"Basic {self.credentials.username}:***"}
```

When the nested dependency is not a `ConfigurableResource`, annotate it with `ResourceDependency` so Dagster treats it as a resource rather than a config field.

```python
class AuditResource(dg.ConfigurableResource):
    emit: dg.ResourceDependency[Callable[[str], None]]
    prefix: str

    def record(self, message: str) -> None:
        self.emit(f"{self.prefix}{message}")
```

Debug rule: if a nested value is being validated as config when you expected a resource, check the annotation first. Plain types like `str`, `dict`, and callables may need `ResourceDependency[...]` depending on intent.

## Add Launch-Time Resource Config

Use this when a schedule, sensor, test, or manual launch should choose resource values.

```python
defs = dg.Definitions(
    assets=[daily_orders],
    resources={"warehouse": WarehouseResource.configure_at_launch()},
)

run_config = dg.RunConfig(
    resources={
        "warehouse": WarehouseResource(
            account=dg.EnvVar("WAREHOUSE_ACCOUNT"),
            database="analytics_test",
        )
    }
)
```

If writing a `RunRequest`, set its config to the `RunConfig` object or to the result of `to_config_dict()` depending on the API contract in the calling code. Keep tests around the final `RunRequest.run_config` shape.

## Add a Configurable IO Manager

1. Subclass `dg.ConfigurableIOManager` when the configured object can implement `handle_output` and `load_input` directly.
2. Add typed config fields for storage paths, namespaces, buckets, or connection parameters.
3. Register it under the resource key `io_manager` for the default asset IO manager, or another key if an asset explicitly selects it.
4. Test with materialization if context attributes such as `asset_key`, partition keys, metadata, or upstream output identifiers are involved.

Template:

```python
class PrefixIOManager(dg.ConfigurableIOManager):
    prefix: str

    def handle_output(self, context: dg.OutputContext, obj: object) -> None:
        write_object(key=f"{self.prefix}/{context.asset_key.to_user_string()}", value=obj)

    def load_input(self, context: dg.InputContext) -> object:
        return read_object(key=f"{self.prefix}/{context.asset_key.to_user_string()}")
```

## Test Config and Resources

Use this decision tree:

- For Pydantic type/default validation, instantiate the `Config` or `ConfigurableResource` directly.
- For `RunConfig` conversion, assert on `RunConfig(...).to_config_dict()` or `dg.validate_run_config(job, run_config)`.
- For resource methods with no Dagster lifecycle, call the method directly on the resource instance.
- For `EnvVar` resolution, nested resources, lifecycle hooks, and launch-time resource config, execute through `Definitions` or `build_resources` so Dagster owns initialization.
- For asset/op behavior that depends on the resource parameter, use `materialize` or `execute_in_process` with explicit test resources.

Minimal launch-time test:

```python
class WriterResource(dg.ConfigurableResource):
    prefix: str
    values: list[str] = []

    def output(self, text: str) -> None:
        self.values.append(f"{self.prefix}{text}")

@dg.asset
def hello(writer: WriterResource) -> None:
    writer.output("hello")

def test_writer_launch_config() -> None:
    resource = WriterResource(prefix="test: ")
    result = dg.materialize([hello], resources={"writer": resource})
    assert result.success
    assert resource.values == ["test: hello"]
```

If list/dict fields are mutable, prefer `pydantic.Field(default_factory=list)` or keep mutable state outside config models unless the test intentionally checks stateful behavior.
