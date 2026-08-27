# Troubleshooting

Validated against spaCy 3.8.15 on the installed CPU environment.

Evidence provenance: `spacy/errors.py`, `spacy/language.py`, `spacy/pipe_analysis.py`, `spacy/tests/pipeline/test_pipe_factories.py`, `spacy/tests/test_factory_registrations.py`, and `website/docs/usage/processing-pipelines.mdx`.

Use this table when a pipeline assembly or component-registration task fails.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `E002` unknown factory | The factory name is not registered on the active `Language` subclass, or the module that registers it has not been imported yet. | Check `Language.has_factory(name)`. Import the module that defines `@Language.component` or `@Language.factory` before calling `add_pipe` or loading the config. If it is a built-in, confirm the active language subclass actually exposes it. |
| `E966` from `nlp.add_pipe` | A callable or component object was passed directly instead of the registered string name. | Register the component and pass its string name. Use `@Language.component("name")` for stateless functions or `@Language.factory("name")` for stateful/configurable components. |
| `ConfigValidationError`, `E962`, `E961`, `E964`, or `E965` | The factory signature or config is wrong: bad types, non-JSON-serializable values, missing `nlp`/`name`, or `@Language.component` used on a class. | Make the config JSON-serializable, add the required `nlp` and `name` arguments, and switch class-based components to `@Language.factory`. Use strict types only when you really want strict validation. |
| `E984` invalid component config | A component block in config is missing both `factory` and `source`, or the wrong key was used for the intended behavior. | Use `factory` when you want to create a fresh component from a registered factory. Use `source` when you want to copy a component from an existing pipeline. In a source block, the component name can be given separately with `component`. |
| `E007` duplicate pipeline name | You tried to add a second component with the same instance name. | Choose a unique `name=`, or remove/rename/replace the existing component first. `rename_pipe`, `replace_pipe`, and `remove_pipe` are the maintenance tools for this case. |
| `analyze_pipes` shows unmet requirements | The consumer component runs before the component that assigns the required annotations, or the custom component declared incomplete metadata. | Reorder with `before`, `after`, `first`, or `last`. For example, make sure something that sets sentences and entities runs before `entity_linker`. If the component is custom, verify its declared `assigns` and `requires` metadata. |
| `nlp.pipe` multiprocessing or batching surprises | This sub-skill only covers the structural relationship between `nlp.pipe`, `batch_size`, and the active pipeline. Throughput tuning and GPU multiprocessing caveats are outside scope. | Keep `n_process=1` first, then tune batch size only after the pipeline is correct. For multiprocessing, GPU, or accelerator caveats, hand off to `install-and-inspect`. |
| `source` copying does not look like a normal factory add | The first argument to `add_pipe(..., source=...)` is the source pipeline component name, not the factory name, and vocab/vector mismatches can affect the copy. | Check `nlp.get_pipe_meta(name).factory` and `nlp.get_pipe_config(name)`. If the source pipeline vectors differ, resolve the compatibility mismatch before trusting the copy. |

## Quick recovery patterns

```python
# Check availability before add_pipe
if not nlp.has_factory("my_component"):
    raise RuntimeError("missing factory")

# Inspect the resolved component and config
print(nlp.get_pipe_meta("my_component").factory)
print(nlp.get_pipe_config("my_component"))

# Inspect ordering problems
print(nlp.analyze_pipes(pretty=True))
```

## Route out of scope

- If the problem is about matcher, ruler, tokenizer, span, or visualization behavior, use `documents-and-visualization`.
- If the problem is about installation, missing wheels, backend support, or model loading, use `install-and-inspect`.
- If the problem is about config generation, training, evaluation, or packaging, use `training-and-cli`.
