# Metrics and Outputs

## Boltz Prediction Output Files

A `boltz predict` output directory has `predictions/<input-name>/` folders. Each prediction folder can contain:

- predicted structures such as `<input-name>_model_0.cif` or `.pdb` depending on `--output_format`;
- `confidence_<input-name>_model_0.json` and additional confidence JSONs for diffusion samples;
- optional `affinity_<input-name>.json` when affinity is requested in the input YAML;
- optional `.npz` arrays for PAE, PDE, and pLDDT when written by the prediction command.

The prediction folder also contains samples ordered by confidence score. Use benchmark metrics only when reference targets are available; otherwise interpret the model-provided confidence and affinity outputs as prediction diagnostics.

## Confidence JSON Fields

Common confidence fields include:

| Field | Meaning | Direction |
| --- | --- | --- |
| `confidence_score` | Aggregate score used to rank predictions; for complexes, combines complex pLDDT and ipTM. | Higher is better |
| `ptm` | Predicted TM-score for the structure or complex. | Higher is better |
| `iptm` | Predicted interface TM-score aggregated over interfaces. | Higher is better |
| `ligand_iptm` | Interface TM-score restricted to protein-ligand interfaces. | Higher is better |
| `protein_iptm` | Interface TM-score restricted to protein-protein interfaces. | Higher is better |
| `complex_plddt` | Average pLDDT confidence for the complex. | Higher is better |
| `complex_iplddt` | Interface-weighted pLDDT. | Higher is better |
| `complex_pde` | Average predicted distance error for the complex in angstroms. | Lower is better |
| `complex_ipde` | Interface-weighted predicted distance error in angstroms. | Lower is better |
| `chains_ptm` | Per-chain predicted TM-score map. | Higher is better |
| `pair_chains_iptm` | Pairwise chain-interface predicted TM-score map. | Higher is better |

Scores such as confidence, pTM, ipTM, and pLDDT are generally bounded from 0 to 1. PDE values are distances in angstroms, so lower values indicate better predicted local geometry.

## Affinity JSON Fields

Affinity JSONs contain ensemble and per-head outputs such as:

| Field | Meaning | Direction |
| --- | --- | --- |
| `affinity_probability_binary` | Predicted probability that the ligand is a binder. Use for binder-vs-decoy or hit-discovery ranking. | Higher is stronger binder likelihood |
| `affinity_pred_value` | Predicted binding-affinity value on the model's `log10(IC50)` scale using IC50 in micromolar. Use for comparing active binders during optimization. | Lower indicates stronger predicted binding |
| `affinity_probability_binary1`, `affinity_probability_binary2` | Individual ensemble-head binder probabilities. | Higher is stronger binder likelihood |
| `affinity_pred_value1`, `affinity_pred_value2` | Individual ensemble-head affinity values. | Lower indicates stronger predicted binding |

Do not rank all compounds by mixing `affinity_pred_value` and `affinity_probability_binary` as if they were the same quantity. The binary probability is for binder likelihood; the affinity value is for relative affinity among active binders.

The docs provide the conversion `y -> (6 - y) * 1.364` for converting an affinity prediction `y` to an energy-like scale when that representation is needed.

## Benchmark Metrics

Legacy benchmark aggregation uses OpenStructure-generated evaluation JSONs and can include:

| Metric | Meaning | Direction |
| --- | --- | --- |
| `lddt` | Local distance difference test score for structural accuracy. | Higher is better |
| `bb_lddt` | Backbone lDDT. | Higher is better |
| `tm_score` | TM-score for global fold similarity. | Higher is better |
| `dockq` or `dockq_>0.23` | Interface/docking quality or fraction above a threshold. | Higher is better |
| `lddt_pli` | Protein-ligand interaction lDDT from ligand comparison. | Higher is better |
| `rmsd` | Root-mean-square deviation. | Lower is better |
| `rmsd<2`, `rmsd<5` | Fraction of ligand RMSDs under threshold. | Higher is better |
| `physical validity` | Boolean or fraction from geometry, stereochemistry, planarity, and clash checks. | Higher is better |

Threshold-derived metrics should retain their threshold in the metric name so downstream aggregation does not confuse them with raw scores.

## Top-1, Oracle, and Average

Use these terms precisely:

- **top-1**: the sample selected by model confidence, not necessarily the best possible sample by a benchmark metric;
- **oracle**: the best sample among generated samples for a metric, using max for higher-is-better metrics and min for lower-is-better metrics;
- **average**: the mean metric across samples.

When reporting top-1 and oracle together, state the number of samples used. For Boltz legacy benchmark comparisons, the documented setup used five samples.

## CSV Aggregation Expectations

Long-form benchmark CSVs are easiest to aggregate when they contain:

- `target`: target or input identifier;
- `tool`: model/tool label, if comparing multiple tools;
- `metric`: metric name;
- `value`: numeric metric value.

Wide-form CSVs can also be summarized if numeric metric columns are present. Preserve metric units and directions in the report, especially for PDE, RMSD, affinity values, and binary affinity probabilities.
