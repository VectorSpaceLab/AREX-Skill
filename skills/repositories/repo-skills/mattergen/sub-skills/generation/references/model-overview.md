# Checkpoint catalog and generation limits

## Released checkpoint names

The package's `PRETRAINED_MODEL_NAME` literal and the repository's checkpoint
config directories provide this catalog. A name is a model selector, not a
promise that its files are present locally.

| Name | Intended route / known condition |
|---|---|
| `mattergen_base` | Unconditional base model trained on Alex-MP-20; its config also contains the base model's available property embeddings for fine-tuning context. |
| `mp_20_base` | Unconditional base model trained on MP-20. |
| `chemical_system` | Chemical-system conditional model. |
| `space_group` | Space-group conditional model. |
| `dft_mag_density` | DFT magnetic-density conditional model. |
| `dft_band_gap` | DFT band-gap conditional model. |
| `ml_bulk_modulus` | ML bulk-modulus conditional model. |
| `dft_mag_density_hhi_score` | Joint DFT magnetic-density and HHI-score model. |
| `chemical_system_energy_above_hull` | Joint chemical-system and energy-above-hull model. |

The same names are available from the default Hub repository
`microsoft/mattergen` under `checkpoints/<name>/`. Repository-provided local
checkpoint folders contain `config.yaml` and LFS-managed checkpoint paths. A
small pointer file is evidence that LFS metadata exists, not evidence that a
loadable checkpoint has been hydrated.

## Condition compatibility

The package registry (`PROPERTY_SOURCE_IDS`) includes:

- `dft_mag_density`
- `dft_bulk_modulus`
- `dft_shear_modulus`
- `energy_above_hull`
- `formation_energy_per_atom`
- `space_group`
- `hhi_score`
- `ml_bulk_modulus`
- `chemical_system`
- `dft_band_gap`

The registry is not a universal model capability list. Use the checkpoint's
config/property embeddings and model training record to confirm compatibility.
For example, the `chemical_system_energy_above_hull` config declares both
`chemical_system` and `energy_above_hull`, while the
`dft_mag_density_hhi_score` config declares `dft_mag_density` and `hhi_score`.
A missing trained condition causes the generator's condition assertion to fail;
do not work around that assertion by editing a checkpoint config.

## Sampling configs

The installed package resolves its default sampling config directory from the
package installation. The source evidence includes these two YAML configs:

- `default.yaml`: `GuidedPredictorCorrector`, `N=1000`, guidance scale default
  `0.0`, position and lattice predictor/corrector parts, and atomic-number
  predictor/corrector parts. Its condition loader samples atom counts from the
  selected number-of-atoms distribution.
- `csp.yaml`: the same broad predictor/corrector structure for position and
  lattice, but no atomic-number predictor/corrector parts. Its condition loader
  is `get_composition_data_loader`, which receives fixed compositions.

The generator appends condition-loader batch/sample-count overrides for ordinary
sampling. Do not copy internal `_target_` paths into application code unless a
Hydra override is genuinely required; prefer the public generator arguments.

## Device, size, and quality boundaries

- Verified inspection facts for this package include Python 3.10,
  `torch 2.2.1+cu118`, CUDA PyTorch Geometric wheels, and an A100 CUDA tensor
  smoke test when a device is selected. These facts describe an inspection
  environment, not a requirement to publish local paths or assume every user
  has an A100.
- MatterGen's model card reports roughly 46.8M parameters and approximately two
  hours for 1,000 samples on one V100. Treat this as an order-of-magnitude
  planning signal, not a throughput guarantee.
- The released training/evaluation regime supports at most 20 atoms per unit
  cell. Organic/non-crystalline use and unsupported elements are out of scope;
  the native CLI adds an element-mask override to suppress disallowed elements.
- Property guidance can trade diversity and realism for adherence, especially at
  extreme target values with sparse training labels. Generated candidates need
  independent structural, energetic, and domain validation before use.
- CPU and MPS routes may import or run with caveats, but are not evidence of the
  CUDA-scale performance described by the model card. Apple Silicon is marked
  experimental and may require `PYTORCH_ENABLE_MPS_FALLBACK=1`.

## Asset acquisition decision

When a user has a working CUDA import but no checkpoint, separate the diagnosis:

1. **Backend ready:** imports and device smoke pass.
2. **Asset missing:** local checkpoint absent, LFS pointer unhydrated, or Hub
   cache/network unavailable.
3. **Execution not yet authorized:** do not invoke `from_hf_hub` or start a
   large sample merely because the backend is ready.

Acquire one named model or hydrate one local checkpoint, perform a one-batch
smoke, and only then scale the run.
