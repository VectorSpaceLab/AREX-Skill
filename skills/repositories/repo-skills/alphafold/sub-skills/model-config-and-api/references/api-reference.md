# Model API Reference

This reference lists the programmatic AlphaFold model APIs most useful to future agents. Use it for lightweight inspection, config edits, and diagnostics; do not treat these APIs as permission to run full inference automatically.

## `alphafold.model.config`

### Preset constants

```python
MODEL_PRESETS = {
    'monomer': ('model_1', 'model_2', 'model_3', 'model_4', 'model_5'),
    'monomer_ptm': ('model_1_ptm', 'model_2_ptm', 'model_3_ptm', 'model_4_ptm', 'model_5_ptm'),
    'multimer': ('model_1_multimer_v3', 'model_2_multimer_v3', 'model_3_multimer_v3', 'model_4_multimer_v3', 'model_5_multimer_v3'),
    'monomer_casp14': same tuple as 'monomer',
}
```

`CONFIG_DIFFS` contains per-model flattened config overrides. It includes active names from `MODEL_PRESETS` plus historical multimer and multimer v2 names used by the config module.

### `model_config(name: str) -> ml_collections.ConfigDict`

Returns a mutable config dict for a model name in `CONFIG_DIFFS`.

Important behavior:

- Raises `ValueError` for unknown model names.
- Uses `CONFIG_MULTIMER` when `'multimer' in name`; otherwise uses the monomer `CONFIG` base.
- Applies differences with `update_from_flattened_dict`.
- The monomer config has `data` and `model` sections; the multimer base has a `model` section and no top-level `data` section.

Common fields to inspect:

| Field | Meaning |
| --- | --- |
| `cfg.model.global_config.multimer_mode` | Whether `RunModel` builds multimer modules. |
| `cfg.model.num_recycle` | Maximum recycling iterations. Multimer v3 defaults to 20. |
| `cfg.model.recycle_early_stop_tolerance` | Multimer v3 early-stop tolerance; absent or `None` in monomer-style configs. |
| `cfg.model.num_ensemble_eval` / `cfg.data.eval.num_ensemble` | Evaluation ensembling knobs. Exact field location differs by config family. |
| `cfg.model.heads.predicted_aligned_error.weight` | Nonzero for pTM/multimer-style confidence-head configs. |
| `cfg.model.embeddings_and_evoformer.template.enabled` | Whether template embedding is enabled. |
| `cfg.model.embeddings_and_evoformer.num_msa` | Multimer MSA row budget in the model stack. |
| `cfg.model.embeddings_and_evoformer.num_extra_msa` | Extra MSA budget; differs between multimer v3 models 1-3 and 4-5. |

### `get_model_config(name: str, frozen: bool = True) -> AlphaFoldConfig`

Returns a dataclass config tree. It is cached with `functools.lru_cache`, so repeated calls with the same arguments return the cached object.

Important behavior:

- Raises `ValueError` for unknown names.
- Applies equivalent differences to `model_config`; `config_test.py` verifies JSON-equivalence between the dict and dataclass views for all `CONFIG_DIFFS` keys.
- With `frozen=True`, use `with cfg.unfreeze():` before assignment.
- `AlphaFoldConfig.as_dict(include_none=False)` is useful for JSON-like summaries.

### Config placeholder constants

The config module imports placeholder strings from `alphafold.model.tf.shape_placeholders`:

| Constant | Placeholder meaning |
| --- | --- |
| `NUM_RES` | Runtime-varying number of residues. |
| `NUM_MSA_SEQ` | Runtime-varying MSA cluster count. |
| `NUM_EXTRA_SEQ` | Runtime-varying extra-MSA count. |
| `NUM_TEMPLATES` | Runtime-varying template count. |

These placeholders appear in feature shape specs such as `cfg.data.eval.feat` and should not be replaced with fixed lengths except inside controlled preprocessing code.

## `alphafold.model.model`

### `RunModel(config, params=None)`

Constructor signature:

```python
RunModel(config: ml_collections.ConfigDict, params: Optional[Mapping[str, Mapping[str, jax.Array]]] = None)
```

Constructor behavior:

- Stores `config`, `params`, and `multimer_mode = config.model.global_config.multimer_mode`.
- Builds a Haiku transform around `modules_multimer.AlphaFold` for multimer configs.
- Builds a Haiku transform around `modules.AlphaFold` for monomer configs with `compute_loss=False` and `ensemble_representations=True`.
- JIT-compiles both `apply` and `init` with `jax.jit`.

Methods:

| Method | Contract | Safety notes |
| --- | --- | --- |
| `init_params(feat, random_seed=0)` | Initializes random parameters if no params were supplied. | Random params are useful only for shape/debug experiments, not scientific predictions. |
| `process_features(raw_features, random_seed)` | Returns multimer raw features unchanged; for monomer calls `features.np_example_to_features`. | Monomer processing imports and executes TensorFlow v1 graph/session code on CPU. |
| `eval_shape(feat)` | Initializes params if needed and calls `jax.eval_shape` on the model apply function. | Can still touch JAX compilation/backend paths. |
| `predict(feat, random_seed)` | Initializes params if needed, applies model, blocks on outputs, and appends confidence metrics. | Full inference is expensive and should not be run during routine skill validation. |

