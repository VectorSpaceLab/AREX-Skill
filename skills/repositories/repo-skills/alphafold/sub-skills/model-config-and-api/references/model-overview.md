# Model Overview

This reference summarizes AlphaFold package version 2.3.2 model presets, configuration objects, runner concepts, parameter loading, and backend assumptions for agents working programmatically with `alphafold.model`.

## Preset Selection

AlphaFold exposes user-facing preset groups through `alphafold.model.config.MODEL_PRESETS`:

| Preset | Model names | Use when |
| --- | --- | --- |
| `monomer` | `model_1` through `model_5` | Standard single-chain structure prediction ranked by mean pLDDT. |
| `monomer_casp14` | Alias of `monomer` | Reproduce CASP14-style monomer model set naming. It is not a separate weight family in this package. |
| `monomer_ptm` | `model_1_ptm` through `model_5_ptm` | Single-chain prediction when pTM/PAE confidence heads are needed. |
| `multimer` | `model_1_multimer_v3` through `model_5_multimer_v3` | Protein-complex prediction with multimer features, ipTM/pTM ranking, and v2.3.0 multimer weights. |

Selection rules:

- Choose `monomer_ptm` rather than `monomer` when the downstream task needs predicted aligned error or pTM for a monomer.
- Choose `multimer` only when the input represents a complex and the data pipeline produced multimer features such as chain identifiers and paired/unpaired MSA features.
- Do not substitute old multimer parameter filenames for the v3 preset names. The active `multimer` preset expects `params_model_1_multimer_v3.npz` through `params_model_5_multimer_v3.npz`.
- The config module still defines config differences for historical `model_N_multimer` and `model_N_multimer_v2` names, but those names are not in `MODEL_PRESETS['multimer']` and should not be used as the default v2.3.2 workflow.

## v2.3 Multimer Defaults

AlphaFold v2.3.0 made the v3 multimer weights the default multimer family. The technical note describes fine-tuned AlphaFold-Multimer weights with a newer training cutoff, larger-complex emphasis, and increased training crop/chain coverage. In config terms:

- `CONFIG_MULTIMER.model.global_config.multimer_mode` is `True`.
- The default v3 multimer base uses `num_recycle = 20`, `num_ensemble_eval = 1`, `recycle_early_stop_tolerance = 0.5`, and `resample_msa_in_recycling = True`.
- Multimer v3 starts with `num_msa = 508` and `num_extra_msa = 2048`; `model_4_multimer_v3` and `model_5_multimer_v3` override `num_extra_msa` to `1152`.
- Historical multimer/v2 config update functions use `num_msa = 252`, `num_extra_msa = 1152`, and disable fused triangle multiplication projection weights. That is why old multimer names should not be treated as interchangeable with v3 weight names.

## Config Objects

There are two supported config access patterns:

- `model_config(model_name)` returns a mutable `ml_collections.ConfigDict` generated from the monomer or multimer base config plus flattened differences for the requested model name.
- `get_model_config(model_name, frozen=True)` returns an `AlphaFoldConfig` dataclass tree derived from the same defaults and differences. With `frozen=True`, assignment raises a dataclass frozen-instance error until the config is temporarily unfrozen.

Recommended edit patterns:

```python
from alphafold.model import config

cfg = config.model_config('model_1_ptm')
with cfg.unlocked():
  cfg.model.num_recycle = 6
  cfg.data.eval.num_ensemble = 1
```

```python
from alphafold.model import config

dataclass_cfg = config.get_model_config('model_1_multimer_v3')
with dataclass_cfg.unfreeze() as cfg:
  cfg.model.num_recycle = 3
```

Use preset-derived configs first, then apply minimal edits. Avoid constructing an entire config from scratch unless you are porting a fully understood AlphaFold variant.

## RunModel Lifecycle

`alphafold.model.model.RunModel` is a thin container around a Haiku-transformed JAX model:

1. Construct it with a model config and optional Haiku parameters.
2. Use `process_features(raw_features, random_seed)` to convert raw monomer pipeline features into model-ready features. In multimer mode this method returns `raw_features` unchanged because multimer feature processing happens upstream.
3. Use `predict(feat, random_seed)` to initialize parameters if missing, run the JIT-compiled model, block until JAX outputs are ready, and attach confidence metrics.
4. Use `eval_shape(feat)` only when you intentionally want JAX shape evaluation; it can still initialize parameters and touch JAX compilation paths.

Safe agent default: inspect configs and signatures without constructing `RunModel` or running `predict`, unless the user explicitly requests runtime model execution and has confirmed weights, data, backend, and resource constraints.

## Parameter Loading

`alphafold.model.data.get_model_haiku_params(model_name, data_dir)` opens:

```text
<data_dir>/params/params_<model_name>.npz
```

and converts flat NumPy arrays to a Haiku parameter tree. It does not download, search, or validate a complete parameter bundle. Common implications:

- `data_dir` is the database/model-parameter root, not the `params` directory itself.
- `model_name` must match the desired config name exactly, including `_ptm` or `_multimer_v3` suffixes.
- A missing file fails before inference; an incompatible file can fail later with parameter shape/key mismatches when the Haiku model is applied.
- Loading parameters is more expensive than config inspection; do not use it for routine preset discovery.

## Dependency Roles

AlphaFold model-layer imports are sensitive to pinned scientific packages:

| Dependency | Model-layer role |
| --- | --- |
| `jax` / `jaxlib` | JIT compilation, random keys, array operations, geometry helpers, model execution. Versions must be compatible with each other. |
| `dm-haiku` | Transforms model modules and stores parameter trees. |
| `ml-collections` | Mutable `ConfigDict` configuration objects. |
| `tensorflow-cpu` | Monomer `features.np_example_to_features` uses TensorFlow v1 graph/session APIs for preprocessing. |
| `numpy` | Feature arrays, parameter `.npz` loading, and many helper APIs. |
| `ml-dtypes` | Transitive numeric dtype dependency that must remain compatible with JAX/TensorFlow pins. |

Known package facts for this skill: AlphaFold package version `2.3.2`, `jax==0.4.26`, `numpy==1.24.3`, `tensorflow-cpu==2.16.1`, `dm-haiku==0.0.12`, `ml-collections==0.1.0`, and a repaired inspection environment used `jaxlib==0.4.26` with `ml-dtypes==0.3.2`. Treat those as compatibility clues, not as a license to mutate a user's environment without confirmation.

## Numerical Helper Scope

The model package includes reusable numerical helpers, but they are lower-level than prediction outputs:

- `alphafold.model.lddt.lddt` computes approximate lDDT from predicted and true point arrays plus a mask.
- `alphafold.model.all_atom` contains atom14/atom37 conversion, torsion-frame, structural violation, ambiguity-renaming, and FAPE helpers used by structure-module logic and tests.
- `alphafold.model.geometry.vector.Vec3Array`, `rotation_matrix.Rot3Array`, and `rigid_matrix_vector.Rigid3Array` represent vector, rotation, and rigid-transform operations as JAX-friendly struct-of-arrays objects.

For interpreting emitted confidence JSON or ranked output artifacts, route to `../outputs-and-confidence/` instead of reimplementing output interpretation from model internals.
