# Custom Components and Metrics

Use this reference when a config needs local code, a new component name, or a
custom metric. It covers the registry path, `metadata.imports`, and the `id` /
`ref` / `#id` mechanics used inside configs.

## Ways To Reference Custom Code

1. **Register a short name**
   - Decorate the class or function with `@register('name')` or
     `@register_metric('name')`.
   - Use that name in `class_name` or metric `name` fields.

2. **Use a fully qualified import path**
   - `class_name: "module.submodule:ClassName"`
   - metric `name: "module.submodule:function_name"`

3. **Pre-import local modules from the config**
   - Add the module path to `metadata.imports` so the decorator code runs before
     the pipeline is built.

## Component Reuse Patterns

- `id` stores a component under a local name inside the build session.
- `ref` reuses the previously initialized component object with that id.
- `#component_id` inside a string value resolves to the stored component.
- `#component_id.some_attribute` resolves an attribute chain on that component.
- `main: true` marks the component that should be treated as the pipeline’s
  primary saved output.

Example shape:

```json
{
  "chainer": {
    "in": ["x"],
    "pipe": [
      {
        "class_name": "split_tokenizer",
        "id": "tokenizer",
        "in": ["x"],
        "out": ["x_tokens"]
      },
      {
        "ref": "tokenizer",
        "in": ["y"],
        "out": ["y_tokens"]
      }
    ],
    "out": ["x_tokens"]
  }
}
```

## Registry Rebuild Workflow

After adding new decorated components or metrics to a local checkout, rebuild
DeepPavlov’s registry files so the short names are discoverable.

```bash
python -m utils.prepare.registry
```

That command walks the package, reloads the modules that define registered
classes or metrics, and refreshes the registry JSON files.

Use this when:

- The new component uses a short registered name and does not appear in the
  runtime registry.
- You added a new metric and want it available by name in configs.
- A config works with a fully qualified import path but you want a stable short
  name for reuse.

## Custom-Component Checklist

- The class inherits from `Component`, `DatasetReader`, `DataLearningIterator`,
  `DataFittingIterator`, or an appropriate trainer/model base.
- The constructor arguments match the config keys you plan to pass.
- The component can be imported through `metadata.imports` or a fully qualified
  path.
- Trainable components declare `fit_on` or `in_y` as appropriate.
- Persisted components define `save_path` and `load_path` when they need to be
  reloaded later.
- If the component needs extra packages, declare them in `metadata.requirements`
  so install workflows can pick them up.

## Common Errors and Their Meaning

- `Model <name> is not registered.`
  - The short name is unknown to the registry.
  - Fix: register the class, add `metadata.imports`, or use a full import path.

- `Expected class description in a module.submodules:ClassName form`
  - The `class_name` string is malformed.
  - Fix: use the exact `module:ClassName` syntax.

- `Component config has no class_name nor ref fields`
  - The config item is missing both a constructor and a reuse reference.
  - Fix: add `class_name`, `ref`, or `config_path`.

- `Component with id "..." was referenced but not initialized`
  - A `ref` or `#id` points to a component that has not been created yet.
  - Fix: define the source component earlier in the pipeline or rename the id.

- Registry overwrite warning
  - A short name already exists and a new registration replaces it.
  - Fix: choose a more specific name if the overwrite is accidental.

For a config-level symptom that looks like a registry problem, check the
troubleshooting reference before changing the code itself.
