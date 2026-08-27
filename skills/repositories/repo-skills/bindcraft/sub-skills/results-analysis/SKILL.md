---
name: results-analysis
description: "Inspect BindCraft output folders and CSVs, explain filter outcomes
  and structure metrics, rank accepted designs conservatively, and recover from
  reporting or scoring failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Analyze BindCraft results

Use this route after a BindCraft run, partial run, or resumed run when the
question is what was produced, why designs were rejected, or which accepted
structures deserve review. Start with the output directory named by the target
settings; do not assume it is inside the BindCraft checkout.

## Fast route

1. Run the read-only [results summarizer](scripts/summarize_bindcraft_results.py)
   on the output directory, then inspect the CSV/PDB counts it reports.
2. Read [output artifacts](references/output-artifacts.md) to reconcile
   `trajectory_stats.csv`, `mpnn_design_stats.csv`, `final_design_stats.csv`,
   `failure_csv.csv`, and the corresponding PDB folders.
3. Use [metrics and scoring](references/metrics-and-scoring.md) to compare
   designs across AF2, MPNN, Rosetta, interface, clash, secondary-structure,
   and RMSD evidence. Rank by `Average_i_pTM` only as BindCraft's structural
   proxy, never as an affinity measurement.
4. If artifacts disagree or a metric is absent, follow
   [troubleshooting](references/troubleshooting.md) before deleting files or
   changing filters.

## Applicability and boundaries

- This route can summarize existing files without PyRosetta, CUDA, AF2 weights,
  DSSP, or DAlphaBall. Metric recomputation may require those dependencies.
- It does not author target JSON or choose GPU/SLURM resources. For input
  structure and chain/hotspot questions, use
  [target preparation](../target-preparation/SKILL.md); for launching, stopping,
  or resource setup, use [design pipeline](../design-pipeline/SKILL.md).
- Treat a complete-looking CSV as evidence of recorded processing, not proof
  that a full campaign finished. A skipped or interrupted run is not verified
  by inspection alone.
- Report the exact output path, CSV used, row/PDB correspondence, filter preset,
  and missing prerequisites in any handoff. Keep source checkout paths and
  verification artifacts out of user-facing runtime instructions.

## Selection discipline

Use `final_design_stats.csv` and `Accepted/Ranked/` when ranking has completed;
otherwise use the available MPNN rows and `Accepted/` PDBs, explicitly labeling
that view as provisional. Prefer several complementary metrics and inspect the
actual relaxed PDBs. Do not infer experimental affinity, specificity,
expressibility, or success from AF2 confidence, Rosetta energy, or a filter pass.

The bundled script is deliberately read-only and uses only Python's standard
library. It is a triage aid, not a replacement for structural inspection or a
new scoring implementation.
