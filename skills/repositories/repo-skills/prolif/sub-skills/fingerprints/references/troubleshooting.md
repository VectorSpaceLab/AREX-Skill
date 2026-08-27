# Fingerprint Troubleshooting

Start every investigation with a tiny serial run and explicit validation. If the smoke run fails, fix the environment or input conversion before tuning fingerprint options.

```bash
python scripts/run_fingerprint_smoke.py --no-progress
```

## RunRequiredError Or Export Before Run

Symptoms:

- `fp.to_dataframe()`, `fp.to_bitvectors()`, or `fp.to_countvectors()` raises ``AttributeError: Please use the `run` method before``.
- Plotting helpers raise `prolif.exceptions.RunRequiredError` with a message asking to run the fingerprint analysis first.

Recovery:

```python
assert not hasattr(fp, "ifp")
fp.run(u.trajectory[:1], lig, prot, n_jobs=1, progress=False)
assert hasattr(fp, "ifp")
df = fp.to_dataframe()
```

Notes:

- `Fingerprint.generate(...)` returns a one-off result and does not populate `fp.ifp`.
- To export a generated single-pair `IFP`, use `plf.to_dataframe({0: ifp}, fp.interactions.keys())`.
- Route plotting-specific `RunRequiredError` debugging to `../../visualization/` after confirming `fp.ifp` exists.

## Empty DataFrame Or Empty Interactions

Symptoms:

- `df.shape[1] == 0`.
- `fp.ifp` has frame keys but each frame maps to an empty `IFP`.
- pandas/prolif warning: `No interaction detected`.

Common causes:

- Ligand or protein selection is empty or not the intended molecule.
- Automatic nearby-residue selection (`residues=None`) found no residues within `vicinity_cutoff`.
- Explicit `residues=[...]` labels do not match ProLIF residue ids.
- Chosen interactions are too restrictive or hydrogens/charges are missing for hydrogen-bond/charged interactions.
- A custom `ignore` predicate filters all residue pairs.

Recovery checklist:

```python
print(lig.n_atoms, prot.n_atoms)
fp = plf.Fingerprint(["Hydrophobic", "HBDonor", "HBAcceptor"], vicinity_cutoff=8.0)
fp.run(u.trajectory[:1], lig, prot, residues=None, n_jobs=1, progress=False)
print(fp.ifp)
print(fp.to_dataframe(drop_empty=False).shape)
```

If this remains empty:

- Try `residues="all"` on a one-frame slice to separate residue-selection failure from interaction absence.
- Print residue ids from prepared molecules in `../../molecules-and-io/` and compare them with explicit residue strings.
- Route interaction thresholds, implicit hydrogens, water bridges, and custom interaction choices to `../../interactions/`.

## Wrong Residue Selection

Symptoms:

- Expected residues do not appear in DataFrame columns.
- `KeyError` when indexing `fp.ifp[frame]["LIG1.G", "ASP129.A"]`.
- A pocket selected on frame 0 misses residues that approach later.

Recovery:

```python
# For dynamic distance selections over a trajectory window:
pocket = plf.select_over_trajectory(
    u,
    u.trajectory[:100],
    "protein and byres around 6 group ligand",
    ligand=lig,
)

fp.run(u.trajectory[:100], lig, pocket, residues=None, n_jobs=1, progress=False)
```

For explicit `residues`, use ProLIF residue ids such as `"ASP129.A"`, not arbitrary MDAnalysis selection text. If residue labels differ unexpectedly, check `use_segid`.

## Multiprocessing Differences

Symptoms:

- Serial `n_jobs=1` succeeds but `n_jobs>1` fails.
- Parallel run hangs, emits child-process conversion errors, or produces results that do not match serial output.
- Behavior differs between `parallel_strategy="chunk"` and `"queue"`.

Recovery workflow:

```python
fp_serial = plf.Fingerprint()
fp_serial.run(u.trajectory[:5], lig, prot, n_jobs=1, progress=False)
df_serial = fp_serial.to_dataframe(drop_empty=False)

for strategy in ["chunk", "queue"]:
    fp_parallel = plf.Fingerprint()
    fp_parallel.run(
        u.trajectory[:5],
        lig,
        prot,
        n_jobs=2,
        parallel_strategy=strategy,
        progress=False,
    )
    df_parallel = fp_parallel.to_dataframe(drop_empty=False)
    print(strategy, df_serial.equals(df_parallel))
```

Guidance:

