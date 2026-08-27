# Metrics, normalization, and scoring

Read the filter JSON used for the run before deciding whether a value is good:
`higher: true` means values below the threshold fail, while `higher: false`
means values above the threshold fail. A `null` threshold is skipped. The
pipeline writes values rounded to two decimal places, so do not use the CSV to
infer precision that was not retained.

## AF2 complex and binder metrics

| Metric | Stored meaning and scale | Direction / caveat |
|---|---|---|
| `pLDDT` | AF2 predicted local confidence, normalized to 0–1 | Higher is confidence, not binding strength. |
| `pTM` | AF2 predicted global model confidence, normalized to 0–1 | Higher is more internally consistent global geometry; it is not an affinity score. |
| `i_pTM` | AF2 interface predicted confidence, normalized to 0–1 | Used for final ordering as `Average_i_pTM`; it is a binding/interface confidence proxy, not a calibrated affinity predictor. |
| `pAE` | Predicted alignment error, normalized to the repository's 0–1 convention (README describes normalization by AF2's `n/31`) | Lower is generally better; confirm the filter direction. |
| `i_pAE` | Interface predicted alignment error in the same normalized convention | Lower is generally better; it can be an early rejection condition. |
| `i_pLDDT` | Mean interface-residue pLDDT divided by 100 | 0–1 confidence summary for residues found at the interface; interface definition is distance-based. |
| `ss_pLDDT` | Mean pLDDT for non-loop binder residues divided by 100 | 0–1 confidence summary for residues assigned helix/sheet by DSSP; zero can mean no qualifying residues or a failed/empty calculation. |
| `Binder_pLDDT`, `Binder_pTM`, `Binder_pAE` | AF2 prediction of the binder alone | Useful for foldability/context comparison, but still confidence/error metrics rather than expression or affinity measurements. |

The complex metrics are captured for each prediction model that runs. The
pipeline may use only a subset of the five model columns (for example, the
validation model list depends on the multimer setting), so blank `3_...` to
`5_...` fields are not automatically failures. `Average_...` is calculated
from the model dictionaries available to the pipeline, not necessarily five
models. Existing `None` values are converted to zero by the average helper;
check per-model columns and file presence before trusting an average with
missing observations.

## MPNN fields

- `MPNN_score` is a ProteinMPNN sequence score whose interpretation depends on
  the protein and model/settings. Do not compare it as a universal energy or
  use it as a stand-alone ranking criterion.
- `MPNN_seq_recovery` is the sequence recovery statistic relative to the input
  trajectory. It describes sequence agreement, not experimental stability or
  affinity. Use the run's filter direction and compare designs of the same
  target/protocol.
- `Sequence`, `InterfaceResidues`, and `InterfaceAAs` are contextual evidence.
  `InterfaceAAs` is a count dictionary for the binder residue types detected at
  the interface; average dictionaries are serialized awkwardly in CSVs and
  are best checked against the corresponding PDB.

## Geometry, clash, and RMSD metrics

- `Unrelaxed_Clashes` and `Relaxed_Clashes` are integer counts from the
  repository's Biopython KD-tree check. The pipeline uses non-hydrogen atoms,
  a 2.4 Å distance threshold, ignores atoms within one residue or the same
  residue, and for the normal side-chain mode counts only cross-chain pairs.
  They are geometry diagnostics, not a force-field energy. Relaxation can
  reduce or sometimes expose clashes; compare both values and inspect the
  PDB.
- `Hotspot_RMSD` is the pipeline's name for an unaligned chain RMSD between the
  trajectory binder and a predicted complex binder. It is reported in Å and is
  intended to indicate whether the redesigned binder moved relative to the
  starting binding site; it is not a direct measurement of hotspot accuracy.
- `Binder_RMSD` is the comparable binder-only prediction versus the trajectory
  binder, in Å. The binder-only structure is first aligned to the trajectory
  when possible, then the RMSD calculation itself does not add a new fit.
- `Target_RMSD` compares predicted complex target chain A with the starting
  target chains using CA atoms and a fitted superposition. It is in Å and is
  truncated to the common residue count by the helper. A low value supports
  target-geometry retention under this comparison; it does not prove a correct
  complex.

