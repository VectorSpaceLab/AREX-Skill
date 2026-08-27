# YAML and Pydantic configuration

The package exposes `Alphafold3Config`, `WeightedPDBSamplerConfig`,
`DatasetConfig`, `TrainerConfig`, and `ConductorConfig` in
`alphafold3_pytorch.configs`. The bundled validator checks the selected mapping
without calling any `create_instance` method.

## Model mapping

`Alphafold3Config` requires the following dimensions and loss/bin settings:

```yaml
dim_atom_inputs: 3
dim_template_feats: 108
dim_template_model: 8
atoms_per_window: 27
dim_atom: 4
dim_atompair_inputs: 5
dim_atompair: 4
dim_input_embedder_token: 4
dim_single: 4
dim_pairwise: 4
dim_token: 4
num_dist_bins: null
num_plddt_bins: 50
num_pde_bins: 64
num_pae_bins: 64
sigma_data: 16
diffusion_num_augmentations: 4
loss_confidence_weight: 0.0001
loss_distogram_weight: 0.01
loss_diffusion_weight: 4.0
```

`ignore_index` defaults to `-1`; the model class supplies many additional
architecture defaults. A small model configuration can override nested
architecture dictionaries such as `confidence_head_kwargs`,
`template_embedder_kwargs`, `msa_module_kwargs`, `pairformer_stack`, and
`diffusion_module_kwargs`. These nested overrides are model-architecture
choices; keep their detailed shape/forward reasoning in `model-inference`.

The Pydantic model uses `extra='allow'` and `use_enum_values=True`. This means
unknown keys survive model validation, but it does **not** mean every key can be
used by the model constructor: `Alphafold3(**model_dump())` must still accept
any extra model keys. Use the validator's warnings and only carry documented
constructor keys into a production plan.

## Trainer mapping

A standalone trainer mapping has these required keys:

```yaml
model:                         # omit only when injecting model= at the factory call
  # the model mapping above
num_train_steps: 1
batch_size: 1
grad_accum_every: 1
valid_every: 1
ema_decay: 0.999
lr: 0.0001
clip_grad_norm: 10.0
accelerator: cpu
checkpoint_prefix: af3.ckpt.
checkpoint_every: 1
checkpoint_folder: ./checkpoints
overwrite_checkpoints: false
```

`model` is optional in `TrainerConfig` because callers may pass a constructed
model to `create_trainer_from_yaml`. If no model is present in YAML and no
model is injected, the factory's mutual-exclusion assertion prevents trainer
construction. The defaulted config fields are:

| Key | Default | Notes |
|---|---:|---|
| `use_tensorboard` | `true` | Adds a TensorBoard logger during factory construction. |
| `tensorboard_log_dir` | `./logs` | Directory is consumed by the logger. |
| `logger_kwargs` | `{}` | Passed to `TensorBoardLogger`. |
| `dataset_config` | `null` | If present, creates train/optional valid/test datasets. |

`TrainerConfig` also has `extra='allow'`. Several runtime `Trainer` options are
therefore accepted as extra YAML keys and forwarded by `create_instance`,
including `use_ema`, `ema_kwargs`, `ema_on_cpu`, `ema_update_model_with_ema_every`,
`distributed_eval`, `fp16`, `fabric_kwargs`, `use_adam_atan2`,
`use_adopt_atan2`, `use_lion`, and `use_torch_compile`. The extra key must still
be a valid `Trainer` keyword; an arbitrary extra is accepted by Pydantic but
can fail later at construction. `use_tensorboard`, `tensorboard_log_dir`, and
`logger_kwargs` are handled by the factory rather than forwarded to `Trainer`.

Keep numeric controls positive where the implementation uses them as loop
counts or modulo divisors: `num_train_steps`, `batch_size`, `grad_accum_every`,
`valid_every`, and `checkpoint_every`. Choose `checkpoint_every` and
`valid_every` in relation to the bounded step budget so diagnostics actually
exercise the intended path.

## Dataset and weighted sampler mappings

`DatasetConfig` has the following contract:

```yaml
dataset_config:
  dataset_type: pdb                 # pdb or atom
  train_folder: ./data/train        # required existing directory
  valid_folder: ./data/valid        # optional existing directory
  test_folder: ./data/test          # optional existing directory
  convert_pdb_to_atom: false
  pdb_to_atom_kwargs: {}
  kwargs: {}                         # passed to PDBDataset or AtomDataset
  train_weighted_sampler: null       # PDB-only sampler configuration
```

