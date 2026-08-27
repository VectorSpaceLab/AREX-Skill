# Boltz Raw-Data Preprocessing Workflows

This reference distills the Boltz raw-data pipeline into safe, self-contained guidance. The original processing scripts are intentionally not bundled here because they require external downloads, Redis databases, mmseqs, multiprocessing, and dataset-scale writes.

## Pipeline Overview

Run the stages in this order when recreating training/evaluation data from raw sources:

1. Prepare extra processing dependencies and external tools.
2. Build or obtain CCD ligand artifacts.
3. Build sequence and ligand clusters.
4. Obtain raw MSAs named by query-sequence hash.
5. Process raw MSAs into compressed Boltz `.npz` files using a taxonomy Redis DB.
6. Process raw mmCIF structures into target `structures/`, `records/`, and `manifest.json` using a CCD Redis DB and the cluster map.
7. Wire processed target/MSA/symmetry paths into the training config.

If the user only wants standard Boltz training, prefer preprocessed archives when available. Re-run raw preprocessing only for custom datasets or reproducibility audits.

## Processing Dependencies

Boltz itself imports as package `boltz`. The extra preprocessing requirements are:

- Python packages: `gemmi`, `pdbeccdutils`, `redis`, `scikit-learn`, and `p_tqdm`.
- External executables/services: `mmseqs` for protein clustering, and `redis-server` for sharing large taxonomy or CCD dictionaries across worker processes.
- Existing Boltz package dependencies used by the processing code include `numpy`, `pandas`, `rdkit`, `biopython`, and `tqdm`.

Check availability without starting expensive work:

```bash
python -c "import gemmi, pdbeccdutils, redis, sklearn, p_tqdm"
mmseqs version
redis-server --version
```

## Stage 1: CCD Dictionary And Symmetries

Purpose:

- Read the wwPDB Chemical Component Dictionary `components.cif`.
- Generate or select ligand conformers with RDKit/pdbeccdutils.
- Compute ligand self-symmetry permutations and store them on molecule properties.
- Write `ccd.pkl` plus per-component molecule pickles and `results.csv`.

Important inputs and outputs:

- Input: `components.cif` from the wwPDB monomer dictionary.
- Output directory: contains `mols/`, `results.csv`, and `ccd.pkl`.
- `ccd.pkl` is a Python pickle mapping CCD codes to RDKit molecules with Boltz-required properties.
- The same molecule/symmetry data is also the conceptual source for the ligand symmetry pickle consumed by training.

Reference command pattern:

```bash
python ccd.py --components components.cif --outdir ./ccd --num_processes 8
```

Safety notes:

- The script uses multiprocessing and may consume substantial CPU and memory.
- Treat pickle files as trusted artifacts; do not load pickles from untrusted sources.
- If a user only needs training with known public data, downloading the provided CCD/symmetry artifacts is usually safer than regenerating them.

## Stage 2: Sequence And Ligand Clustering

Purpose:

- Split sequences into proteins, short protein-like sequences, and nucleotide sequences.
- Cluster proteins at 40% sequence identity with mmseqs.
- Assign each nucleotide sequence, each short sequence, and each ligand CCD code to its own cluster.
- Write `clustering.json` used by structure processing and training sampling.

Important inputs and outputs:

- Input FASTA: all polymer sequences in the target structural dataset, such as RCSB `pdb_seqres.txt`.
- Input CCD pickle: `ccd.pkl` from the CCD stage.
- mmseqs executable path: `mmseqs` or an explicit executable path.
- Output: `clustering.json`, plus mmseqs temporary/intermediate files such as `proteins.fasta`, `clust_prot*`, and `tmp/`.

Reference command pattern:

```bash
python cluster.py \
  --sequences pdb_seqres.txt \
  --ccd ./ccd/ccd.pkl \
  --mmseqs mmseqs \
  --outdir ./clustering
```

Key implementation details:

- Protein sequence IDs are SHA-256 hashes of the raw sequence string.
- Short protein-like sequences shorter than 10 residues are not sent through mmseqs; each gets its own cluster ID.
- DNA/RNA-like sequences made only of `A`, `C`, `G`, `T`, `U`, and `N` each get their own cluster ID.
- Ligands are keyed by CCD code and cluster to themselves.

Safety notes:

- mmseqs writes a temporary database under the output directory; ensure the filesystem has enough space and fast local I/O.
- If `mmseqs` is missing or shadowed by the wrong binary, clustering fails before structure processing can attach cluster IDs.

## Stage 3: Raw MSA Acquisition And Naming

Purpose:

- Boltz training expects processed MSA `.npz` files that can be found by chain `msa_id` values in target records.
- The public PDB/OpenFold workflow names raw MSA files by SHA-256 hash of the query sequence.

