# Python API for DeePMD-kit Inference

This reference distills the Python inference contracts for DeePMD-kit energy models and model-deviation workflows.

## Imports and Model Loading

```python
from deepmd.infer import DeepPot, DeepPotential, calc_model_devi
```

Use `DeepPot` for potential-energy models. `DeepPotential` is a broader alias-style entry point in some DeePMD workflows, but `DeepPot` is the direct energy-model class covered here.

```python
pot = DeepPot(model_file, auto_batch_size=True, neighbor_list=None)
```

Constructor contract:

| Argument | Meaning | Practical guidance |
| --- | --- | --- |
| `model_file` | Frozen model path, checkpoint path supported by the selected backend, or built-in pretrained model name. | Prefer explicit backend CLI flags outside Python when suffix detection is ambiguous. |
| `auto_batch_size` | `True`, integer initial batch size, or DeePMD auto-batch object. | Keep `True` for general inference; use an integer only to tune memory. |
| `neighbor_list` | ASE-compatible neighbor list object. | TensorFlow-oriented advanced path; otherwise leave `None`. |
| `**kwargs` | Backend-specific options such as a multi-task head where supported. | Inspect the installed API before relying on backend-specific keywords. |

Load models once and reuse the object. Repeated construction in a loop can grow TensorFlow/PyTorch memory.

## Core Shape Contract

`DeepPot` normalizes inputs internally, so flattened and structured coordinate/cell arrays are both acceptable if their total sizes match.

| Input | Non-mixed shape | Mixed-type shape | Notes |
| --- | --- | --- | --- |
| `coords` | `(nframes, natoms, 3)` or `(nframes, natoms * 3)` | same coordinate shapes | Values are Cartesian coordinates. |
| `cells` | `(nframes, 3, 3)` or `(nframes, 9)` | same cell shapes | Use `None` for non-periodic systems. |
| `atom_types` | `(natoms,)` | `(nframes, natoms)` | Integer indices in model `type_map` order. |
| `fparam` | `(nframes, dim_fparam)` or `(dim_fparam,)` | same | Required only when `pot.get_dim_fparam() > 0`. |
| `aparam` | `(nframes, natoms, dim_aparam)`, `(natoms, dim_aparam)`, or `(dim_aparam,)` | same conceptual dimensions | Required only when `pot.get_dim_aparam() > 0`. |

The helper script `../scripts/deeppot_input_shapes.py` prints a minimal NumPy skeleton for these arrays without loading a model.

## Energy, Force, and Virial

Signature:

```python
energy, force, virial = pot.eval(
    coords,
    cells,
    atom_types,
    atomic=False,
    fparam=None,
    aparam=None,
    mixed_type=False,
)
```

Outputs when `atomic=False`:

| Output | Shape | Meaning |
| --- | --- | --- |
| `energy` | `(nframes, 1)` | Total energy per frame. |
| `force` | `(nframes, natoms, 3)` | Cartesian force on each atom. |
| `virial` | `(nframes, 9)` | Flattened virial tensor per frame. |

Outputs when `atomic=True` add:

| Output | Shape | Meaning |
| --- | --- | --- |
| `atomic_energy` | usually `(nframes, natoms, 1)` | Atomic energy contribution; for spin models this may cover real atoms only. |
| `atomic_virial` | `(nframes, natoms, 9)` | Per-atom virial tensor. |

Some model classes may append spin-force/mask or Hessian outputs when the backend model exposes them. When writing robust code, unpack the first three outputs and inspect `len(result)` before assuming optional outputs.

## Non-Periodic Inference

Use `cells=None` for isolated/non-periodic systems:

```python
energy, force, virial = pot.eval(coord, None, atype)
```

Do not use a zero matrix as a non-PBC sentinel. A numeric cell still means the model should treat the frame as periodic after input normalization.

## Type Map and Atom Types

Always map species labels through the model type map:

```python
type_map = pot.get_type_map()  # for example ["O", "H"]
type_to_index = {symbol: index for index, symbol in enumerate(type_map)}
atype = [type_to_index[symbol] for symbol in symbols]
```

If a data system has `type.raw`, do not assume it matches a new model. Confirm that the integer indices and element order agree with `pot.get_type_map()` or `dp show MODEL type-map`.

## Optional Frame and Atomic Parameters

Check dimensions before passing `fparam` or `aparam`:

```python
if pot.get_dim_fparam() > 0:
    fparam = np.asarray(frame_params).reshape(nframes, pot.get_dim_fparam())
else:
    fparam = None

if pot.get_dim_aparam() > 0:
    aparam = np.asarray(atom_params).reshape(nframes, natoms, pot.get_dim_aparam())
else:
    aparam = None
```

Broadcasting accepted by DeePMD-kit:

- `fparam` can be one vector of shape `(dim_fparam,)` and will be tiled over frames.
- `aparam` can be one vector of shape `(dim_aparam,)` and will be tiled over frames and atoms.
- `aparam` can be shape `(natoms, dim_aparam)` and will be tiled over frames.

