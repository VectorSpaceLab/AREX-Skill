# Parameters, Configs, and IncludeFile

## Verified constructors

```python
Parameter(name, default=None, type=None, help=None, required=None, show_default=None, **kwargs)
IncludeFile(name, required=None, is_text=None, encoding=None, help=None, parser=None, **kwargs)
Config(name, default=None, default_value=None, help=None, required=None, parser=None, plain=False, **kwargs)
```

`JSONType` is a Click parameter type for JSON values. `config_expr("config.path")` creates a delayed expression that can be used in decorators.

## Parameter guidance

- Define parameters as class attributes.
- Parameter names become CLI flags such as `--alpha`.
- Avoid reserved names including `with`, `tag`, `namespace`, `run-id`, `max-workers`, `run-id-file`, and `runner-attribute-file`.
- Use `type=int`, `type=float`, `type=bool`, or `type=JSONType` when the default value is not enough.

## Config guidance

`Config` is evaluated before execution and can be used in decorators. Values become immutable `ConfigValue` mappings unless `plain=True`.

```python
from metaflow import Config, FlowSpec, config_expr, environment, step

class ConfiguredFlow(FlowSpec):
    cfg = Config("cfg", default_value={"mode": "debug"})

    @environment(vars={"MODE": config_expr("cfg.mode")})
    @step
    def start(self):
        self.mode = self.cfg.mode
        self.next(self.end)
```

Do not mutate `ConfigValue` in steps; copy it to a normal dict if you need to build derived state.

## IncludeFile guidance

`IncludeFile` reads a local file and stores its contents as a run artifact. Upload is delayed until the parameter is evaluated, which prevents premature file upload during graph checks.

- Use a local path for `default` or a CLI value.
- `is_text=True` and `encoding="utf-8"` are the normal text defaults.
- Direct cloud URI references such as `s3://...` are rejected by current IncludeFile behavior; download or materialize the file locally first, then pass the local path.
- Large files may make flow startup and artifact storage slow; prefer cloud datastores for large datasets and pass metadata/pointers as parameters.
