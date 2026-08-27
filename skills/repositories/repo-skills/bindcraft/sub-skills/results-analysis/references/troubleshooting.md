# Results troubleshooting

Start read-only: record the output root, modification times, CSV headers, PDB
filenames, settings/filter filenames stored in the rows, and the last run-log
message. Do not rerun or delete files until the discrepancy is classified.

## Missing CSVs or rows

**No CSVs or an empty output root**

- Confirm `design_path` in the target settings and the path passed to the
  process. A SLURM working directory is not necessarily the output directory.
- A process can exit during GPU/import/setup before CSV initialization. Use the
  design-pipeline route for launch/backend diagnostics; do not call an empty
  directory a completed run.
- If CSV headers exist but row counts are zero, check whether trajectories were
  stopped by early pLDDT/clash/contact/hotspot checks or whether the process
  ended before the first surviving trajectory.

**Trajectory PDB but no trajectory row**

The PDB may have been written before relaxation, DSSP, PyRosetta scoring, RMSD,
or CSV insertion completed. Inspect `Trajectory/Relaxed/`, the log, and
`failure_csv.csv`; preserve the PDB and rerun only with an explicit recovery
plan. A stale file with a reused design name can also make a resume appear to
have more progress than the CSV records.

**MPNN PDB but no MPNN row**

Early AF2 filters can remove unrelaxed complex PDBs before a row is written.
Later exceptions can leave a PDB or relaxed PDB without a final CSV row. Check
whether the design has both `MPNN/` and `MPNN/Relaxed/` files, whether the
validation model number is present, and whether the failure counter has the
matching AF2 condition.

**Accepted PDB but no final row or rank**

A passing design is copied to `Accepted/` and appended to the final CSV before
the final threshold-triggered reranking. A partial run can therefore have an
accepted PDB and a blank/missing `Rank`. `Accepted/Ranked/` is populated only
when the requested number of final designs is reached. Match the design stem
before `_model` to the `Design` column; do not invent a rank.

## Inconsistent counts or filenames

Use the following reconciliation table:

| Observation | Likely explanation | Safe action |
|---|---|---|
| More PDBs than CSV rows | Early/partial write, rejected/accepted copy, resumed stale files, or multiple model PDBs | Group filenames by design stem and compare with both CSVs; inspect timestamps. |
| More CSV rows than current PDBs | Cleanup removed unrelaxed files or a later manual deletion occurred | Use relaxed/accepted locations and archives; do not regenerate metrics from a missing structure without recording it. |
| `Accepted/` populated but `Accepted/Ranked/` empty | Final target count not reached or reranking was interrupted | Treat accepted set as provisional and do not report final rank. |
| Rank order differs from file creation order | Expected: final ranking sorts descending `Average_i_pTM` | Verify the rank file's `Design` and metric row, not mtime. |
| `Average_...` differs unexpectedly from per-model values | Only available model dictionaries are averaged; present `None` can become zero | Check model columns and configured model list; report coverage. |
| CSV has dictionary-looking `InterfaceAAs` text | Pandas serialization of amino-acid count dictionaries | Use per-model values/PDB for inspection; do not parse it as a scalar. |
| Files disappeared after a successful message | Advanced cleanup can remove unrelaxed trajectory/complex/binder files or zip plots/animations | Look for `Trajectory/Plots.zip` or `Trajectory/Animation.zip`; preserve relaxed PDBs and CSVs. |

Never resolve a mismatch by renaming PDBs or editing CSVs in place. If a
manually repaired copy is necessary, work on a copy and keep the original
artifacts plus a repair note.

## Reading filter failures

1. Identify the selected filter JSON from the CSV's `Filters` column or the run
   command.
2. In that JSON, map each condition to its `threshold` and `higher` value.
   `threshold: null` is disabled. `higher: true` rejects values below the
   threshold; `higher: false` rejects values above it.
