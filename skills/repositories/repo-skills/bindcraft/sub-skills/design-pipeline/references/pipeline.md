# BindCraft control flow and stop gates

## Preconditions and initialization

`bindcraft.py` imports the package surface and checks `jax.devices()` before
parsing its three command-line arguments. A GPU must be visible; `--help` can
therefore still fail in an incomplete import/GPU environment. The accepted
flags are:

- `--settings` / `-s`: required target-settings JSON.
- `--filters` / `-f`: optional filter JSON, defaulting to
  `./settings_filters/default_filters.json` when the program receives no value.
- `--advanced` / `-a`: optional advanced JSON, defaulting to
  `./settings_advanced/default_4stage_multimer.json` when the program receives
  no value.

The program loads all three JSONs, chooses AF2 model roles, fills empty utility
paths from the installation context, creates the output tree, creates four
CSV files if absent, initializes PyRosetta with DAlphaBall, and enters the
campaign loop. The target JSON contract and PDB checks belong to
[../../target-preparation/SKILL.md](../../target-preparation/SKILL.md).

With `use_multimer_design: true`, design uses model indices 0--4 and complex
validation uses indices 0--1 with the non-multimer validation setting. With it
false, design uses indices 0--1 and validation uses indices 0--4 with multimer
validation. This is a model-role choice, not a guarantee that all models fit
in memory for every target.

## One trajectory

For each iteration, BindCraft samples a random seed below 999999, samples an
integer binder length inclusively between the two target `lengths`, and creates
a name such as `binder_l90_s12345`. It runs AF2 binder hallucination with the
selected target chains/hotspots, design model role, recycles, template masks,
AA exclusions, contact losses, confidence losses, optional radius-of-gyration,
interface-pTM, termini, and helicity losses.

The trajectory is then checked before expensive optimization:

- In the final hallucination structure, any CA clash at the implementation's
  2.5 distance test moves the PDB to `Trajectory/Clashing` and records
  `Trajectory_Clashes`.
- A final binder pLDDT below `0.70` moves it to
  `Trajectory/LowConfidence` and records `Trajectory_final_pLDDT`.
- Fewer than three detected interface contacts also moves it to
  `Trajectory/LowConfidence` and records `Trajectory_Contacts`.
- A trajectory that passes these gates is relaxed and scored. If no interface
  residues are found after scoring, MPNN optimization is skipped.

The 4stage implementation also has internal confidence gates while designing:
its initial logits, softmax, and one-hot stages must each have best-binder
pLDDT above `0.65` before the next stage is attempted. Failures are recorded as
`Trajectory_logits_pLDDT`, `Trajectory_softmax_pLDDT`, or
`Trajectory_one-hot_pLDDT`. `optimise_beta` can add iterations/recycles when
beta content exceeds the implementation's 15% trigger; it is not a promise of
beta-sheet quality.

## Algorithm families

The advanced `design_algorithm` selects one implementation:

| Value | Actual sequence of operations | Trade-off |
| --- | --- | --- |
| `2stage` | Gradient/logit-like optimization followed by PSSM semigreedy mutations; uses `soft_iterations`, `greedy_iterations`, and `greedy_percentage`. | Faster and less extensive. |
| `3stage` | Soft/logit, temporary softmax, then one-hot optimization using `soft_iterations`, `temporary_iterations`, and `hard_iterations`. | Standard staged design; common in peptide presets. |
| `4stage` | A 50-iteration logits prescreen, remaining logits iterations, softmax, one-hot, then optional PSSM semigreedy optimization. | Default extensive route; has the 0.65 intermediate gates and optional beta branch. |
| `greedy` | Semigreedy random mutations that improve loss, with `greedy_iterations` and a length-derived mutation count. | Less memory intensive, slower and generally less efficient. |
| `mcmc` | The implementation's MCMC mutation routine with `greedy_iterations`, mutation count from `greedy_percentage`, temperature 0.01, and a half-life derived from iterations/5. | Less memory intensive but slower; implementation-sensitive. |

Do not infer that `2stage` or `3stage` skips all confidence checks: the final
clash, pLDDT, and contact gates still apply. An unsupported algorithm reaches
the source's error path and must be corrected before launch.

## MPNN and validation

For a passing trajectory and `enable_mpnn: true`, BindCraft identifies the
interface, samples `num_seqs` ProteinMPNN sequences at `sampling_temp` with
`backbone_noise`, removes duplicate sequences already present in the MPNN CSV,
and optionally rejects sequences containing `omit_AAs` when
`force_reject_AA` is true. `mpnn_fix_interface` fixes the hallucinated
interface positions; false permits MPNN to redesign them. It processes at most
`max_mpnn_sequences` accepted sequences from one trajectory.

Each candidate is predicted as a complex for the selected validation models and
as a binder monomer. The initial per-model AF2 checks cover pLDDT, pTM, i_pTM,
pAE, and i_pAE. If any configured non-null early AF2 threshold fails, the
candidate's complex PDBs are removed, relaxation/interface scoring is skipped,
and the failure counter is updated. Passing candidates are relaxed, scored with
PyRosetta and structural helpers, compared against the filter JSON, and copied
to `Accepted` or `Rejected`. The accepted model is the relaxed model with the
highest pLDDT among available validation models, not a measured affinity
winner.

## Stop, rank, and resume behavior

At the top of every loop, the program checks accepted PDB count against
`number_of_final_designs`. Once reached, it sorts MPNN rows by descending
`Average_i_pTM`, rebuilds `Accepted/Ranked`, writes `final_design_stats.csv`,
and optionally zips trajectory animations/plots. Before starting a new
trajectory it checks the relaxed, low-confidence, clashing, and normal
trajectory folders for the generated name. The `max_trajectories` limit counts
PDBs in `Trajectory/Relaxed`; `false` disables that limit.

When `enable_rejection_check` is true and `trajectory_n` is at least
`start_monitoring`, the source compares newly tracked `accepted_designs /
trajectory_n` with `acceptance_rate`. If below the configured rate, it prints a
warning and stops. This is an early campaign stop, not proof that the target is
undesignable. A rerun against the same output directory reuses existing files
where source checks find them and starts fresh counters; review CSVs and
settings before resuming, and do not merge incompatible campaigns.

Typical folders are `Accepted`, `Accepted/Ranked`, `Rejected`, `Trajectory`
(with `Relaxed`, `Clashing`, `LowConfidence`, `Plots`, `Animation`, and
optional `Pickle`), `MPNN` (with relaxed, binder, and sequence outputs), plus
`trajectory_stats.csv`, `mpnn_design_stats.csv`, `final_design_stats.csv`, and
`failure_csv.csv`. See [../../results-analysis/SKILL.md](../../results-analysis/SKILL.md)
for post-run interpretation; this route deliberately does not reproduce its
score tables.