- Keep `n_jobs=1` for debugging, CI, and very small runs.
- Prefer `parallel_strategy="queue"` when pickling a large MDAnalysis trajectory is expensive or unreliable.
- Prefer `parallel_strategy="chunk"` for small/simple trajectories after confirming it matches serial output.
- Set `PROLIF_N_JOBS` or pass `n_jobs` explicitly rather than relying on machine-dependent defaults.
- If a single `Timestep` is passed, ProLIF runs serially even when `n_jobs>1`.

## `converter_kwargs` Misuse

Symptoms:

- `ValueError: converter_kwargs must be a list of 2 dicts`.
- MDAnalysis RDKit conversion works for ligand but fails for protein, or vice versa.
- Parallel workers fail with converter errors after serial input setup looked valid.

Correct shape:

```python
fp.run(
    u.trajectory[:10],
    lig,
    prot,
    converter_kwargs=({"force": True}, {"force": True}),
    n_jobs=1,
    progress=False,
)
```

Rules:

- Pass exactly two dicts: ligand converter kwargs first, protein converter kwargs second.
- Do not pass one dict for both sides.
- Start with `n_jobs=1`; only parallelize after conversion succeeds serially.
- For input preparation and converter semantics, route to `../../molecules-and-io/`.

## Pickle Portability

Symptoms:

- `Fingerprint.from_pickle(...)` fails after moving between machines or changing package versions.
- Unpickled custom interactions or molecule metadata do not behave as expected.

Guidance:

- ProLIF fingerprint pickles use `dill` and are best for short-term reuse in compatible environments.
- Do not load pickle bytes or files from untrusted sources.
- For durable exports, save `fp.to_dataframe(...)` output in a user-chosen tabular format and record ProLIF, RDKit, and MDAnalysis versions.
- If a pickle fails, rerun from original user inputs or use DataFrame exports rather than editing pickle internals.

## Progress Or Noise In Automated Contexts

Symptoms:

- CI logs contain tqdm progress bars.
- JSON-producing scripts have progress noise on stderr/stdout.
- Notebook-oriented progress display is unwanted in automation.

Recovery:

```python
fp.run(u.trajectory[:10], lig, prot, n_jobs=1, progress=False)
fp.run_from_iterable(pose_iterable, protein_mol, n_jobs=1, progress=False)
```

Use the bundled smoke script with `--no-progress` when machine-readable JSON is required.

## `use_segid` Surprises

Symptoms:

- Residue ids appear as segment-index labels instead of chain ids.
- Explicit residue strings that worked in one input fail in another.
- Water or multi-segment systems change label format between workflows.

What happens:

- `Fingerprint(use_segid=None)` auto-detects whether to use segment indices when inputs have more segments than chains.
- `Molecule.from_mda(..., use_segid=...)` uses the same concept when constructing residue ids.
- `Fingerprint.run(...)` stores the resolved value on `fp.use_segid`.

Recovery:

```python
fp = plf.Fingerprint(use_segid=False)
fp.run(u.trajectory[:1], lig, prot, n_jobs=1, progress=False)
print(fp.use_segid)
print(next(iter(fp.ifp[0])))
```

If explicit residue labels are required, pin `use_segid` consistently during molecule preparation and fingerprint execution. For plotting from a completed fingerprint, pass or reuse `fp.use_segid` in `../../visualization/` workflows.

## Interaction Setup Errors During Fingerprints

Symptoms:

- `NameError` for unknown interaction names.
- `ValueError` for bridged interactions without required settings.
- Implicit-hydrogen parameter errors.

Recovery:

- Route interaction names, `parameters`, `implicit_hydrogens`, `WaterBridge`, and `ignore` predicate setup to `../../interactions/`.
- After setup changes, rerun a one-frame or one-pose fingerprint before full-scale execution.

## Minimal Diagnostic Template

```python
import MDAnalysis as mda
import prolif as plf

u = mda.Universe(topology, trajectory)
lig = u.select_atoms(ligand_selection)
prot = u.select_atoms(protein_selection)

print({"lig_atoms": lig.n_atoms, "prot_atoms": prot.n_atoms})

fp = plf.Fingerprint(["Hydrophobic", "HBDonor", "HBAcceptor"])
fp.run(u.trajectory[:1], lig, prot, residues=None, n_jobs=1, progress=False)

df = fp.to_dataframe(drop_empty=False, dtype=int)
print({
    "frames": sorted(fp.ifp),
    "shape": df.shape,
    "columns": [tuple(map(str, col)) for col in df.columns[:5]],
    "use_segid": fp.use_segid,
})
```

Escalate only after this template identifies whether the failure is input conversion, residue selection, interaction setup, execution/parallelism, or export.