`train_folder`, `valid_folder`, and `test_folder` are Pydantic
`DirectoryPath` values, so package validation checks that they already exist.
`train_weighted_sampler` uses:

```yaml
train_weighted_sampler:
  chain_mapping_paths:
    - ./clusters/protein.csv
    - ./clusters/nucleic.csv
  interface_mapping_path: ./clusters/interfaces.csv
```

Those mapping values are Pydantic `FilePath` values. The sampler reads CSVs at
trainer construction, precomputes chain/interface weights, and uses the
trainer batch size. Its implementation supports optional `beta_chain`,
`beta_interface`, `alpha_prot`, `alpha_nuc`, `alpha_ligand`,
`pdb_ids_to_skip`, and `pdb_ids_to_keep` through the nested mapping. It is
expensive relative to a plain loader and requires compatible mapping columns;
use it only when the sampling policy is intentional.

`dataset_type: atom` selects `AtomDataset`, which expects saved `.pt`
`AtomInput` records. `dataset_type: pdb` selects `PDBDataset`, whose additional
options belong in `kwargs` and whose input/MSA/template preparation is owned by
`data-pipeline`. `convert_pdb_to_atom: true` is valid only with `dataset_type:
pdb`; conversion may write many atom files and should be planned separately.

Do not provide a YAML dataset source and also inject the corresponding
`dataset`, `valid_dataset`, or `test_dataset` object into the factory. The
factory asserts that those sources are not duplicated. This is easy to miss
because Pydantic permits extra keys and because object injection is only
visible at the call site.

## Dotpaths and factory selection

`safe_deep_get` walks dictionary keys using either a dotted string or a list of
segments. The convenience factories are:

```python
create_alphafold3_from_yaml(path, dotpath=[])
create_trainer_from_yaml(path, dotpath=[], **injected_objects)
create_trainer_from_conductor_yaml(path, dotpath=[], trainer_name=..., **kwargs)
```

Examples of valid selection:

```text
model                 # select a nested model mapping from a trainer document
training.main         # select one phase only from a conductor document
```

A missing segment returns no configuration and the factory raises an assertion;
it does not search alternative branches or infer a phase. Validate the exact
selected dotpath before construction. Avoid a trailing dot, list indices, or
assuming that a YAML list is a dictionary; the helper only walks mappings.

## Conductor mapping

A conductor document has one shared model and an explicitly named phase set:

```yaml
checkpoint_folder: ./runs
checkpoint_prefix: af3.
training_order: [main, nucleic_acids, ligands]
model:
  # required model mapping
training:
  main:
    num_train_steps: 1
    batch_size: 1
    grad_accum_every: 1
    valid_every: 1
    ema_decay: 0.999
    lr: 0.0001
    clip_grad_norm: 10.0
    accelerator: cpu
    checkpoint_prefix: main.ckpt.
    checkpoint_every: 1
    checkpoint_folder: main
    overwrite_checkpoints: false
  nucleic_acids:
    # same required trainer fields, with a deliberate override
  ligands:
    # same required trainer fields, with a deliberate override
```

`training_order` must contain exactly the same phase names as `training`; the
package validator checks set equality. Also reject duplicate phase names in
practice: set equality alone can hide a repeated name in the order list. When
phase `main` is selected, the effective checkpoint folder is
`root_folder / phase_folder` and the effective prefix is
`root_prefix + phase_prefix`. The root model is created for the selected
phase. Validate all phases, not only the first one, and compare effective
folder/prefix pairs so phases do not silently overwrite one another.

Each nested trainer can carry its own `dataset_config`. A phase without one
can use an injected dataset. If multiple phases share a mutable parsed config
object in custom code, remember that conductor construction rewrites the
selected phase's checkpoint folder and prefix in memory; reload or copy the
configuration before selecting another phase.

## Extra fields and validation status

Pydantic success means the mapping has the required types and fields for that
config class; it does not prove:

- that a Fabric accelerator or mixed-precision mode is installed;
- that the model/dataset dimensions agree after collation;
- that a weighted-sampler CSV has the required columns or covers the dataset;
- that a checkpoint directory is safe to reuse;
- that a full training budget is affordable; or
- that constructing the factory is side-effect free.

The validator reports package-model errors, selected dotpath errors, static
cross-field hazards, and warnings separately. Resolve errors first. Treat
warnings as explicit decisions to record in the run plan rather than as
permission to construct immediately.
