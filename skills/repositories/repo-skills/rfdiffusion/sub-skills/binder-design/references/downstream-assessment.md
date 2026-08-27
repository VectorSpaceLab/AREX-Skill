# Downstream Backbone Assessment

RFdiffusion binder runs generate backbone candidates. They do not assign final binder sequences, prove binding, or replace downstream prediction and filtering. Use this reference to explain safe assessment boundaries and simple metrics distilled from the repository's protein-binder tutorial scripts.

## What RFdiffusion Outputs Mean

Typical binder-design outputs are:

- `.pdb` files: generated backbone complexes with the designed binder and target context.
- `.trb` files: metadata, including the sampled contig, residue mappings, and full config.

Designed regions may appear as poly-glycine or placeholder sequence because RFdiffusion is a backbone generator. Sequence design and complex prediction are separate steps.

## Assessment Stages

A practical binder-design funnel is:

1. Generate RFdiffusion backbones with a small pilot batch.
2. Remove obvious failures by visual inspection and backbone metrics.
3. Assign binder sequences with an external sequence-design method if available.
4. Predict or relax sequence-designed complexes with tools available to the user.
5. Filter for interface confidence, target hotspot engagement, shape complementarity, and lack of severe clashes.

Keep these as optional downstream boundaries. Do not require STRIDE, Rosetta, ProteinMPNN, or AF2 to draft or run RFdiffusion commands.

## Backbone Metrics Distilled from Tutorial Scripts

The tutorial assessment scripts compute these per-PDB metrics:

- Radius of gyration (`rg`) for the binder chain or selected atoms.
- Number of atoms used for Rg (`n_atoms_rg`).
- Binder-chain CA count (`n_ca_binder`).
- N-terminus score (`nterm_sc`) and C-terminus score (`cterm_sc`) normalized by RMS distance to a user-provided interface point.
- STRIDE secondary-structure percentages: `pct_H`, `pct_E`, `pct_C`, `pct_T`, `pct_G`, `pct_I`, `pct_B`.
- Aggregates: `pct_helix_total = pct_H + pct_G + pct_I`; `pct_extended_total = pct_E + pct_B`.
- Row status and warning/error messages.

Interpretation:

- `rg` is a compactness screen, not an interface-quality guarantee.
- Terminus scores help retain designs whose termini are positioned suitably for a user-defined geometry, such as pore blocking or fusion constraints.
- Secondary-structure percentages help enforce fold-shape preferences, especially for topology-constrained binders.
- Missing or failed STRIDE should not block all assessment; geometry metrics can still be computed.

## STRIDE-Unavailable Fallback

If the user lacks STRIDE:

- Do not fail the whole binder workflow.
- Report that secondary-structure percentages are unavailable.
- Continue with PDB existence checks, binder-chain CA count, Rg, terminus score if an interface point is known, and visual inspection.
- If filtering by secondary-structure thresholds, mark those filters as skipped or ask the user to provide another secondary-structure assignment source.

A safe fallback triage can use:

```text
Required: output PDB exists, binder chain present, nonzero CA count
Optional: rg within target-specific range, termini away from or near interface as desired
Manual: binder contacts hotspot region, no obvious target clashes, no disconnected geometry
Skipped without STRIDE: helix/sheet/coil percentage thresholds
```

## Filtering Logic

The tutorial filter behavior is threshold-based:

- `--min column=value` keeps rows with numeric `column >= value`.
- `--max column=value` keeps rows with numeric `column <= value`.
- Missing, `NA`, or non-numeric values fail thresholds that require that column.
- Optional `require_ok` accepts only rows whose status is `OK`.
- Passing PDBs are copied or symlinked into a selected output directory.

Example threshold concepts:

```text
Keep compact binders:       min rg=9.5, max rg=12.0
Keep helical binders:       min pct_helix_total=70
Avoid excess coil:          max pct_C=15
Control terminus position:  min nterm_sc=0.9, max nterm_sc=1.4
```

Do not reuse thresholds blindly. Ask the user what geometry matters for their target, binder length, and downstream assay.

## ProteinMPNN and Structure Prediction Boundary

When the user asks what comes after RFdiffusion:

- Explain that RFdiffusion backbones need sequence design before most structure-prediction filters are meaningful.
- ProteinMPNN-style sequence design is a common next step, but it is external to this runtime skill.
- AF2-style complex prediction and PAE/interface filters are also external; they can be recommended only if the user has those tools.
- Repo guidance notes `pae_interaction < 10` as a useful AF2-style predictor in the paper pipeline, but it is not computed by RFdiffusion itself.

Safe phrasing:

```text
RFdiffusion can provide the backbone pool. If you have ProteinMPNN and an AF2-style complex predictor, use them downstream to sequence and rank candidates. If you do not, start with backbone triage and preserve the `.trb` files so a later pipeline can recover residue mappings and sampled contigs.
```

## Minimal Backbone Triage Checklist

For each generated design:

- PDB and TRB were created for the requested prefix.
- `.trb` sampled contig matches the requested target/binder architecture.
- Binder chain length is within the requested range.
- Binder is near the hotspot side of the target, not an artifact of the crop boundary.
- Target residues are not missing around the hotspot site.
- Backbone is compact enough for the intended binder class.
- Termini are compatible with peptide, fusion, or expression constraints.
- Candidate remains marked as unvalidated until sequence design and complex prediction are complete.

## Common Reporting Template

When summarizing a binder batch, report:

```text
Generated: N requested, M PDB/TRB pairs present
Architecture: target span(s), binder length range, sampled lengths observed
Hotspots: residues requested, whether included in target crop
Backbone triage: compactness/termini/secondary-structure status if available
External steps: sequence design pending, complex prediction pending
Failures: missing outputs, invalid contigs, model/checkpoint/backend issues
```
