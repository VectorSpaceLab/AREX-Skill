# Modules and Parameters

This reference covers `pyro.param`, the global parameter store, ordinary
`torch.nn.Module` registration, and `pyro.nn` module primitives. For SVI or
optimizer loop details, route to `../../svi-and-autoguides/SKILL.md`.

## Mental model: parameter state is global unless made local

By default Pyro has one process-global `ParamStoreDict`, accessed through
`pyro.get_param_store()` and used by `pyro.param`, `pyro.module`, and
`PyroModule` attribute access. This has two consequences:

1. The first call to `pyro.param(name, init_tensor, ...)` creates the parameter.
   Later calls with the same name ignore new initializers and return the stored
   value.
2. Separate experiments in the same Python process can leak parameters into one
   another unless the store is cleared, scoped, or avoided with module-local
   parameters.

Start independent runs with:

```python
pyro.clear_param_store()
```

Use local scoping when multiple models need independent parameter namespaces in
one process:

```python
store = pyro.get_param_store()

with store.scope() as state_a:
    # train/evaluate model A
    pass

with store.scope() as state_b:
    # train/evaluate model B with a clean store
    pass

with store.scope(state_a):
    # temporarily restore model A's parameters
    pass
```

## `pyro.param` and constraints

Signature:

```python
pyro.param(name, init_tensor=None, constraint=constraints.real, event_dim=None)
```

Usage:

```python
from torch.distributions import constraints

loc = pyro.param("loc", torch.zeros(()))
scale = pyro.param("scale", torch.ones(()), constraint=constraints.positive)
probs = pyro.param("probs", torch.ones(3) / 3,
                   constraint=constraints.simplex, event_dim=1)
```

Key details:

- `init_tensor` may be a tensor or a lazy zero-argument callable. Lazy callables
  are evaluated only when the parameter name is first created.
- If `init_tensor` is omitted, the parameter must already exist or lookup fails.
- The returned value is constrained/user-facing. The unconstrained optimizer
  tensor is available through `pyro.param(...).unconstrained()` when needed.
- Internally constrained parameters are stored in unconstrained space using
  PyTorch transforms. Do not manually optimize the constrained view unless you
  know the transform behavior.
- `event_dim` tells Pyro how many rightmost dimensions are not batch dimensions.
  For parameters inside subsampled plates, dimensions left of `event_dim` may be
  subsampled. If omitted, all dimensions are treated as event dimensions and no
  plate subsampling is applied to the parameter.

## ParamStoreDict operations

`store = pyro.get_param_store()` returns a dict-like global store. Useful
operations:

| Operation | Use |
|---|---|
| `store.clear()` or `pyro.clear_param_store()` | Remove all parameters and constraints. |
| `len(store)`, `name in store`, `store.keys()` | Inspect registered parameter names. |
| `store.items()` / `store.values()` | Iterate constrained parameter values. |
| `store.named_parameters()` | Iterate unconstrained tensors used by optimizers. |
| `store[name]` | Get the constrained value for a parameter. |
| `store[name] = constrained_value` | Set an existing or new parameter in constrained space, preserving any existing constraint or defaulting to real. |
| `del store[name]` | Remove one parameter and its constraint. |
| `store.match(regex)` | Return constrained parameters whose names match a regex. |
| `store.get_state()` / `store.set_state(state)` | Snapshot and restore in-memory state. |
| `store.save(filename)` / `store.load(filename, map_location=None)` | Save/load parameter state with `torch.save` / `torch.load`. |
| `store.scope(state=None)` | Context manager that swaps in an isolated parameter state, then restores the old global store. |

Save/load cautions:

```python
store = pyro.get_param_store()
store.save("params.pt")
pyro.clear_param_store()
store.load("params.pt", map_location="cpu")
```

- Loading state does not automatically update an already-created ordinary
  `torch.nn.Module`. If using `pyro.module`, call it after loading with
  `update_module_params=True` when you want module parameters overwritten by the
  loaded ParamStore values.
- With `PyroModule`, `torch.load` values can be overridden by the current global
  parameter store. It is safest to call `pyro.clear_param_store()` before
  loading or constructing a replacement module when global params are enabled.

