# Registry and import paths

## Runtime registration helpers

YiVal registers custom components from YAML during `ExperimentRunner._register_custom_components()` using helpers in `yival.experiment.utils`.

The helpers expect mappings like:

```yaml
custom_evaluators:
  my_eval:
    class: my_pkg.my_module.MyEvaluator
    config_cls: my_pkg.my_module.MyEvaluatorConfig
```

Each helper:

1. calls `_get_class_from_path(details["class"])`;
2. optionally calls `_get_class_from_path(details["config_cls"])`;
3. registers the class against the mapping key (`my_eval`).

## `_get_class_from_path` behavior

The helper splits the path at the last dot:

```text
my_pkg.my_module.MyClass
```

Then imports `my_pkg.my_module` and returns `MyClass`.

For path-like module strings, it also appends the directory component of the module path to `sys.path`. This is brittle. Prefer importable package/module names and set `PYTHONPATH` explicitly.

## Common YAML key gotchas

- Runtime registration helpers use `config_cls`, not `config_path`.
- `custom_reader` is singular in `ExperimentConfig`, while most other sections are plural (`custom_wrappers`, `custom_evaluators`, etc.).
- `ExperimentRunner._register_custom_components()` calls `self.config.get("custom_selection_strategy", {})` in the baseline, while the dataclass/CLI generation names `custom_selection_strategies`. If a custom selection strategy does not register, import/register it manually before constructing the runner or verify the exact key expected by the installed version.
- `register_custom_enhancer()` expects `custom_enhancer` when called directly, while the runner reads `custom_enhancers` for enhancers. Check the installed code when debugging custom enhancer registration.

## Direct decorator registration

Some base classes also expose direct registration methods or decorators. This can be useful in custom modules:

```python
from yival.evaluators.base_evaluator import BaseEvaluator

@BaseEvaluator.register("my_eval")
class MyEvaluator(BaseEvaluator):
    ...
```

If the module is imported before runner setup, the registry id is already available. YAML `custom_*` registration is still preferred for explicit, config-driven runs.

## Verification probes

Inside the same process that will run YiVal:

```python
from yival.evaluators.base_evaluator import BaseEvaluator
import my_pkg.my_eval_module
print(BaseEvaluator._registry.keys())
```

For runner-driven registration, inspect after `runner._register_custom_components()` or just run a tiny fixture and check errors.
