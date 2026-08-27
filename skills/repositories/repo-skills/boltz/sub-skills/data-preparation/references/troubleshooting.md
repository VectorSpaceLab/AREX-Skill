# Boltz Data Preparation Troubleshooting

Use this guide to diagnose preprocessing failures before routing a user to training or prediction.

## Quick Triage Order

1. Run the bundled checklist script against the user's current paths.
2. Confirm which stage the user has completed: CCD, clustering, raw MSA acquisition, MSA processing, mmCIF processing, or training-config wiring.
3. Check whether the failure is from missing local files, missing external tools, Redis DB/port mismatch, dataset scale, or a docs/code flag mismatch.
4. Avoid launching original preprocessing scripts until prerequisites and output locations are explicit.

## Missing mmseqs

Symptoms:

- `FileNotFoundError`, shell `mmseqs: command not found`, or a failed `easy-cluster` subprocess during clustering.
- No `clust_prot_cluster.tsv` appears in the clustering output directory.
- `clustering.json` is absent, causing structure processing to fail or assign missing cluster IDs.

Checks:

```bash
mmseqs version
which mmseqs
```

Next steps:

- Install mmseqs2 through the user's preferred package manager or provide the explicit executable path with `--mmseqs`.
- Re-run only the clustering stage after confirming `pdb_seqres.txt` and `ccd.pkl` are present.
- Do not proceed to RCSB/mmCIF processing without a valid `clustering.json` unless the user intentionally accepts missing cluster IDs.

## Redis Not Ready Or Wrong Port

Symptoms:

- `Connection refused`, Redis timeout, or worker failures at the start of MSA or structure processing.
- MSA taxonomy annotations are all missing or unexpectedly `-1`.
- Structure parsing reports missing CCD components even though the DB file exists.

Checks:

```bash
redis-cli -p 7777 ping
redis-cli -p 7777 info persistence
```

Next steps:

- Start Redis explicitly with the DB needed for the current stage.
- Use `taxonomy.rdb` for `msa.py`; use `ccd.rdb` for `rcsb.py`/mmCIF structure processing.
- Wait for Redis to print `Ready to accept connections` before launching parallel workers.
- If another Redis instance already uses the port, choose a different port and pass the same `--redis-port` to the processing script.

Important distinction:

```text
MSA processing      -> taxonomy.rdb -> taxonomy lookup for UniRef rows
Structure processing -> ccd.rdb      -> CCD molecule lookup for ligands
```

## Wrong Redis DB Filename

Symptoms:

- Redis `PING` works, but MSA taxonomy or CCD ligand lookups fail.
- MSA processing completes but paired-MSA quality is poor because taxonomy annotations are absent.
- mmCIF processing skips ligands or fails on components that should exist.

Next steps:

- Stop or isolate the Redis instance on that port.
- Restart with the correct `--dbfilename` from the directory containing that DB file.
- Re-run the affected stage; do not assume existing partial outputs are valid.

## `.a3m` / `.a3m.gz` Naming Problems

Symptoms:

- MSA processing prints that it found zero or too few MSAs.
- Training cannot find `msa_dir/<msa_id>.npz`.
- Chains silently use dummy/unpaired MSA behavior or training logs repeatedly fail to load inputs.

Checks:

- Raw files should end in `.a3m` or `.a3m.gz` and are discovered recursively by the MSA processor.
- For the public raw-data workflow, each filename stem should be the SHA-256 hash of the query sequence.
- Processed outputs should be named `<same_stem>.npz`.
- Chain records should use `msa_id` values matching those stems.

Next steps:

- Rename raw MSA files before processing, or rewrite target record `msa_id` values only if the dataset has a controlled manifest-generation process.
- If the user used a non-ColabFold pipeline, ensure UniRef rows use headers like `>UniRef100_UNIREFID` when taxonomy pairing is desired.

## Missing Taxonomy DB

Symptoms:

- `redis-server --dbfilename taxonomy.rdb` cannot start from the chosen directory.
- MSA processing cannot connect to useful taxonomy data.
- Multi-chain MSA pairing has little or no taxonomy-based pairing.

Next steps:

- Obtain the trusted taxonomy Redis DB artifact used for Boltz preprocessing, or document that taxonomy pairing will be unavailable.
- Keep `taxonomy.rdb` separate from `ccd.rdb` and from default Redis dump files.
- Re-run MSA processing after Redis is restarted with the correct DB.

## Missing CCD DB Or CCD Pickle

Symptoms:

