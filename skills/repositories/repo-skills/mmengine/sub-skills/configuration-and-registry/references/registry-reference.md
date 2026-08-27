# MMEngine Registry Reference

This reference covers `Registry`, registration, `build_from_cfg`, default arguments, default scopes, and cross-library routing.

## Core APIs

| Task | API | Notes |
| --- | --- | --- |
| Create a registry | `Registry(name, build_func=None, parent=None, scope=None, locations=[])` | If `scope` is omitted, MMEngine infers it from the caller package; pass `scope` explicitly in small projects and examples. |
| Register | `registry.register_module(name=None, force=False, module=None)` | Works as `@registry.register_module()` or `registry.register_module(module=Cls)`. A duplicate name raises unless `force=True`. |
| Lookup | `registry.get(key)` | `key` may be unscoped, local-scoped, or `scope.Name`. Missing keys return `None`. |
| Build | `registry.build(cfg, *args, **kwargs)` | Calls the registry build function, usually `build_from_cfg`. |
| Direct build | `build_from_cfg(cfg, registry, default_args=None)` | `cfg` and/or `default_args` must contain `type`. `cfg` wins over `default_args` on conflicts. |
| Default scope | `init_default_scope(scope)` | Sets the current global registry scope for code that builds through parent or root registries. |
| Inspect scope | `DefaultScope.get_current_instance()` | Returns `None` if no default scope exists; otherwise has `.scope_name`. |

Import pattern:

```python
from mmengine.registry import Registry, build_from_cfg, DefaultScope, init_default_scope
```

MMEngine also exposes many root registries, such as `MODELS`, `HOOKS`, `DATASETS`, `TRANSFORMS`, `METRICS`, `OPTIMIZERS`, `OPTIM_WRAPPERS`, `PARAM_SCHEDULERS`, `VISUALIZERS`, `VISBACKENDS`, `LOG_PROCESSORS`, `FUNCTIONS`, `INFERENCERS`, `RUNNERS`, and loop registries. Route the object-specific contract to the sibling sub-skill that owns it.

## Minimal Registry Pattern

```python
from mmengine.registry import Registry

ACTIVATIONS = Registry('activation', scope='toy')

@ACTIVATIONS.register_module()
class ReLU:
    def __init__(self, inplace=False):
        self.inplace = inplace

obj = ACTIVATIONS.build(dict(type='ReLU', inplace=True))
```

The `type` value can be:

- A registered string key, such as `'ReLU'`.
- A scope-qualified key, such as `'toy.ReLU'`.
- A callable class or function object, when the config is created in Python code rather than plain text.

Registries can register functions as well as classes:

```python
FUNCTIONS = Registry('function', scope='toy')

@FUNCTIONS.register_module()
def make_value(x=1):
    return x

value = FUNCTIONS.build(dict(type='make_value', x=3))
```

## Registration Mechanics

A registered item is available only after its module has been imported. Trigger registration by one of these routes:

1. Define the module in a package listed in the registry's `locations`; MMEngine imports these locations lazily during build.
2. Import the Python module manually before building.
3. Add `custom_imports = dict(imports=['package.module'], allow_failed_imports=False)` to the config and load with `Config.fromfile(..., import_custom_modules=True)`.

Use explicit names or aliases when needed:

```python
@REGISTRY.register_module(name='alias_name')
class LongClassName:
    pass

REGISTRY.register_module(module=LongClassName, name=['LongClassName', 'alias'])
```

Avoid `force=True` unless intentionally replacing an existing registration; duplicate registration usually indicates repeated imports, reused names, or a stale interactive session.

## `build_from_cfg` Contract

`build_from_cfg(cfg, registry, default_args=None)` requires:

- `cfg` is `dict`, `ConfigDict`, or `Config`.
- `registry` is a `Registry`.
- At least one of `cfg` or `default_args` contains `type`.
- `type` is a string key or callable.
- Remaining keys become constructor or function keyword arguments.

Example with defaults:

```python
cfg = dict(type='ResNet', depth=50)
model = build_from_cfg(cfg, MODELS, default_args=dict(stages=4))
```

If both `cfg` and `default_args` define the same key, the `cfg` value wins. This is useful for shared defaults:

```python
default_args = dict(type='ToyLayer', width=128, activation='relu')
layer = LAYERS.build(dict(width=256), default_args=default_args)
```

`build_from_cfg` pops `_scope_` before constructing. That key temporarily switches registry routing for the build call and is not passed to the constructor.

## Parent, Child, and Sibling Scopes

A child registry can inherit lookup from a parent:

```python
from mmengine.registry import MODELS as MMENGINE_MODELS, Registry

MODELS = Registry('model', parent=MMENGINE_MODELS, scope='myproj')
```

Lookup rules:

- Unscoped `type='Name'` first searches the current registry, then parent/ancestor registries.
- Scoped `type='mmengine.Name'` routes to the registry node under that scope when present.
- Sibling lookup requires a prefix, such as `type='otherproj.Name'`, unless `_scope_` or the default scope switches the build context.

Use `_scope_` for a config subtree whose nested unscoped types belong to another package:

```python
model = dict(
    _scope_='mmdet',
    type='YOLOX',
    backbone=dict(type='CSPDarknet'),
)
```

This is often paired with `custom_imports`:

```python
custom_imports = dict(imports=['mmdet.models'], allow_failed_imports=False)
```

Use `init_default_scope('myproj')` when code builds through an MMEngine root registry but should find objects from your child package:

```python
from mmengine.registry import init_default_scope

init_default_scope('myproj')
```

This matters when a parent or root builder, such as a runner or root model registry, is responsible for constructing child-package objects.

## Cross-Library Routing Checklist

When `type='otherpkg.SomeClass'` or `_scope_='otherpkg'` fails:

1. Confirm the target package is installed and importable.
2. Confirm its registry module or explicit `custom_imports` has been imported.
3. Confirm the target registry is a child or sibling in the same registry tree.
4. Confirm the type key is registered under the expected name, including aliases.
5. Confirm the right builder registry is used; building a dataset item through `MODELS` cannot find `TRANSFORMS` entries.
6. Confirm `_scope_` is at the config dict level that contains `type`, not only at an unrelated parent.

## Integration with Config Files

Config files normally carry registry specs as plain dicts:

```python
model = dict(type='ToyModel', backbone=dict(type='ToyBackbone', depth=18))
```

A caller then chooses the correct registry or high-level builder:

```python
model = MODELS.build(cfg.model)
```

For full runner configs, keep the config syntax here but route training loop placement and `Runner.from_cfg` usage to `../runner-and-training/SKILL.md`.