### `get_confidence_metrics(prediction_result, multimer_mode)`

Internal post-processing helper that adds confidence metrics from model logits:

- Always computes `plddt` from `prediction_result['predicted_lddt']['logits']`.
- When `predicted_aligned_error` exists, computes aligned-error arrays and `ptm`.
- In multimer mode, computes `iptm` and sets `ranking_confidence = 0.8 * iptm + 0.2 * ptm`.
- In non-multimer mode, sets `ranking_confidence` to mean pLDDT.

Route output JSON interpretation and user-facing confidence explanations to `../outputs-and-confidence/`.

## `alphafold.model.data`

### `get_model_haiku_params(model_name: str, data_dir: str) -> hk.Params`

Loads parameters from:

```text
<data_dir>/params/params_<model_name>.npz
```

and converts them with `alphafold.model.utils.flat_params_to_haiku`.

Use cases:

- Constructing a `RunModel` for a known model name after the user has confirmed the parameter bundle exists.
- Diagnosing path/name mismatches without running prediction.

Common failures:

- Passing the `params/` directory instead of its parent as `data_dir`.
- Using `model_1_multimer` or `model_1_multimer_v2` when the installed preset selected `model_1_multimer_v3`.
- Missing downloaded parameter files or stale pre-v2.3 parameter bundles.
- Shape/key mismatch after loading a file whose suffix does not match the selected config.

## `alphafold.model.features`

### `make_data_config(config, num_res)`

Returns `(cfg, feature_names)` for monomer TensorFlow preprocessing:

- Deep-copies `config.data`.
- Starts from `cfg.common.unsupervised_features`.
- Appends `cfg.common.template_features` when templates are enabled.
- Sets `cfg.eval.crop_size = num_res` under an unlocked config.

### `np_example_to_features(np_example, config, random_seed=0)`

Converts raw NumPy example features into model-ready monomer features:

- Reads `num_res` from `np_example['seq_length'][0]`.
- Renames `deletion_matrix_int` to float32 `deletion_matrix` when present.
- Builds a TensorFlow v1 graph on CPU.
- Converts NumPy features with `proteins_dataset.np_to_tensor_dict`.
- Applies `input_pipeline.process_tensors_from_config`.
- Runs a TensorFlow session and drops object-dtype outputs.

Do not call this for multimer feature dictionaries unless you intentionally know the monomer pipeline is expected; `RunModel.process_features` bypasses it when `multimer_mode` is true.

## Numerical Helper APIs

### `alphafold.model.lddt.lddt`

```python
lddt(predicted_points, true_points, true_points_mask, cutoff=15.0, per_residue=False)
```

Contract:

- `predicted_points`: `(batch, length, 3)` array.
- `true_points`: `(batch, length, 3)` array.
- `true_points_mask`: `(batch, length, 1)` binary-valued float mask.
- Returns approximate lDDT in `[0, 1]`; with `per_residue=True`, returns per-residue scores.
- This implementation omits the physical plausibility correction from the original lDDT definition.

### `alphafold.model.geometry`

Key struct-of-arrays objects:

| Object | Useful methods |
| --- | --- |
| `vector.Vec3Array` | `from_array`, `to_array`, `cross`, `dot`, `norm`, `normalized`, arithmetic operators. |
| `rotation_matrix.Rot3Array` | `identity`, `from_array`, `to_array`, `from_quaternion`, `from_two_vectors`, `random_uniform`, `inverse`, `apply_to_point`. |
| `rigid_matrix_vector.Rigid3Array` | `identity`, `from_array`, `from_array4x4`, `to_array`, `inverse`, `apply_to_point`, `apply_inverse_to_point`, `scale_translation`. |

These objects are JAX pytrees and are designed for numerical stability/performance with coordinate geometry. They are not PDB/mmCIF parsers.

### `alphafold.model.all_atom`

Frequently referenced helper groups:

| Helper | Purpose |
| --- | --- |
| `atom14_to_atom37` / `atom37_to_atom14` | Convert atom representations using residue index maps in a feature batch. |
| `atom37_to_frames` / `atom37_to_torsion_angles` | Build rigid group frames and torsion features from all-atom coordinates. |
| `torsion_angles_to_frames` / `frames_and_literature_positions_to_atom14_pos` | Convert structure-module torsion/frame outputs back to atom positions. |
| `extreme_ca_ca_distance_violations`, `between_residue_bond_loss`, `between_residue_clash_loss`, `within_residue_violations` | Structural violation and loss helpers. |
| `find_optimal_renaming`, `get_alt_atom14` | Handle ambiguous atom naming alternatives. |
| `frame_aligned_point_error` | Compute masked FAPE for frame/position pairs. |

Use these helpers only with correctly shaped JAX arrays and feature-batch maps. For user-level relaxation troubleshooting, route to `../relaxation/`; for output confidence artifacts, route to `../outputs-and-confidence/`.

## Lightweight Inspection Pattern

For safe package inspection:

```python
from alphafold.model import config

for preset, names in config.MODEL_PRESETS.items():
    print(preset, names)

cfg = config.model_config('model_1_ptm')
print(cfg.model.global_config.multimer_mode)
print(cfg.model.heads.predicted_aligned_error.weight)
```

This pattern imports configuration metadata only. It does not load model parameters, construct `RunModel`, preprocess features, or run inference.
