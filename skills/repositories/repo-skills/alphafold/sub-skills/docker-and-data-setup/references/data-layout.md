# Data Layout Reference

AlphaFold data setup combines model parameters with large sequence/template databases. Treat download and update commands as user-supervised external operations because they can transfer hundreds of GB and expand to TB-scale storage.

## Acquisition Modes

| Mode | Intended use | BFD-related directory | Notes |
| --- | --- | --- | --- |
| `full_dbs` | Highest-fidelity/default database setup | `bfd/` plus `uniref30/` | Full setup is about 556 GB downloaded and about 2.62 TB uncompressed. |
| `reduced_dbs` | Faster/lower-resource monomer workflows | `small_bfd/` | Requires matching prediction flag `--db_preset=reduced_dbs`; documented requirements are about 8 vCPUs, 8 GB RAM, and 600 GB disk. |

`download_all_data.sh` also downloads model parameters. The selected `db_preset` during prediction must match the data mode: `reduced_dbs` requires `small_bfd`, while `full_dbs` requires `bfd` and `uniref30`.

## Expected Directory Layout

| Directory/file | Required for | Approximate size notes | Created by |
| --- | --- | --- | --- |
| `params/` | all model presets | about 5.3 GB downloaded | AlphaFold parameter download |
| `uniref90/uniref90.fasta` | all workflows | about 34 GB download, 67 GB expanded | UniRef90 download |
| `mgnify/mgy_clusters_2022_05.fa` | all workflows | about 67 GB download, 120 GB expanded | MGnify download |
| `pdb_mmcif/mmcif_files/` | template search | about 43 GB download, 238 GB expanded | PDB mmCIF rsync/download |
| `pdb_mmcif/obsolete.dat` | template search | small metadata file | PDB mmCIF download |
| `pdb70/pdb70` | monomer-style presets | about 19.5 GB download, 56 GB expanded | PDB70 download |
| `bfd/bfd_metaclust_clu_complete_id30_c90_final_seq.sorted_opt` | `full_dbs` | about 271.6 GB download, 1.8 TB expanded | BFD download |
| `uniref30/UniRef30_2021_03` | `full_dbs` | about 52.5 GB download, 206 GB expanded | UniRef30 download |
| `small_bfd/bfd-first_non_consensus_sequences.fasta` | `reduced_dbs` | about 9.6 GB download, 17 GB expanded | Small BFD download |
| `uniprot/uniprot.fasta` | multimer | about 53 GB download, 105 GB expanded | UniProt TrEMBL/SwissProt merge |
| `pdb_seqres/pdb_seqres.txt` | multimer | about 0.2 GB | PDB SeqRes download/filter |

## Official Download Sequence

The all-data workflow performs these actions in order:

1. Download AlphaFold model parameters into `params/`.
2. Download `small_bfd/` for `reduced_dbs`, or `bfd/` for `full_dbs`.
3. Download `mgnify/`.
4. Download `pdb70/`.
5. Download and flatten PDB mmCIF files into `pdb_mmcif/mmcif_files/`, plus `obsolete.dat`.
6. Download `uniref30/`.
7. Download `uniref90/`.
8. Download and merge UniProt TrEMBL/SwissProt into `uniprot/uniprot.fasta`.
9. Download/filter PDB SeqRes into `pdb_seqres/pdb_seqres.txt`.

The all-data script checks for `aria2c` and `rsync`. Individual downloads generally need `aria2c`; PDB mmCIF also needs `rsync`.

## Incremental Update Order

For a previous installation, update in this order:

1. Update AlphaFold code separately under user supervision.
2. Refresh UniProt: remove `uniprot/`, then run the UniProt downloader.
3. Refresh UniRef30: remove old `uniclust30/` or stale UniRef30 data as applicable, then run the UniRef30 downloader.
4. Refresh UniRef90: remove `uniref90/`, then run the UniRef90 downloader.
5. Refresh MGnify: remove `mgnify/`, then run the MGnify downloader.
6. Refresh PDB data as a matched pair: remove `pdb_mmcif/`, run the PDB mmCIF downloader, then run the PDB SeqRes downloader.
7. Refresh parameters: remove `params/`, then run the AlphaFold parameter downloader.
8. Re-plan prediction commands with the matching `db_preset`, `model_preset`, and `max_template_date`.

Keep PDB mmCIF and PDB SeqRes from the same update window. Mismatched dates can create template-search and multimer failures.

## Bundled Dry-Run Helper

Use [../scripts/plan_data_downloads.py](../scripts/plan_data_downloads.py) to print a safe setup or update plan:

```bash
python sub-skills/docker-and-data-setup/scripts/plan_data_downloads.py --download-dir /data/alphafold --mode reduced_dbs
python sub-skills/docker-and-data-setup/scripts/plan_data_downloads.py --download-dir /data/alphafold --mode full_dbs --update-from 2.3.0
```

The helper prints prerequisites, expected directories, mode-specific actions, update ordering, and warnings. It does not run `aria2c`, `rsync`, `tar`, `gunzip`, `find`, `mv`, `rm`, or network calls.

## User-Supervised External Operations

If the user explicitly requests download execution guidance, describe the official operations as external work rather than running them: all-data setup, reduced-database setup, UniProt refresh, UniRef30 refresh, UniRef90 refresh, MGnify refresh, PDB mmCIF refresh, PDB SeqRes refresh, and model-parameter refresh. Use the bundled planner output to provide ordering, target directories, prerequisites, and warnings.

Always pair external operations with storage, bandwidth, permission, and prerequisite warnings. Do not assume this runtime skill has access to the original repository scripts; use this reference and the bundled planner as the self-contained source of setup facts.
