# TFG, Confidence, and Metrics

Use this reference when enabling Training-Free Guidance (TFG), checking confidence post-processing, or using Protenix metrics directly.

## Training-Free Guidance Entry Points

Current TFG entry points:

```python
from protenix.tfg import TFGEngine, parse_tfg_config
from protenix.tfg.config import TFGConfig, validate_features
from protenix.tfg.potentials import CLASS_REGISTRY
```

The generator constructs guidance with `parse_tfg_config(configs.sample_diffusion.guidance)` and `TFGEngine(tfg_cfg, device=device, dtype=dtype)` when guidance is enabled.

## TFG Config Shape

The parser accepts a mapping with only these top-level keys:

- `enable`: bool switch.
- `rho`: denoiser-path guidance strength.
- `mu`: direct x0 refinement step size.
- `mc`: mapping with `std` and `batch` for Monte-Carlo perturbations.
- `steps`: mapping with `tfg_outer`, `tfg_inner`, `projection_outer`, and `projection_inner`.
- `terms`: mapping from potential class name to term config.
- `log_last_step_energy`: bool debug switch.

Unknown top-level keys raise `KeyError`. If `enable=True` and no terms are configured, parsing raises `ValueError`.

Schedule values can be constants or schedule dictionaries:

```python
{"type": "const", "value": 0.1}
{"type": "exp_interpolation", "start": 1.0, "end": 0.0, "alpha": 3.0}
```

## Built-In TFG Potential Names

Registered potential class names include:

- `InterchainBondPotential`
- `PairwiseDistancePotential`
- `StereoBondPotential`
- `ChiralAtomPotential`
- `PlanarImproperPotential`
- `LinearBondPotential`
- `ExperimentalTorsionPotential`
- `VinaStericPotential`

Unknown names raise `KeyError` and include the sorted available registry keys.

## Required Feature Keys

TFG validates required input feature keys before a step. Missing features raise a `KeyError` grouped by potential name.

| Potential | Required feature keys |
| --- | --- |
| `PairwiseDistancePotential` | `pairwise_distance_index`, `pairwise_distance_is_bond`, `pairwise_distance_is_angle`, `pairwise_distance_upper_bound`, `pairwise_distance_lower_bound`, `ref_element` |
| `InterchainBondPotential` | `interchain_bond_index` |
| `VinaStericPotential` | `asym_id`, `atom_to_token_idx`, `ref_element`, `interchain_bond_index` |
| `SymmetricChainPotential` | `asym_id`, `atom_to_token_idx`, `symmetric_chain_index` |
| `StereoBondPotential` | `stereo_bond_index`, `stereo_bond_orientation` |
| `ChiralAtomPotential` | `chiral_index`, `chiral_orientation`, `asym_id`, `atom_to_token_idx` |
| `PlanarImproperPotential` | `planar_improper_index`, `planar_improper_is_carbonyl` |
| `LinearBondPotential` | `linear_triple_bond_index` |
| `ExperimentalTorsionPotential` | `experimental_torsion_index`, `experimental_torsion_force_constant`, `experimental_torsion_sign` |

If a feature key is missing during prediction, route input/feature authoring to `../../input-data-and-features/SKILL.md` unless the user is modifying TFG internals.

## TFG Runtime Shapes

TFG potential conventions:

- Coordinates are shaped `[..., N_atom, 3]`.
- Energy returns shape `[...]` or a scalar per sample.
- Gradients and projection deltas match coordinate shape.
- Projection terms are applied in a fixed order prioritizing chiral constraints, then pairwise distances, then other projection-capable terms.

Use conservative tuning:

- Keep `enable=False` unless the user explicitly needs guidance.
- Start with a small number of inner/projection steps when debugging.
- If terms are configured but `rho=0`, `mu=0`, and projections are disabled, guidance may be effectively inert.
- Do not invent feature keys or output files; TFG consumes features already prepared by the input pipeline.

## Confidence Utility Families

Current confidence helpers live in `protenix.model.sample_confidence`.

Common entry points:

```python
from protenix.model.sample_confidence import (
    merge_per_sample_confidence_scores,
    compute_contact_prob,
    logits_to_prob,
    logits_to_score,
    calculate_ptm,
    calculate_iptm,
    calculate_chain_based_ptm,
    calculate_chain_based_gpde,
    calculate_chain_pair_pae,
    calculate_chain_based_plddt,
)
```

Important signatures and shapes:

