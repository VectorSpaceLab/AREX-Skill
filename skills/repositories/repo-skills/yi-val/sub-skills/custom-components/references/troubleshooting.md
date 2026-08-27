# Custom component troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ImportError` for custom class | Module is not on `PYTHONPATH` or class path is not dotted correctly. | Install the custom package or set `PYTHONPATH` to the parent directory; use `package.module.Class`. |
| `KeyError: class` or `config_cls` ignored | YAML section uses docs-era `config_path` instead of runtime `config_cls`. | Use `class` and `config_cls` keys. |
| Registry id not found | Custom YAML section was not read, wrong key name, or module import failed. | Verify exact `custom_*` key and run a tiny import/registry probe. |
| Config dataclass rejects YAML fields | Config class lacks fields supplied in YAML. | Add dataclass fields with defaults or remove extra YAML keys. |
| Custom reader returns wrong shape | Reader yields dicts/lists instead of `InputData` chunks. | Yield `Iterator[List[InputData]]`. |
| Custom function receives unexpected kwargs | Reader/data generator `content` keys do not match function parameters. | Align field names and inspect `get_function_args()`. |
| Custom evaluator output not aggregated | Missing `metric_calculators` or non-numeric result for AVERAGE. | Return numeric `EvaluatorOutput.result` for averaged metrics. |
| Custom selection strategy never runs | YAML custom strategy key mismatch in the installed version. | Import/register the strategy module before running or verify runner code's custom strategy key. |

## Minimal debug snippet

```python
import importlib

module = importlib.import_module("my_components.keyword_evaluator")
print(module.ContainsKeywordEvaluator)
```

Then check the appropriate registry after registration:

```python
from yival.evaluators.base_evaluator import BaseEvaluator
print(BaseEvaluator._registry)
```

## Best practices

- Keep custom components in a small importable package.
- Use absolute dataset paths in configs; use dotted import paths for Python classes/functions.
- Write one no-network test row and one variation before provider-backed runs.
- Do not place credentials or tokens inside YAML checked into source control.
