---
name: symmetric-oligomers
description: "Build RFdiffusion symmetric oligomer and symmetric
  motif-scaffolding commands for cyclic, dihedral, tetrahedral, octahedral, and
  icosahedral point groups, including contig divisibility, oligomer contact
  potentials, neighbor-only modeling, and output checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Symmetric Oligomers

Use this sub-skill when a user wants RFdiffusion to generate homo-oligomeric backbones or scaffold a motif under an explicit point-group symmetry.

## Route Here

- Cyclic or dihedral oligomers such as `C4`, `C6`, `D2`, or `d5`.
- Tetrahedral, octahedral, or icosahedral symmetric generation with `inference.symmetry=tetrahedral`, `octahedral`, or `icosahedral`.
- Commands that require `--config-name=symmetry` or symmetry-mode defaults.
- Total oligomer contigs whose length must divide evenly across symmetry copies.
- Symmetric motif scaffolding where the input PDB already contains symmetrized motif copies aligned to RFdiffusion's canonical axes.
- Oligomer contact potential setup for symmetric oligomer packing, with routing to detailed potential tuning when needed.
- Debugging outputs, chain counts, chain labels, and symmetry-specific validation failures.

## Route Elsewhere

- Detailed potential selection, custom contact matrices, weight sweeps, and guide-decay tuning belong in `../guided-potentials/SKILL.md` when that sibling exists.
- Motif residue mechanics, non-symmetric motif scaffolding, active-site checkpoint choice, `inpaint_seq`, or target-chain contigs belong in `../motif-scaffolding/SKILL.md`.
- Macrocyclic peptide design uses `inference.cyclic=True` and belongs in the macrocycle-design sibling, not here.
- Single-chain de novo generation without symmetry belongs in `../unconditional-generation/SKILL.md`.
- Partial diffusion from an existing oligomer belongs in `../partial-diffusion/SKILL.md` unless the main question is the symmetry setup itself.

## Inputs To Confirm

- `run_inference.py` path in the user's RFdiffusion installation; do not assume the original checkout remains available.
- Symmetry name exactly as an RFdiffusion override: `C6`, `D2`, `tetrahedral`, `octahedral`, or `icosahedral`.
- Total oligomer length or a total-length range, not per-chain length.
- Output prefix and number of designs; use one deterministic design for smoke checks.
- Model directory or explicit checkpoint when the installation cannot find weights automatically.
- Whether contact potentials are desired; start from the documented oligomer-contact defaults before tuning.
- For symmetric motif scaffolding: an input PDB whose motif copies are already symmetrized around RFdiffusion's canonical axes.

## Chain Counts And Divisibility

RFdiffusion symmetry mode applies rotations to one asymmetric unit and requires the generated sequence length to divide evenly by the number of symmetry copies.

- `C<n>` has `n` chains, so `C6` with total length `480-480` gives six 80-residue chains.
- `D<n>` has `2*n` chains, so `D2` with total length `320-320` gives four 80-residue chains.
- `tetrahedral` uses 12 saved rotations for the named point group; `t3` is also accepted by the code but only produces the legacy four-rotation `T3` mode.
- `octahedral` uses 24 rotations, and `icosahedral` uses 60 rotations.
- Every bound in a length range should be divisible by the chain count unless the user accepts possible runtime failures from sampled incompatible lengths.

If the user gives a per-chain length, multiply it by the chain count before writing `contigmap.contigs`. For example, a 90-residue `C4` chain uses `'contigmap.contigs=[360-360]'`.

## Command Pattern

Use the detailed templates in `references/workflows.md`. The common skeleton is:

```bash
python /path/to/run_inference.py \
  --config-name=symmetry \
  inference.symmetry="C6" \
  'contigmap.contigs=[480-480]' \
  inference.output_prefix=outputs/C6_oligo/design \
  inference.num_designs=10
```

Keep Hydra list-like values in single quotes. Quote `inference.symmetry` when using uppercase cyclic/dihedral names to avoid shell surprises, although RFdiffusion handles cyclic and dihedral prefixes case-insensitively.