- `merge_per_sample_confidence_scores(summary_confidence_list)` stacks per-sample score dictionaries, unsqueezing scalar tensors first.
- `compute_contact_prob(distogram_logits, min_bin, max_bin, no_bins, thres=8.0)` expects distogram logits shaped `[N_token, N_token, N_bins]` and returns `[N_token, N_token]` contact probabilities.
- `logits_to_prob(logits, dim=-1)` softmaxes logits along the bin dimension.
- `logits_to_score(logits, min_bin, max_bin, no_bins, return_prob=False)` expects `[..., no_bins]`; it returns a score shaped `[...]`, and optionally the probability tensor shaped `[..., no_bins]`.
- `calculate_ptm(pae_prob, has_frame, min_bin, max_bin, no_bins, token_mask=None)` expects PAE probability shaped `[..., N_token, N_token, N_bins]` and frame mask shaped `[N_token]`.
- `calculate_iptm` follows the PAE probability and token metadata pattern, with asymmetry/interface semantics.
- `calculate_chain_based_ptm` returns `chain_ptm`, `chain_iptm`, `chain_pair_iptm`, and `chain_pair_iptm_global`.
- `calculate_chain_based_gpde` returns `chain_gpde` and `chain_pair_gpde` from `token_pair_pde`, `contact_probs`, and `asym_id`.
- `calculate_chain_pair_pae` returns `chain_pair_pae_mean` and `chain_pair_pae_min`; tests show it preserves directionality for chain pairs and remaps gapped `asym_id` values to contiguous chain axes.

Confidence interpretation notes:

- `plddt` and `ptm` are higher-is-better ranking-style scores.
- `gpde` and PAE/PDE distances are error-like values; lower is generally better.
- Chain-pair values may be directional, especially PAE mean/min calculations.
- Many helpers assume token-level and atom-level arrays are aligned through `atom_to_token_idx` and `asym_id`; shape mismatches should be fixed at the feature level, not hidden by reshaping.

## RMSD Metrics

Current RMSD helpers live in `protenix.metrics.rmsd`:

```python
from protenix.metrics.rmsd import (
    rmsd,
    align_pred_to_true,
    partially_aligned_rmsd,
    self_aligned_rmsd,
    weighted_rigid_align,
)
```

Important signatures and shapes:

- `rmsd(pred_pose, true_pose, mask=None, eps=0.0, reduce=True)` expects matching coordinate shapes `[..., N, 3]`; mask shape is `[..., N]`. With `reduce=True`, batch-like dimensions are averaged.
- `align_pred_to_true(pred_pose, true_pose, atom_mask=None, weight=None, allowing_reflection=False)` returns `(aligned_pose, rot, translate)`.
- `partially_aligned_rmsd(pred_pose, true_pose, align_mask, atom_mask, weight=None, eps=0.0, reduce=True, allowing_reflection=False)` returns aligned-part RMSD, unaligned-part RMSD, transformed coordinates, rotation, and translation.
- `self_aligned_rmsd(pred_pose, true_pose, atom_mask, eps=0.0, reduce=True, allowing_reflection=False)` aligns and evaluates the same atom subset.
- `weighted_rigid_align(x, x_target, atom_weight, stop_gradient=True)` wraps alignment and returns aligned coordinates.

RMSD troubleshooting:

- Empty or all-zero masks can lead to division by zero or invalid values.
- Coordinates must share shape exactly for `rmsd`.
- Use `allowing_reflection=False` unless the user explicitly asks for mirror/reflection alignment.
- Keep tensors on the same device and use floating dtypes.

## LDDT Metrics

Current LDDT helpers live in `protenix.metrics.lddt_metrics`:

```python
from protenix.metrics.lddt_metrics import LDDT, LDDTMetrics
```

Important behavior:

- `LDDT.forward(pred_coordinate, true_coordinate, lddt_mask, chunk_size=None)` uses sparse pair indices from `torch.nonzero(lddt_mask)`.
- `pred_coordinate` is shaped `[N_sample, N_atom, 3]`.
- `true_coordinate` is shaped `[N_atom, 3]`.
- `lddt_mask` is a dense pair mask shaped `[N_atom, N_atom]`; the implementation converts it to sparse indices internally.
- `LDDT.compute_lddt_mask(true_coordinate, true_coordinate_mask, is_nucleotide=None, is_nucleotide_threshold=30.0, threshold=15.0)` builds a dense pair mask, removes diagonal pairs, and zeroes atom pairs without true coordinates.
- Tests confirm the fused threshold computation is equivalent to averaging threshold comparisons at `0.5`, `1.0`, `2.0`, and `4.0`.

## Hard Usability Cases This Sub-Skill Should Support

1. A GPU run fails in a tri-attention/cuEquivariance path. Expected response: run the doctor, set `LAYERNORM_TYPE=torch`, switch both triangle kernels to `torch`, verify CUDA and optional package versions, then re-enable only one acceleration path at a time.
2. A user asks how to interpret confidence, RMSD, and LDDT values from tensors. Expected response: identify the correct function family, state required shapes and higher/lower-is-better semantics, and avoid inventing output files or unsupported post-processing.