Hash function:

```python
import hashlib

hashlib.sha256(sequence.encode()).hexdigest()
```

Expected raw file names:

- `<sha256>.a3m`
- `<sha256>.a3m.gz`

MSA header expectations:

- ColabFold-style UniRef rows should begin with `>UniRef100_UNIREFID`.
- MSA processing uses the UniRef identifier to look up taxonomy IDs in the Redis taxonomy DB.
- Rows without recognized taxonomy get taxonomy `-1`, which reduces paired-MSA quality for multi-chain examples.

Safety notes:

- Public raw MSA archives are large: the PDB raw MSA archive is around 130 GB and the OpenFold raw MSA archive is around 88 GB, each needing additional extraction space before the tar can be removed.
- Validate naming and file extensions before processing. The processor searches recursively for `*.a3m*`, so unexpected suffixes can be included or skipped depending on naming.

## Stage 4: Process MSAs

Purpose:

- Parse raw A3M/A3M.GZ files into compact compressed NumPy files.
- Deduplicate identical sequences after removing gaps.
- Encode residues, deletion runs, and taxonomy IDs.
- Limit the number of sequences per MSA.

Redis requirement:

- Start Redis with the taxonomy DB, usually on port `7777`.
- Wait for Redis to report readiness before launching workers.

Reference service pattern:

```bash
redis-server --dbfilename taxonomy.rdb --port 7777
```

Reference processing pattern:

```bash
python msa.py \
  --msadir /path/to/raw_msa \
  --outdir /path/to/processed_msa \
  --redis-host localhost \
  --redis-port 7777 \
  --max-seqs 16384
```

Output:

- One compressed `.npz` per raw MSA file, named from the input stem.
- Arrays correspond to Boltz `MSA`: `sequences`, `deletions`, and `residues`.

Safety notes:

- The script connects to Redis but does not start it.
- Use a taxonomy DB for this stage, not the CCD DB.
- Wrong Redis port or wrong DB can silently degrade taxonomy annotation or fail with missing keys/connection errors.

## Stage 5: Process RCSB/mmCIF Structures

Purpose:

- Parse `.cif` and `.cif.gz` structures with gemmi and RDKit CCD references.
- Build Boltz `Structure` arrays and `Record` JSON metadata.
- Apply static filters for excluded ligands, polymer length, all-unknown polymers, large CA gaps, and clashing chains.
- Attach cluster IDs from `clustering.json`.
- Write a processed target directory that the training data module can load.

Redis requirement:

- Start Redis with the CCD DB, usually on port `7777`.
- Use the CCD Redis DB for structure processing; do not reuse the taxonomy DB for this stage.

Reference service pattern:

```bash
redis-server --dbfilename ccd.rdb --port 7777
```

Current-code command pattern:

```bash
python rcsb.py \
  --datadir /path/to/mmcif_files \
  --clusters ./clustering/clustering.json \
  --outdir /path/to/processed_targets \
  --use-assembly \
  --max-file-size 7000000 \
  --redis-host localhost \
  --redis-port 7777
```

Docs/code note:

- Some Boltz docs or older notes may show `--cluster`; current argparse uses `--clusters`.
- The parser exposes `--max-file-size`; if behavior seems inconsistent in a local checkout, inspect whether the current `fetch(...)` call forwards the parsed value before assuming large files are actually skipped.

Output:

- `structures/<target_id>.npz`: compressed arrays for atoms, bonds, residues, chains, connections, interfaces, and mask.
- `records/<target_id>.json`: per-target metadata with chain, interface, validity, and structure info.
- `manifest.json`: list/dict of all parsed records, loadable by Boltz `Manifest.load`.

Safety notes:

- Full RCSB processing is network/storage/CPU heavy and should not be run as a casual smoke test.
- Use `--num-processes` conservatively on shared machines.
- Confirm file extensions: the script looks for `*.cif*`, so `.cif` and `.cif.gz` are expected.
- Confirm output ownership before reusing an existing output directory; the script skips already-existing `structures` and `records` pairs.

## Stage 6: Training Config Handoff

Before routing to training, verify:

- `data.datasets[].target_dir` points at the processed target directory containing `manifest.json` and `structures/`.
- `data.datasets[].msa_dir` points at the processed MSA directory containing `.npz` files keyed by chain MSA IDs.
- `data.symmetries` points at the ligand symmetry pickle.
- Multi-dataset configs keep each target directory paired with the matching MSA directory.
- Optional `split` and `manifest_path` entries are valid relative to the training invocation context or are absolute paths chosen by the user.

Use `scripts/boltz_preprocessing_checklist.py` from this sub-skill for a safe preflight check.
