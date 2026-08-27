# BindCraft output artifacts

All paths below are relative to the configured `design_path` output directory.
The exact root is user-configured; use the path in the target settings or the
launch log rather than guessing.

## Directory tree

```text
<design_path>/
├── trajectory_stats.csv
├── mpnn_design_stats.csv
├── final_design_stats.csv
├── failure_csv.csv
├── Accepted/
│   ├── *.pdb
│   ├── Ranked/*.pdb
│   ├── Animation/*
│   ├── Plots/*
│   └── Pickle/*
├── Trajectory/
│   ├── *.pdb                         # unrelaxed hallucinated trajectories
│   ├── Relaxed/*.pdb                 # relaxed trajectory structures
│   ├── Clashing/*.pdb
│   ├── LowConfidence/*.pdb
│   ├── Animation/*
│   ├── Plots/*
│   └── Pickle/*
├── MPNN/
│   ├── *.pdb                         # unrelaxed complex predictions
│   ├── Relaxed/*.pdb                 # relaxed complex predictions
│   ├── Binder/*.pdb                  # binder-only predictions
│   └── Sequences/*.fasta             # optional MPNN FASTA files
└── Rejected/*.pdb
```

`generate_directories` creates these folders even when they remain empty.
Additional `Trajectory/Animation.zip` and `Trajectory/Plots.zip` files may
appear after configured cleanup. A zip archive means matching files were added
and removed from the original folder; it does not mean the run was complete.

## CSV roles and important columns

### `trajectory_stats.csv`

One row is written after a trajectory survives the design-stage termination
checks, relaxation, clash/secondary-structure analysis, and interface scoring.
It records the trajectory name, protocol, length, seed, helicity, target
hotspots, sequence, interface residues, AF2 trajectory metrics, relaxed and
unrelaxed clashes, Rosetta/interface metrics, secondary-structure percentages,
target RMSD, elapsed time, notes, and the settings/filter filenames. A
trajectory can have a PDB without a row if the process stopped before the row
was written; conversely, a row can remain when later MPNN processing failed.

### `mpnn_design_stats.csv`

One row is appended for each MPNN sequence that reaches the full statistics
stage. The first fields are `Design`, `Protocol`, `Length`, `Seed`, `Helicity`,
`Target_Hotspot`, `Sequence`, `InterfaceResidues`, `MPNN_score`, and
`MPNN_seq_recovery`. They are followed, for each metric, by an `Average_...`
column and `1_...` through `5_...` model columns. The complex metrics include
AF2 confidence/error, clash counts, Rosetta/interface scores, secondary
structure, `InterfaceAAs`, `Hotspot_RMSD`, and `Target_RMSD`; binder-only
metrics include `Binder_pLDDT`, `Binder_pTM`, `Binder_pAE`, and `Binder_RMSD`.
Only the configured validation models may contain values; unused model columns
can be blank.

A complex prediction that fails an enabled early AF2 filter is skipped before
relaxation/interface scoring and normally has no MPNN row. The failure counter
still records the failed filter.

### `final_design_stats.csv`

This has `Rank` followed by the same design fields as the MPNN CSV. A design
that passes all final filters is appended with a blank rank immediately. When
the requested number of accepted PDBs is reached, the pipeline rebuilds this
file from matching MPNN rows sorted by descending `Average_i_pTM` and assigns
ranks starting at 1. Therefore a blank `Rank`, missing rows, or a file that is
not ordered by rank indicates an in-progress or interrupted ranking phase, not
necessarily bad designs.

### `failure_csv.csv`

This is a cumulative counter table, initialized from the selected filter JSON.
It contains early trajectory failure categories such as
`Trajectory_logits_pLDDT`, `Trajectory_softmax_pLDDT`,
`Trajectory_one-hot_pLDDT`, `Trajectory_final_pLDDT`, `Trajectory_Contacts`,
`Trajectory_Clashes`, and `Trajectory_WrongHotspot`, plus normalized filter
names and `InterfaceAAs_<AA>` categories. Counts are not a row-per-design
log. A failed model-prefixed condition such as `1_i_pTM` is normalized to the
base metric (`i_pTM`) for the counter; final filter handling similarly counts a
base condition at most once per design. `null` thresholds are skipped.

Use this file to identify bottlenecks, not to reconstruct every design. Compare
its categories with the CSV row counts and the run log because early failures
may never create a complete MPNN row.

## Acceptance, matching, and ranking flow

1. An MPNN sequence is predicted against the complex and as a binder alone.
2. Enabled early AF2 conditions are checked model by model. Failure stops that
   sequence before Rosetta interface scoring.
3. For surviving sequences, the pipeline computes per-model metrics, averages
   available model dictionaries, applies the complete filter JSON, and writes
   an MPNN row.
4. A passing sequence's best relaxed complex PDB is copied to `Accepted/`; the
   selected model is the model with the highest per-model complex `pLDDT`, not
   the model with the highest `Average_i_pTM`.
5. Once `number_of_final_designs` accepted PDBs exists, rows are sorted by
   descending `Average_i_pTM`, matched by the design name embedded before
   `_model`, and copied to `Accepted/Ranked/` as
   `<rank>_<design>_model<model>.pdb`.

Consequently, ranking chooses the ordering metric independently from the model
used for the accepted structure. Verify that each ranked filename has a
matching `Design` row and that the source accepted PDB exists before reporting
a final shortlist.

## Cleanup and retention

Advanced settings can remove unrelaxed trajectory PDBs, unrelaxed MPNN complex
PDBs, binder-only PDBs, and zip trajectory HTML/PNG files. These actions are
intended to reduce disk growth and do not rewrite metric CSVs. Before cleanup,
preserve `final_design_stats.csv`, `mpnn_design_stats.csv`,
`trajectory_stats.csv`, `failure_csv.csv`, all relaxed accepted/trajectory PDBs,
and any plots or animations needed for audit. Make a separate copy or archive
before deleting anything; this analysis route never mutates the output tree.