- CCD preprocessing did not produce `ccd.pkl`.
- Clustering cannot add ligand CCD codes.
- RCSB/mmCIF processing cannot parse ligand/nonpolymer residues or reports missing components.
- Training symmetry loading fails for ligand symmetry pickle.

Checks:

- `ccd.pkl` is needed by clustering.
- `ccd.rdb` is needed by structure-processing workers.
- `symmetry.pkl` is needed by training config `data.symmetries`.

Next steps:

- Prefer trusted provided artifacts if the user does not need to regenerate CCD data.
- If regenerating, run the CCD stage from `components.cif` and inspect `results.csv` for failed components.
- Do not load untrusted CCD/symmetry pickle artifacts.

## Disk Requirements And Archive Extraction

Symptoms:

- `No space left on device`, partial tar extraction, abruptly missing MSA files, or corrupted processed outputs.
- Very slow preprocessing caused by network-mounted or quota-limited storage.

Planning rules:

- Full preprocessed training archives can require around 250 GB.
- Raw PDB MSA archive is around 130 GB and needs roughly another 130 GB while extracted.
- Raw OpenFold MSA archive is around 88 GB and needs roughly another 88 GB while extracted.
- Full RCSB/mmCIF processing can require substantial additional temporary and output space.

Next steps:

- Use local scratch storage when possible.
- Check available space before download and before extraction.
- Avoid running multiple dataset-scale stages into the same small filesystem.

## Max-File-Size Skips And Very Large mmCIFs

Symptoms:

- Some expected target IDs are missing from `manifest.json`.
- Logs mention files excluded due to size.
- Very large complexes cause memory pressure or parser crashes.

Next steps:

- Confirm the exact `--max-file-size` value and units; it is a byte threshold.
- Decide whether skipped entries are acceptable for the user's training/evaluation goal.
- If a local code version exposes the flag but does not appear to apply it, inspect the current `fetch(...)` call in `rcsb.py` and treat the behavior as checkout-specific.
- Increase the threshold only when disk/RAM budget and runtime are acceptable.

## `--cluster` Versus `--clusters`

Symptoms:

- `rcsb.py` exits with an unrecognized-argument error for `--cluster`.
- The user copied a command from older docs or notes.

Next steps:

- Use current-code argparse spelling: `--clusters /path/to/clustering.json`.
- If working with a different Boltz version, inspect `python rcsb.py --help` before rerunning.

## Processed Targets But Missing MSA Hashes

Symptoms:

- `target_dir/manifest.json` and `structures/` exist, but training fails while loading MSA files.
- Chain records contain non-empty `msa_id` values, but `msa_dir/<msa_id>.npz` is missing.
- The user processed structures but skipped raw MSA acquisition or MSA conversion.

Diagnosis:

- Structure processing and MSA processing are independent stages.
- The training loader only loads MSA files by `record.chains[].msa_id`; it does not generate them.

Next steps:

- Inspect a small sample of records and list their non-empty `msa_id` values.
- Compare those IDs to processed MSA filenames.
- Process raw A3M files with `msa.py` into the configured `msa_dir`, or update the training config to point at the correct processed MSA directory.
- If the dataset intentionally lacks MSAs for some chains, document expected dummy/unpaired behavior and performance impact before training.

## Training Config Points At The Wrong Directories

Symptoms:

- `Failed to load input for <id>` repeats in training logs.
- `manifest.json` loads, but `structures/<id>.npz` or MSA files are missing.
- The first dataset works but a second dataset fails.

Checks:

- `data.datasets[].target_dir` should contain `manifest.json`, `records/`, and `structures/`.
- `data.datasets[].msa_dir` should contain `.npz` files named by chain `msa_id`.
- `data.symmetries` should be a trusted readable pickle.
- In multi-dataset configs, each `target_dir` must be paired with its own matching `msa_dir`.

Next steps:

- Run the bundled checklist with the exact paths from the config.
- Correct path pairs before changing model, sampler, cropper, or GPU settings.
- Route to the training sub-skill only after data paths pass preflight.

## Original Scripts Are Skipped As Native Candidates

The original process scripts are useful evidence but unsafe as default native verification because they can start dataset-scale work, depend on external services, read/write Redis DBs, and require large downloads. Safe native candidates for this sub-skill are:

- `python scripts/boltz_preprocessing_checklist.py --help`
- Checklist runs against small temporary directories or user-provided paths where the user expects read-only inspection.

Do not run full `ccd.py`, `cluster.py`, `msa.py`, or `rcsb.py` as a routine verification step.