## Oligomer Contact Potentials

The repository examples add `olig_contacts` to improve packing between and within chains:

```bash
'potentials.guiding_potentials=["type:olig_contacts,weight_intra:1,weight_inter:0.1"]' \
potentials.olig_intra_all=True \
potentials.olig_inter_all=True \
potentials.guide_scale=2.0 \
potentials.guide_decay="quadratic"
```

Use this as a starting point, not a universal optimum. The documented rule of thumb is to keep intra-chain contact weight higher than inter-chain contact weight. RFdiffusion's potential manager can compute oligomer contact chain counts for `C*`, `D*`, and `tetrahedral`; avoid promising `olig_contacts` for `octahedral` or `icosahedral` without first checking the installed code because the manager raises `NotImplementedError` for symbols starting with `o` and does not handle `i`.

## Symmetric Motif Scaffolding

Use this path only when the motif PDB is already symmetrized in the same point group and axes RFdiffusion will use. For cyclic symmetry, the canonical axis is `Z`; for dihedral symmetry, the cyclic axis is `Z` and the flip/reflection axis is `X`.

The C4 nickel-style command combines symmetry, an input PDB, repeated motif spans, oligomer contacts, and a checkpoint override:

```bash
python /path/to/run_inference.py \
  inference.symmetry="C4" \
  inference.input_pdb=/path/to/nickel_symmetric_motif.pdb \
  'contigmap.contigs=[50/A2-4/50/0 50/A7-9/50/0 50/A12-14/50/0 50/A17-19/50/0]' \
  inference.ckpt_override_path=/path/to/Base_epoch8_ckpt.pt \
  inference.output_prefix=outputs/design_nickel/design \
  inference.num_designs=15 \
  'potentials.guiding_potentials=["type:olig_contacts,weight_intra:1,weight_inter:0.06"]' \
  potentials.olig_intra_all=True \
  potentials.olig_inter_all=True \
  potentials.guide_scale=2 \
  potentials.guide_decay="quadratic"
```

Do not substitute an asymmetric single motif and expect RFdiffusion to place the other copies correctly. If motif residue selection, masking, or active-site checkpoint reasoning is the main issue, route to motif scaffolding after establishing the symmetric layout requirement.

## Validation Checklist

- Use `--config-name=symmetry` for ordinary symmetric oligomer generation; if omitting it for an advanced motif command, explicitly set all needed symmetry/base overrides.
- Confirm `inference.symmetry` is one of `C<n>`, `D<n>`, `tetrahedral`, `octahedral`, or `icosahedral`; `c6` and `d2` also work.
- Confirm the total contig length divides by the chain count.
- Confirm potential-guided commands quote the nested list exactly as one override.
- Confirm `inference.output_prefix` is a prefix; outputs are suffixed as `_0.pdb`, `_0.trb`, and optional trajectory files.
- For motif scaffolding, confirm the PDB contains every motif span and those spans are already arranged symmetrically around the canonical axes.
- For smoke checks, use `inference.num_designs=1`, `inference.deterministic=True`, `inference.final_step=48`, `inference.cautious=True`, and often `inference.write_trajectory=False`.

## Output Interpretation

Symmetric outputs are written as multi-chain PDBs. RFdiffusion inserts chain breaks across the symmetry copies, using sequential chain labels generated from the symmetry order. The `.trb` file records the resolved config and contig mappings; inspect it when validating sampled length, symmetry, checkpoint, or motif placement. If `inference.write_trajectory=True`, trajectory PDBs are written under a `traj/` directory next to the output prefix.

Use `references/troubleshooting.md` for failure triage and `references/workflows.md` for complete command recipes.

## Evidence Base

This sub-skill is backed by RFdiffusion evidence from the README symmetric oligomer and symmetric motif sections, `config/inference/symmetry.yaml`, `config/inference/base.yaml`, `rfdiffusion/inference/symmetry.py`, `rfdiffusion/potentials/manager.py`, `rfdiffusion/potentials/potentials.py`, and the cyclic, dihedral, tetrahedral, and nickel example scripts.
