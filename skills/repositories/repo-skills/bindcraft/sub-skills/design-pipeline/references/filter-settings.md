# Filter settings and rejection semantics

Each checked-in filter preset contains 218 named entries. A scalar entry has
this shape:

```json
"Average_i_pTM": {"threshold": 0.50, "higher": true}
```

The source applies the following semantics:

- `threshold: null` disables that condition. `no_filters.json` keeps the full
  218-key schema but sets all thresholds to null; it is useful for benchmarking,
  not as evidence of a quality design.
- `higher: true` keeps a value when it is greater than or equal to the
  threshold. `higher: false` keeps a value when it is less than or equal to
  the threshold.
- `Average_` values average available AF2 models. `1_` through `5_` are
  model-specific values; only the models selected by the advanced model role
  are populated. Null-disabled model slots are normal. The current filter
  implementation also skips a condition when its computed metric value is
  `None`; investigate an unexpected missing value rather than calling it a
  successful measurement.
- `Average_InterfaceAAs` and `1_`--`5_InterfaceAAs` are nested amino-acid
  counts. Each amino acid has its own threshold/higher pair. Do not replace
  this object with a scalar.

Filter comparisons are applied after MPNN complex prediction, relaxation, and
metric calculation, except for the early AF2 gate described below. A candidate
that fails any enabled condition is copied to `Rejected` and each unmet base
condition increments `failure_csv.csv`. A candidate that passes is copied to
`Accepted`, with its selected relaxed model and associated final CSV row.

## Early AF2 gate

Before Rosetta relaxation and interface scoring, each selected validation model
is checked for the five AF2 fields:

- `pLDDT` and `pTM`: higher is better.
- `i_pTM`: higher is better for interface confidence.
- `pAE` and `i_pAE`: lower is better.

The corresponding `1_...` through `5_...` filter names are read. If any
configured early threshold fails, the current complex predictions are removed,
`failure_csv.csv` is updated, and interface scoring is skipped. This can make
a log look as if Rosetta never ran; that is intended short-circuit behavior.

## Metric groups

The names below are the major groups in the 218-key schema. Direction is a
recommendation for interpreting a filter, not a universal threshold; use the
preset's actual `higher` flag.

| Group | Fields and conservative interpretation |
| --- | --- |
| MPNN | `MPNN_score`, `MPNN_seq_recovery`. Scores depend on the protein and are not generally a standalone quality ranking; sequence recovery compares to the trajectory. |
| AF2 complex confidence | `pLDDT`, `pTM`, `i_pTM`, `pAE`, `i_pAE`, plus `i_pLDDT` and `ss_pLDDT`. The README presents the confidence/error values in normalized form; higher confidence and lower error are preferred. |
| Steric/energy | `Unrelaxed_Clashes`, `Relaxed_Clashes`, `Binder_Energy_Score`, `dG`, and `dG/dSASA`. Clashes and unfavorable energy should generally be lower, but Rosetta scores are protocol-dependent rather than experimental affinity. |
| Interface geometry/size | `ShapeComplementarity`, `PackStat`, `dSASA`, `Interface_SASA_%`, `n_InterfaceResidues`, `n_InterfaceHbonds`, and `InterfaceHbondsPercentage`. Shape/packing/contact size and hydrogen bonds are context-dependent structural indicators. |
| Interface chemistry | `Surface_Hydrophobicity`, `Interface_Hydrophobicity`, `n_InterfaceUnsatHbonds`, `InterfaceUnsatHbondsPercentage`, and `InterfaceAAs`. Excess surface/interface hydrophobicity or unsatisfied buried H-bonds can be undesirable; thresholds should match the preset and target. |
| Secondary structure | `Interface_Helix%`, `Interface_BetaSheet%`, `Interface_Loop%`, `Binder_Helix%`, `Binder_BetaSheet%`, and `Binder_Loop%`. These describe predicted composition, not a guarantee of folding or experimental stability. |
| Structural consistency | `Hotspot_RMSD`, `Target_RMSD`, and `Binder_RMSD`. Lower RMSD generally means closer to the intended/reference arrangement, but alignment/reference choices matter. |
| Binder-alone confidence | `Binder_pLDDT`, `Binder_pTM`, and `Binder_pAE` assess a monomer prediction and should not be read as complex affinity. |

The implementation chooses the accepted relaxed model by highest pLDDT among
available models before applying the filter row. Final ranking, when the target
accepted count is reached, is by descending `Average_i_pTM`. Neither operation
measures binding affinity. In particular, the README warns that i_pTM is useful
as a binary binding predictor but is not a reliable affinity predictor.

## Preset differences

The checked-in presets share the same schema but encode different trade-offs:

- `default_filters.json` is stringent relative to relaxed presets. Its visible
  core thresholds include average pLDDT 0.80, pTM 0.55, i_pTM 0.50, i_pAE <=
  0.35, interface shape complementarity >= 0.60, dSASA >= 1, at least 7
  interface residues and 3 interface H-bonds, and average binder pLDDT 0.80.
- `relaxed_filters.json` lowers average pTM to 0.45 and relaxes several
  interface, hydrophobicity, unsatisfied-H-bond, hotspot-RMSD, and binder-RMSD
  conditions. It can increase yield while changing the experimental risk.
- `peptide_filters.json` uses peptide-oriented interface/RMSD/contact values;
  `peptide_relaxed_filters.json` is more permissive again.
- `no_filters.json` disables every threshold. It does not bypass trajectory
  confidence, clash, contact, duplicate, or early AF2 gates implemented before
  final filtering.

When acceptance is near zero, first identify the failing columns in
`failure_csv.csv` and distinguish an early AF2 failure from a post-relaxation
filter failure. Do not loosen every threshold at once; preserve a copy of the
original filter file and change one justified family at a time.
