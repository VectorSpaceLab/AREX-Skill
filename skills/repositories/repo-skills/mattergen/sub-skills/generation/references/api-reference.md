# Generation API reference

This reference describes the public generation surface observed in MatterGen
1.0.3. Use `inspect.signature` in the installed environment if a later package
version is being used; do not infer compatibility from a checkpoint filename.

## `MatterGenCheckpointInfo`

Import:

```python
from mattergen.common.utils.data_classes import MatterGenCheckpointInfo
```

Constructor contract:

```python
MatterGenCheckpointInfo(
    model_path,
    load_epoch="last",
    config_overrides=[],
    split="val",
    strict_checkpoint_loading=True,
)
```

- `model_path` is a local checkpoint/config directory. The loader recursively
  searches it for `.ckpt` files and expects `last.ckpt` for `load_epoch="last"`.
  `load_epoch="best"` chooses the lowest validation-loss filename among
  non-`last.ckpt` files; an integer selects that epoch.
- `config_overrides` is a list of Hydra override strings applied while composing
  the checkpoint config. Keep overrides compatible with the checkpoint.
- `split` defaults to `val` and is stored in checkpoint metadata; it is not a
  substitute for selecting a different model.
- `strict_checkpoint_loading=True` makes missing/unexpected checkpoint keys a
  failure. Only relax it when the checkpoint producer explicitly documents why.

Hub helper:

```python
MatterGenCheckpointInfo.from_hf_hub(
    model_name,
    repository_name="microsoft/mattergen",
    config_overrides=None,
)
```

The helper requests `checkpoints/<model_name>/checkpoints/last.ckpt` and
`checkpoints/<model_name>/config.yaml` from the Hub. It may download data. Call
it only after the user explicitly chooses a run; the bundled validator does not
call it.

## `CrystalGenerator`

Import:

```python
from mattergen.generator import CrystalGenerator
```

The observed constructor signature is:

```python
CrystalGenerator(
    checkpoint_info,
    batch_size=None,
    num_batches=None,
    target_compositions_dict=None,
    num_atoms_distribution="ALEX_MP_20",
    diffusion_guidance_factor=0.0,
    properties_to_condition_on=None,
    sampling_config_overrides=None,
    num_samples_per_batch=1,
    niggli_reduction=False,
    sampling_config_path=None,
    sampling_config_name="default",
    record_trajectories=True,
    _model=None,
    _cfg=None,
    progress_callback=None,
)
```

The public generation call is:

```python
structures = generator.generate(
    batch_size=None,
    num_batches=None,
    target_compositions_dict=None,
    output_dir="outputs",
)
```

It returns a `list[pymatgen.core.structure.Structure]` and writes files under
`output_dir`. Constructor values are defaults; values passed to `generate` take
priority for batch size, number of batches, and compositions. If those values
are not supplied at either level, generation asserts because it cannot determine
how many samples to request.

### Parameter semantics

| Parameter | Meaning and safe use |
|---|---|
| `batch_size` | Samples processed per loader batch. Increase only within device memory. |
| `num_batches` | Number of batches. Total requested samples are `batch_size * num_batches`. |
| `target_compositions_dict` | List of element-to-count dictionaries for CSP. Use only with a CSP-trained model and `sampling_config_name="csp"`. |
| `num_atoms_distribution` | Unconditional atom-count distribution. The shipped choice is `ALEX_MP_20`; it covers 1–20 atoms. |
| `diffusion_guidance_factor` | Classifier-free guidance scale; 0 unconditional, 1 conditional, larger values stronger guidance. |
| `properties_to_condition_on` | Target property dictionary, for example `{"dft_mag_density": 0.15}`. Every key must be a trained condition of the loaded model. |
| `sampling_config_overrides` | Hydra override strings, applied to the selected sampling config. |
| `sampling_config_path` | Directory containing sampling YAML files. `None` selects MatterGen's installed default sampling config directory. |
| `sampling_config_name` | YAML basename without extension, normally `default` or `csp`. |
| `record_trajectories` | When true, writes the full denoising trajectory ZIP as well as final structures. Disable to reduce disk and memory pressure. |
| `progress_callback` | Optional callable receiving a float from 0 to 1. |

`niggli_reduction` and `num_samples_per_batch` are legacy-model knobs and do
not replace the CSP composition route. `_model` and `_cfg` are injection/cache
hooks; do not use them to bypass checkpoint validation in a normal workflow.

## Output contract

`mattergen-generate` and `CrystalGenerator.generate` use the same output writer:

- `generated_crystals_cif.zip`: one `gen_<index>.cif` per final structure.
- `generated_crystals.extxyz`: final structures as frames.
- `generated_trajectories.zip`: one `gen_<index>.extxyz` per structure when
  `record_trajectories=True`; each contains intermediate denoising states.

A returned Python structure list is in memory and is not a replacement for the
on-disk artifacts. A failed or interrupted job can leave a directory with some
files; verify the structure/frame counts before evaluation.

## Property and composition types

`TargetProperty` is effectively:

```python
dict[str, int | float | str | Sequence[str]]
```

Typical property keys in the package registry are `dft_mag_density`,
`dft_bulk_modulus`, `dft_shear_modulus`, `energy_above_hull`,
`formation_energy_per_atom`, `space_group`, `hhi_score`, `ml_bulk_modulus`,
`chemical_system`, and `dft_band_gap`. The registry is broader than any one
checkpoint's trained condition set. Composition mappings should use valid
pymatgen element symbols and positive integer atom counts.
