---
name: custom-components
description: "Implement and register custom YiVal readers, wrappers, evaluators,
  generators, enhancers, selection strategies, and output parsers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# YiVal custom components

Use this sub-skill when the user needs to extend YiVal with a custom data reader, wrapper, evaluator, data generator, variation generator, enhancer, selection strategy, or output parser, or when a YAML `custom_*` section fails to register.

## Read first

- [Custom component patterns](references/custom-component-patterns.md): base classes, required methods, config dataclasses, and YAML registration.
- [Registry and import paths](references/registry-and-import-paths.md): how YiVal resolves custom classes.
- [Custom examples](references/custom-examples.md): concise examples for common custom components.
- [Custom troubleshooting](references/troubleshooting.md): import, config, and registry failures.

Useful helper:

- `python sub-skills/custom-components/scripts/write_component_skeleton.py --kind evaluator --output-dir ./my_yival_components` writes small starter files for selected component kinds.

## Custom YAML sections

| Component | YAML section | Base class |
| --- | --- | --- |
| Reader | `custom_reader` | `yival.data.base_reader.BaseReader` |
| Wrapper | `custom_wrappers` | `yival.wrappers.base_wrapper.BaseWrapper` |
| Evaluator | `custom_evaluators` | `yival.evaluators.base_evaluator.BaseEvaluator` |
| Data generator | `custom_data_generators` | `yival.data_generators.base_data_generator.BaseDataGenerator` |
| Variation generator | `custom_variation_generators` | `yival.variation_generators.base_variation_generator.BaseVariationGenerator` |
| Selection strategy | `custom_selection_strategies` | `yival.result_selectors.selection_strategy.SelectionStrategy` |
| Enhancer | `custom_enhancers` | `yival.enhancers.base_combination_enhancer.BaseCombinationEnhancer` |

General runtime form:

```yaml
custom_evaluators:
  simple_evaluator:
    class: my_components.simple_evaluator.SimpleEvaluator
    config_cls: my_components.simple_evaluator.SimpleEvaluatorConfig
```

Then use the registry id in the normal section:

```yaml
evaluators:
  - name: simple_evaluator
    evaluator_type: individual
    metric_calculators: []
```

## Implementation checklist

1. Put the custom module on `PYTHONPATH` or install it in the active environment.
2. Define a dataclass config that inherits the matching YiVal base config class when one exists.
3. Subclass the correct base class and implement the required abstract method.
4. Set `default_config` on the class if config generation/default lookup should work.
5. Add the correct `custom_*` YAML block with `class` and `config_cls`.
6. Reference the custom id in `dataset.reader`, `dataset.data_generators`, `variations[].generator_name`, `evaluators[].name`, `selection_strategy`, or `enhancer.name`.
7. Run a tiny no-network fixture before provider-backed work.

## Important import-path behavior

YiVal's helper `_get_class_from_path()` splits a dotted class path into a module path and class name. For ordinary installed modules, use `package.module.ClassName`. For ad-hoc files, put the parent directory on `PYTHONPATH` and still use a dotted module path.

Avoid relying on absolute filesystem strings in reusable configs; install or package the custom module where possible.

## Route elsewhere

- Use [setup](../setup/SKILL.md) for base YAML generation/validation.
- Use [run](../run/SKILL.md) for executing experiments and inspecting output pickles.
- Use [evaluation-optimization](../evaluation-optimization/SKILL.md) for custom evaluator semantics, AHP metrics, and enhancer behavior.
