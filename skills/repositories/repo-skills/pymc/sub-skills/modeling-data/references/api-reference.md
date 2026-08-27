# PyMC modeling-data API reference

Use this for PyMC 6.3.0 model/data signatures and practical notes.

| API | Signature | Use |
| --- | --- | --- |
| `pm.Model` | `pm.Model(*args, **kwargs)`; constructor accepts model options such as `name`, `coords`, and `check_bounds` through keyword arguments | Create a mutable model context. |
| `pm.Data` | `(name, value, *, dims=None, coords=None, infer_dims_and_coords=False, model=None, **kwargs)` | Register mutable shared data. Values may change in value/shape but not rank. |
| `pm.set_data` | `(new_data, model=None, *, coords=None)` | Update one or more `pm.Data` containers by name. |
| `pm.Deterministic` | `(name, var, model=None, dims=None)` | Register a derived expression in outputs. |
| `pm.Potential` | `(name, var, model=None, dims=None)` | Add an arbitrary log-probability term. |
| `pm.do` | `(model, vars_to_interventions, *, make_interventions_shared=True, prune_vars=False) -> Model` | Return a cloned model with variables replaced by intervention values/expressions. |
| `pm.observe` | `(model, vars_to_observations) -> Model` | Return a cloned model where free RVs or deterministics are conditioned as observed. |

Important model attributes: `named_vars`, `free_RVs`, `observed_RVs`, `basic_RVs`, `deterministics`, `potentials`, `data_vars`, `coords`, `dim_lengths`, `named_vars_to_dims`, `rvs_to_values`, and `rvs_to_transforms`.

Use `model.initial_point(random_seed=None)` to obtain a point keyed by value-variable names. Use `model.compile_logp(vars=None, jacobian=True, sum=True)` to evaluate total or factor logp at that point. Use `model.compile_fn(outs, inputs=None, point_fn=True, **kwargs)` for expression checks; replace RVs by value variables before compiling expressions that depend on RVs.

`model.to_graphviz(var_names=None, formatting="plain", save=None, figsize=None, dpi=300)` needs optional Python and system Graphviz. If unavailable, inspect textual registries and `model.named_vars_to_dims`.

Regular `coords`/`dims` provide shape metadata and output labels. Experimental `pymc.dims` carries dimension labels through operations with xtensor variables and may break across releases.
