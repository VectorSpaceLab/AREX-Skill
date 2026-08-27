# Registry and Extension Reference

LLM Foundry builds most configurable components through typed registries. Use this reference when you need to inspect keys, register custom components, debug constructor dispatch, or adapt a config that uses package registries.

## Registry objects

Registry objects live under `llmfoundry.registry` and lower-level layer registries are re-exported through it. Each registry is a typed wrapper around `catalogue.Registry` with a namespace such as `('llmfoundry', 'models')`.

Runtime inspection:

```python
from llmfoundry import registry

print(sorted(registry.models.get_all()))
model_cls = registry.models.get('mpt_causal_lm')
```

CLI inspection:

```bash
llmfoundry registry get
llmfoundry registry get models
llmfoundry registry find models mpt_causal_lm
```

The `get` command lists groups, descriptions, and keys. The `find` command reports the module, file, line number, and docstring for one key when the registry can locate it.

## Registry construction

The lower-level helper is:

```python
from llmfoundry.utils.registry_utils import construct_from_registry

construct_from_registry(
    name='decoupled_lionw',
    registry=registry.optimizers,
    partial_function=True,
    pre_validation_function=None,
    post_validation_function=None,
    kwargs={'params': model.parameters(), 'lr': 1e-4},
)
```

Behavior:

- The exact `name` is looked up with `registry.get(name)`.
- `pre_validation_function` can be a type check or callable validation before construction.
- Classes are constructed immediately with `**kwargs`.
- Callables return a `functools.partial` when `partial_function=True`.
- Callables are invoked immediately when `partial_function=False`; this is how builder functions are handled.
- Non-callable registry entries are invalid for construction.
- `post_validation_function` runs after construction.

Common failure interpretations:

| Symptom | Likely cause |
| --- | --- |
| Unknown registry key | The component was not imported/registered, the key is misspelled, or an entry-point package is not installed in the active environment. |
| `TypeError: unexpected keyword argument` | The config contains kwargs not accepted by the target constructor. Remove YAML-only fields such as `name` before direct construction. |
| `Expected <name> to be of type ...` | A registry entry exists but is not a subclass of the expected Composer/HF/torch type. |
| `Expected <name> to be a class or function` | Something non-callable was registered. |

## One-run extension with `code_paths`

Train and eval config loaders import files listed in top-level `code_paths` before registry-driven builders run. The imported file can register custom components.

Example extension file:

```python
# custom_registry_code.py
from composer.loggers import InMemoryLogger
from llmfoundry.registry import loggers

@loggers.register('my_in_memory_logger')
class MyInMemoryLogger(InMemoryLogger):
    pass
```

Example YAML fragment:

```yaml
code_paths:
- custom_registry_code.py

loggers:
  my_in_memory_logger: {}
```

Operational notes:

- `code_paths` is top-level in both train and eval configs.
- Import execution is arbitrary Python; keep it small, deterministic, and free of downloads/training side effects.
- Import failures are wrapped as `RuntimeError: Error executing <path>`.
- Missing files fail with `FileNotFoundError`.
- This pattern is best for a single run, notebook, or platform job where the source file is shipped with the job.

## Reusable extension with Python entry points

Each registry was created with entry-point loading enabled. A reusable Python package can expose registry entries through entry-point groups derived from the namespace: `llmfoundry_<registry_name>`.

Example `pyproject.toml` fragment for an extension package:

```toml
[project.entry-points."llmfoundry_callbacks"]
my_callback = "my_pkg.callbacks:MyCallback"

[project.entry-points."llmfoundry_models"]
my_model = "my_pkg.models:MyComposerModel"

[project.entry-points."llmfoundry_tokenizers"]
my_tokenizer = "my_pkg.tokenizers:MyTokenizer"
```

Then install the extension package into the same environment as LLM Foundry and verify:

```bash
llmfoundry registry get callbacks
llmfoundry registry find callbacks my_callback
```

Use entry points when the extension must be reused across jobs without listing `code_paths` every time.

## Direct decorator registration

Direct registration is useful in library code, tests, and `code_paths` modules.

```python
from llmfoundry.registry import callbacks, models, optimizers

@callbacks.register('my_callback')
class MyCallback(...):
    ...

models.register('my_model', func=MyComposerModel)
optimizers.register('my_optimizer', func=MyOptimizer)
```

Registration overwrites an existing key if the same key is registered again in the current process. Avoid accidental collisions with built-in names.

## Builder-specific extension contracts

### Models

Registry: `registry.models`

Expected type: `composer.models.ComposerModel` subclass or builder returning one.

Constructor convention: model constructors should accept a `tokenizer` keyword plus any model-specific kwargs. `build_composer_model` passes:

```python
{
    **cfg,
    'tokenizer': tokenizer,
}
```

### Dataloaders

Registry: `registry.dataloaders`

Expected return: Composer `DataSpec`.

Builder convention: dataloader builders receive a tokenizer, device batch size, dataset/config kwargs, and loader kwargs. Full data-loader workflows belong elsewhere; here, only inspect names and constructor contracts.

### Callbacks

Registries: `registry.callbacks` and `registry.callbacks_with_config`

- Standard callbacks receive kwargs directly.
- `callbacks_with_config` receive an extra reserved `train_config` kwarg injected by `build_callback`.
- If a callback name is in `callbacks_with_config`, it takes precedence over `callbacks` in `build_callback`.

### Optimizers

Registry: `registry.optimizers`

`build_optimizer` injects `params` from the model. Config must not include `params`.

Advanced config handled before registry construction:

```yaml
optimizer:
  name: decoupled_lionw
  lr: 1.0e-4
  disable_grad: ["norm", "bias"]
  param_groups:
  - param_str_match: "norm"
    lr: 1.0e-5
    weight_decay: 0.0
```

`disable_grad` sets matching parameters to `requires_grad=False`. `param_groups` create ordered parameter groups by regex match.

### Schedulers, algorithms, metrics, loggers

These registries pass kwargs through to constructors. Unknown kwargs normally surface as Python constructor `TypeError`s.

### Tokenizers

Registry: `registry.tokenizers`

If `tokenizer.name` is registered, LLM Foundry constructs that tokenizer. Otherwise it calls Hugging Face `AutoTokenizer.from_pretrained`, which may download.

### Config transforms

Registry: `registry.config_transforms`

Transforms take and return a config dict. The built-in transform is `update_batch_size_info`.

## Registry CLI caveats

- CLI import must succeed before registry commands work. Missing base dependencies, flash-attn undefined symbols, or incompatible torch/flash wheels can prevent even `llmfoundry registry get` from starting.
- Registry output only reflects the active Python environment. If an extension is installed in a different environment or omitted from the platform image, it will not appear.
- Entry points can be cached by Python packaging metadata; reinstall or restart the process after changing extension package metadata.