RMSD values are target/chain/preprocessing dependent. Different chain IDs,
residue numbering, missing CA atoms, or a changed starting PDB can make values
incomparable. A missing RMSD is not zero.

## Rosetta and interface metrics

These values are calculated on relaxed PDBs when early AF2 filters pass and
PyRosetta plus DAlphaBall are available.

| Metric | Stored meaning and units | Caution |
|---|---|---|
| `Binder_Energy_Score` | PyRosetta total energy for binder chain B, conventionally Rosetta Energy Units (REU) | More negative may be favorable within a matched protocol, but it is not a measured folding free energy. |
| `dG` | PyRosetta interface energy for A_B | REU-like score-function units; score-function, protonation, chain definition, and relaxation matter. Do not call it experimental binding free energy. |
| `dSASA` | Interface delta solvent-accessible surface area | Conventionally Å² in PyRosetta reports; larger contact area is not automatically better. |
| `dG/dSASA` | Interface energy divided by interface area, multiplied by 100 in this pipeline | A scaled score-density value; compare only within the same setup and retain the sign/scale. |
| `ShapeComplementarity` | Rosetta interface shape-complementarity score | Dimensionless packing geometry indicator; not affinity. |
| `PackStat` | Rosetta interface packing statistic | Dimensionless score; use only for relative comparisons under the same scoring setup. |
| `Surface_Hydrophobicity` | Fraction (0–1) of binder surface residues treated as apolar/aromatic by Rosetta | Excess hydrophobicity can hurt solubility; a low value is not proof of a soluble protein. |
| `Interface_SASA_%` | 100 × interface delta SASA / binder SASA | Percentage of binder surface covered by interface, despite some prose calling it a fraction. |
| `Interface_Hydrophobicity` | 100 × hydrophobic interface residues / detected interface residues | Percentage-like 0–100 value; hydrophobic contacts can be useful or nonspecific. |
| `n_InterfaceResidues` | Count of binder residues with any atom within 4.0 Å of target atoms | Depends on chain IDs and the distance definition. |
| `n_InterfaceHbonds` | Count of interface hydrogen bonds from Rosetta | A count, not a strength or lifetime measurement. |
| `InterfaceHbondsPercentage` | 100 × interface H-bonds / interface residue count | Undefined for an empty interface; the code records `None` in that case. |
| `n_InterfaceUnsatHbonds` | Buried unsatisfied heavy-atom H-bond report from Rosetta/DAlphaBall | Lower is generally preferred; tool/version and parameters matter. |
| `InterfaceUnsatHbondsPercentage` | 100 × unsatisfied H-bonds / interface residue count | Undefined for an empty interface; never treat a blank as zero. |

The interface is based on binder chain B versus target chain A in the scoring
helpers. Chain remapping or multi-chain targets can invalidate comparisons.
Rosetta scores are computational diagnostics and should be combined with
structure review and, for real claims, experimental tests.

## Secondary structure and interface composition

`Binder_Helix%`, `Binder_BetaSheet%`, and `Binder_Loop%` are percentages over
DSSP-assigned binder residues. The corresponding `Interface_...%` values are
percentages over residues identified as interacting. Helix includes DSSP H/G/I,
sheet is E, and all other assigned classes are treated as loop. `i_pLDDT` and
`ss_pLDDT` are computed from the same interface/secondary-structure selections.
Missing DSSP, an empty selection, or an unusual PDB can produce zeros or absent
values; see [troubleshooting](troubleshooting.md).

## How to compare candidates without overclaiming

1. Confirm the same target PDB, chain definition, filter preset, AF2 model
   family, and scoring environment.
2. Exclude or separately flag structures with missing relaxed PDBs, unresolved
   clashes, very large RMSD, target deformation, or incomplete model coverage.
3. Use `Average_i_pTM` for the pipeline's reproducible ordering, then inspect
   per-model spread, `i_pAE`, `Hotspot_RMSD`, target/binder RMSDs, interface
   geometry, clashes, and sequence liabilities.
4. Treat a high-confidence/high-`i_pTM` design as a candidate for follow-up,
   not as a high-affinity binder. The README explicitly recommends screening
   more designs because `i_pTM` is not a good affinity predictor even though it
   can be useful as a binary binding signal.
5. Preserve the exact metric table and selection rationale for experimental
   design; do not silently replace the pipeline's rank with a new score.