## `pyro.module` for ordinary `nn.Module`

Signature:

```python
pyro.module(name, nn_module, update_module_params=False)
```

`pyro.module` registers all `requires_grad=True` parameters of an ordinary
`torch.nn.Module` in the global parameter store under names derived from the
Pyro module name and PyTorch parameter name. It returns the module.

```python
net = torch.nn.Linear(3, 1)
pyro.module("net", net)
# Parameter-store names use an internal module separator, for example a weight
# parameter is stored under a module-qualified name rather than the bare
# PyTorch attribute name.
```

Use `update_module_params=True` after loading a ParamStore when the stored value
should replace the module object's current parameter tensors:

```python
pyro.get_param_store().load("params.pt", map_location="cpu")
pyro.module("net", net, update_module_params=True)
```

Do not pass a class constructor to `pyro.module`; pass an initialized module
instance. New code that needs Bayesian module attributes should usually prefer
`PyroModule`, `PyroParam`, and `PyroSample`.

## PyroModule basics

Imports:

```python
from pyro.nn import PyroModule, PyroParam, PyroSample, pyro_method
from pyro.nn.module import clear as clear_pyro_module, to_pyro_module_
```

A `PyroModule` is a `torch.nn.Module` whose attribute access can trigger Pyro
primitive statements.

```python
class Model(PyroModule):
    def __init__(self):
        super().__init__()
        self.loc = torch.nn.Parameter(torch.tensor(0.0))
        self.scale = PyroParam(torch.tensor(1.0),
                               constraint=constraints.positive)
        self.z = PyroSample(lambda self: dist.Normal(self.loc, self.scale))

    def forward(self, data=None):
        z = self.z                     # triggers pyro.sample("z", ...)
        with pyro.plate("data", len(data)):
            return pyro.sample("obs", dist.Normal(z, self.scale), obs=data)
```

Attribute behavior:

- Reading a `torch.nn.Parameter` on an active `PyroModule` call triggers a
  `pyro.param` site.
- Reading a `PyroParam` triggers a constrained `pyro.param` site.
- Reading a `PyroSample` triggers a `pyro.sample` site. If the prior callable
  returns a tensor rather than a distribution, Pyro records it as a
  deterministic site.
- `PyroSample` values are cached within a single `.__call__()` / `forward()`
  invocation so repeated reads in one call refer to the same sample site value.
  They are not cached across separate calls.
- Public methods other than `forward()` that read Pyro-managed attributes should
  be decorated with `@pyro_method` so Pyro effects and per-call caching are
  active.

## PyroParam patterns

Eager attribute:

```python
m = PyroModule()
m.scale = PyroParam(torch.ones(4), constraint=constraints.positive, event_dim=1)
```

Lazy attribute:

```python
m.weight = PyroParam(lambda: torch.randn(3, 2))
```

Decorator style:

```python
class M(PyroModule):
    @PyroParam(constraint=constraints.positive, event_dim=1)
    def scale(self):
        return torch.ones(4)
```

Notes:

- Pyro stores constrained parameters as an unconstrained `*_unconstrained`
  PyTorch parameter inside the module.
- Assigning a tensor to an existing `PyroParam` attribute updates the
  unconstrained value through the constraint transform.
- Delete and recreate a `PyroParam` if you need to replace its constraint or
  reset its declaration.

## PyroSample patterns

Independent prior:

```python
m.weight = PyroSample(dist.Normal(0.0, 1.0).expand([out_dim, in_dim]).to_event(2))
```

Prior depending on module attributes:

```python
m.bias = PyroSample(lambda self: dist.Normal(self.loc, self.scale))
```

Deterministic dependent value:

```python
class M(PyroModule):
    @PyroSample
    def squared(self):
        return self.latent ** 2
```

Mixin/dynamic conversion patterns:

```python
class BayesianLinear(torch.nn.Linear, PyroModule):
    def __init__(self, in_features, out_features):
        super().__init__(in_features, out_features)
        self.weight = PyroSample(
            lambda self: dist.Normal(0.0, 1.0)
            .expand([self.out_features, self.in_features])
            .to_event(2)
        )

layer = PyroModule[torch.nn.Linear](3, 2)
```