3. Check whether the failure happened in an early AF2 gate or the complete
   post-Rosetta filter pass. Early failures commonly include per-model
   `pLDDT`, `pTM`, `i_pTM`, `pAE`, or `i_pAE` and can prevent interface scoring.
4. Read the corresponding `failure_csv.csv` category, remembering that it is a
   cumulative counter rather than a design-by-design log. Model prefixes are
   normalized to base metric names, and final filter code avoids incrementing
   the same base condition twice for one design.
5. Compare with per-model CSV fields. An `Average_i_pTM` pass does not override
   a failing enabled `1_i_pTM` or `2_i_pTM` condition, and a high average cannot
   prove all model predictions agree.

A low acceptance rate may be a target/site or protocol mismatch, a strict
filter set, early AF2 instability, structural clashes, missing scoring
capabilities, or simply too few trajectories. Do not loosen filters solely to
obtain a desired count; document the changed preset and re-evaluate candidates
under the same comparison protocol. For settings/resource changes, link to
[design pipeline](../../design-pipeline/SKILL.md).

## Missing scoring dependencies

**DSSP missing, not executable, or incompatible**

`calc_ss_percentage` calls the configured DSSP executable on a parsed PDB. A
bad path, missing execute permission, architecture mismatch, or malformed PDB
can stop secondary-structure and pLDDT-derived statistics. Verify the
user-configured DSSP path and run its own help/version probe outside the
pipeline. Do not copy an opaque bundled binary into a generated skill or
replace missing DSSP percentages with guessed values.

**DAlphaBall missing or invalid**

PyRosetta is initialized with a DAlphaBall path and uses DAlphaBall-backed
buried-unsatisfied-H-bond/SASA calculations. Confirm that the path exists, is
executable, and matches the host architecture; then check the PyRosetta log for
the first failing call. DAlphaBall failures can prevent relaxation or interface
scoring. A CPU-only CSV summary remains valid, but Rosetta metrics are
unverified until the dependency is repaired.

**PyRosetta unavailable or unlicensed**

The summarizer does not import PyRosetta and can still count files and inspect
existing CSV values. It cannot recompute or validate `dG`, `dSASA`, `PackStat`,
shape complementarity, interface H-bonds, unsatisfied H-bonds, or relaxation.
Install/use PyRosetta only under the applicable license and the run's supported
environment. Never substitute a different score and label it BindCraft's
Rosetta result.

## High confidence is not affinity

A high `pLDDT`, `pTM`, or `i_pTM` means the prediction is confident or
structurally self-consistent under that AF2 setup. It does not establish
binding affinity, kinetics, specificity, expression, solubility, or correct
biological state. Likewise, a favorable Rosetta `dG` is a model score, not an
experimental free energy. Report `Average_i_pTM` as the pipeline's ranking
criterion and call it a confidence/interface proxy. Experimental
characterization and orthogonal computational checks are still required.

## Disk growth and safe cleanup

Large campaigns can create hundreds or thousands of trajectories, multiple AF2
model PDBs, HTML animations, PNG plots, pickles, and AF2/MPNN weights. Before
cleanup:

1. Stop new design generation and copy the four CSVs plus relaxed accepted and
   trajectory PDBs to a separately named archive.
2. Run the bundled summarizer and save its terminal output outside the results
   tree; it never writes to the input.
3. Confirm every intended ranked candidate has a matching relaxed/accepted PDB
   and record the filter/settings filenames.
4. Prefer the pipeline's configured cleanup or a separately scripted archive;
   check for `Trajectory/Plots.zip` and `Trajectory/Animation.zip` before
   removing source files.
5. Never remove `failure_csv.csv` while diagnosing low acceptance, and never
   delete relaxed PDBs before structural review.

Manual deletion is irreversible and can make CSV/PDB reconciliation impossible.
If disk pressure caused an interrupted run, preserve the partial tree and
resume/repair only through the launch and recovery guidance in the design route.