## Descriptor Evaluation

Signature:

```python
descriptor = pot.eval_descriptor(
    coords,
    cells,
    atom_types,
    fparam=None,
    aparam=None,
    mixed_type=False,
    dtype="native",
)
```

| Output | Shape | Notes |
| --- | --- | --- |
| `descriptor` | `(nframes, natoms, ndesc)` | Per-atom local-environment representation. |

`dtype` may be `"fp32"`, `"fp64"`, or `"native"`. Use `"native"` when comparing with model/backend-native values; use `"fp32"` or `"fp64"` when a downstream tool needs a fixed precision.

## Embedding Evaluation

Signature:

```python
descriptor, atomic_feature, structural_feature = pot.eval_embedding(
    coords,
    cells,
    atom_types,
    fparam=None,
    aparam=None,
    mixed_type=False,
    dtype="fp32",
)
```

| Output | Shape | Meaning |
| --- | --- | --- |
| `descriptor` | `(nframes, natoms, dim_descriptor)` | Local-environment representation. |
| `atomic_feature` | `(nframes, natoms, dim_hidden)` | Activation after the last fitting hidden layer. |
| `structural_feature` | `(nframes, dim_hidden)` | Atom-summed structure feature. |

Embedding extraction is PyTorch-focused and may raise `NotImplementedError` for models that do not support it. Spin models are not a supported embedding target. For CLI embedding output, use `dp embed` and read the HDF5 file.

## Model Deviation API

Signature:

```python
deviation = calc_model_devi(
    coord,
    box,
    atype,
    models,
    fname=None,
    frequency=1,
    mixed_type=False,
    fparam=None,
    aparam=None,
    real_data=None,
    atomic=False,
    relative=None,
    relative_v=None,
)
```

Key requirements:

- `coord`: coordinates for all frames, accepted in the same flattenable shape family as `DeepPot.eval`.
- `box`: cells for all frames, or `None` for non-PBC.
- `atype`: atom type indices; shape `(natoms,)` unless `mixed_type=True`.
- `models`: list of already-loaded `DeepPot` objects, not file paths.
- `relative`: force relative-deviation level parameter.
- `relative_v`: virial relative-deviation level parameter.
- `atomic=True`: appends per-atom force deviation columns.

Returned table when `atomic=False` has columns:

1. `step`
2. `max_devi_v`
3. `min_devi_v`
4. `avg_devi_v`
5. `max_devi_f`
6. `min_devi_f`
7. `avg_devi_f`
8. `devi_e`

With `fname`, DeePMD-kit appends the table to a text file with a header. With `real_data`, it calculates RMS real error against supplied energy/force/virial arrays instead of ensemble-only deviation.

## Four-Model Deviation Pattern

```python
from deepmd.infer import DeepPot, calc_model_devi

model_paths = ["graph.000.pb", "graph.001.pb", "graph.002.pb", "graph.003.pb"]
models = [DeepPot(path, auto_batch_size=True) for path in model_paths]

# Optionally check type maps before evaluation.
type_maps = [model.get_type_map() for model in models]
if any(type_map != type_maps[0] for type_map in type_maps):
    raise ValueError(f"model type_map mismatch: {type_maps}")

deviation = calc_model_devi(
    coord,
    cell,
    atype,
    models,
    atomic=True,
    relative=0.05,
    relative_v=0.05,
)
```

This pattern supports active-learning or trajectory loops by keeping `models` alive and changing only `coord`, `cell`, and optional parameters per batch.

## Metadata Methods Useful Before Inference

| Method | Use |
| --- | --- |
| `get_type_map()` | Map element symbols to integer atom types. |
| `get_rcut()` | Check whether a cell/box is large enough for the model cutoff. |
| `get_ntypes()` | Validate type index range. |
| `get_dim_fparam()` | Decide whether frame parameters are required. |
| `get_dim_aparam()` | Decide whether atomic parameters are required. |
| `has_default_fparam()` | Detect whether a model has built-in frame parameters. |

## Minimal Shape Conversion Example

```python
import numpy as np
from deepmd.infer import DeepPot

symbols = ["O", "H", "H"]
coords_xyz = np.array([
    [[0.0, 0.0, 0.0], [0.0, 0.76, 0.58], [0.0, -0.76, 0.58]],
])
cell_3x3 = np.tile(np.eye(3) * 12.0, (coords_xyz.shape[0], 1, 1))

pot = DeepPot("model.pth")
type_to_index = {symbol: i for i, symbol in enumerate(pot.get_type_map())}
atype = np.array([type_to_index[symbol] for symbol in symbols], dtype=np.int32)

energy, force, virial = pot.eval(
    coords_xyz.reshape(coords_xyz.shape[0], -1),
    cell_3x3.reshape(coords_xyz.shape[0], 9),
    atype,
)
```

For non-PBC, replace the cell argument with `None`.