`PyroModule[...]` creates a Pyro-aware mixin type for one module class. It does
not recursively convert already-existing submodules unless you wrap/convert
those submodules too.

To convert an existing module in place:

```python
to_pyro_module_(net, recurse=True)
for module in net.modules():
    for name, value in list(module.named_parameters(recurse=False)):
        setattr(module, name,
                PyroSample(dist.Normal(0.0, 1.0)
                           .expand(value.shape)
                           .to_event(value.dim())))
```

## Module names and global parameter synchronization

A root `PyroModule(name="...")` uses that name as the prefix for its Pyro sites;
submodules derive nested names from their parent. If the root name is empty,
site names are the attribute names such as `x`, `p.w`, or module-qualified names
for ordinary child modules.

Important global-store behavior:

- Two `PyroModule` objects with the same Pyro names synchronize with the same
  global parameter-store entries. A newly created module can unexpectedly reuse
  values from a previously deleted module.
- To avoid persistence, call `pyro.clear_param_store()` before constructing a
  fresh model, or call `pyro.nn.module.clear(mod)` before deleting a module when
  global params are enabled.
- If multiple `PyroModule` instances appear in one model or guide, include them
  under one root `PyroModule` so nested names are unique and the Pyro context is
  shared.
- Do not call `pyro.module()` on a `PyroModule`; attribute access already emits
  the needed parameter/module sites.

## `module_local_params`

`pyro.settings.set(module_local_params=True)` makes `PyroModule` parameters
behave like ordinary `torch.nn.Parameter` state local to each module, rather
than sharing values by name through the global ParamStore. This is recommended
when models can be written without standalone global `pyro.param()` calls and
when using vanilla PyTorch optimizer patterns over an ELBO module.

Use a context or set it near process startup:

```python
with pyro.settings.context(module_local_params=True):
    model = Model()
    guide = AutoNormal(model)  # inference details belong to SVI/autoguide docs
```

Caveats:

- `module_local_params=True` applies to `PyroModule` attribute-triggered params;
  standalone global `pyro.param(...)` statements inside a `PyroModule` forward
  are not supported and can raise `NotImplementedError` when validation is on.
- In local mode, `pyro.get_param_store().keys()` can remain empty even after a
  module has initialized parameters. Inspect `model.named_parameters()` or
  `model.named_pyro_params()` instead.
- In global mode, a second guide/model with the same names may initialize from
  the first one's stored values. This can be useful for loading but confusing
  during repeated experiments.

## Optimizer interaction

With Pyro optimizers and `SVI`, the optimizer gets unconstrained parameter
tensors from the ParamStore or from the relevant module state; the SVI sub-skill
owns the training loop details. Modeling-level implications:

- Define all parameters with correct constraints before creating/running an
  optimizer.
- If using a PyTorch optimizer over an ELBO module, run one tiny forward/loss
  call first so autoguide and PyroModule parameters are initialized, then create
  the optimizer over `loss_fn.parameters()`.
- If using `module_local_params=True`, the global ParamStore is not the source
  of truth for module parameters; saving/loading should use ordinary
  `torch.save`/`torch.load` patterns or the ELBO/module state rather than
  relying on `pyro.get_param_store().save()`.
- If using global params, `pyro.get_param_store().save()` and `.load()` preserve
  parameter values and constraints, but remember to clear stale state before
  loading into a different model shape or name layout.

## Serialization choices

Choose based on where parameter state lives:

| Situation | Preferred approach |
|---|---|
| Standalone `pyro.param` or old `pyro.module` workflow | `pyro.get_param_store().save()` / `.load()`; then re-register modules if needed. |
| `PyroModule` with global params | Clear the ParamStore before `torch.load`; or use ParamStore save/load deliberately and rebuild modules with matching names. |
| `PyroModule` with `module_local_params=True` | Use ordinary PyTorch module serialization/checkpointing of the module/ELBO state. |
| Multiple independent models in one process | Use `ParamStoreDict.scope()` or `module_local_params=True`, plus explicit seeding/clearing. |
