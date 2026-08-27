# Docker Workflow Reference

This reference distills the AlphaFold Docker setup and launcher behavior into safe planning guidance. Docker builds and container runs are expensive, machine-dependent, and must be performed only when the user explicitly supervises them.

## Prerequisites to Confirm

- Host OS: AlphaFold's documented Docker path targets Linux.
- Docker: Docker Engine must be installed and usable by the invoking user.
- GPU path: install NVIDIA Container Toolkit when GPU inference is expected.
- GPU smoke check: a user-supervised check is `docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi`; successful output should list GPUs.
- Docker image: the documented build operation is `docker build -f docker/Dockerfile -t alphafold .`; do not run this automatically because the build context can become huge if data is nested under the repository.
- Docker launcher Python deps: the official launcher uses `absl-py==1.0.0` and `docker==5.0.0`; the bundled dry-run helper avoids both.
- Output directory: choose an absolute writable host directory before running containers.
- Data directory: choose a host directory outside the AlphaFold source checkout and with enough storage for the selected database mode.

## Launcher Path Mapping

The official Docker launcher mounts every host FASTA and database path under `/mnt/` inside the container. File paths are mounted by their parent directory, while directories are mounted directly.

Important mounted paths produced from `data_dir`:

| Launcher flag | Host path under `data_dir` | Container flag target |
| --- | --- | --- |
| `--data_dir` | `<data_dir>` | `/mnt/data_dir` |
| `--uniref90_database_path` | `uniref90/uniref90.fasta` | `/mnt/uniref90_database_path/uniref90.fasta` |
| `--mgnify_database_path` | `mgnify/mgy_clusters_2022_05.fa` | `/mnt/mgnify_database_path/mgy_clusters_2022_05.fa` |
| `--template_mmcif_dir` | `pdb_mmcif/mmcif_files` | `/mnt/template_mmcif_dir` |
| `--obsolete_pdbs_path` | `pdb_mmcif/obsolete.dat` | `/mnt/obsolete_pdbs_path/obsolete.dat` |
| `--pdb70_database_path` | `pdb70/pdb70` | `/mnt/pdb70_database_path/pdb70` |
| `--small_bfd_database_path` | `small_bfd/bfd-first_non_consensus_sequences.fasta` | `/mnt/small_bfd_database_path/bfd-first_non_consensus_sequences.fasta` |
| `--uniref30_database_path` | `uniref30/UniRef30_2021_03` | `/mnt/uniref30_database_path/UniRef30_2021_03` |
| `--bfd_database_path` | `bfd/bfd_metaclust_clu_complete_id30_c90_final_seq.sorted_opt` | `/mnt/bfd_database_path/bfd_metaclust_clu_complete_id30_c90_final_seq.sorted_opt` |
| `--uniprot_database_path` | `uniprot/uniprot.fasta` | `/mnt/uniprot_database_path/uniprot.fasta` |
| `--pdb_seqres_database_path` | `pdb_seqres/pdb_seqres.txt` | `/mnt/pdb_seqres_database_path/pdb_seqres.txt` |

`--pdb70_database_path` is used for monomer-style presets. `--uniprot_database_path` and `--pdb_seqres_database_path` are used for `--model_preset=multimer`. Reduced database mode uses `small_bfd`; full database mode uses `bfd` and `uniref30`.

## Command Planning Rules

- Require `--data_dir`, `--fasta_paths`, and `--max_template_date`.
- Keep every FASTA basename unique; the official workflow uses each basename to name a target output directory.
- Reject or flag `data_dir` inside the AlphaFold repository because Docker build can copy databases into the build context and become extremely slow.
- Check that all FASTA paths exist and that each required database path exists for the selected `model_preset` and `db_preset`.
- Plan output as `/mnt/output` inside the container, mounted from the host `--output_dir`.
- When `--use_gpu=false`, `--use_gpu_relax` must effectively be false even if `--enable_gpu_relax=true` is requested.
- When `--use_gpu=true`, Docker uses NVIDIA device requests and `NVIDIA_VISIBLE_DEVICES` from `--gpu_devices`.
- The official container environment sets `TF_FORCE_UNIFIED_MEMORY=1` and `XLA_PYTHON_CLIENT_MEM_FRACTION=4.0` to help long proteins fit in GPU memory.

## Bundled Dry-Run Helper

Use [../scripts/plan_docker_command.py](../scripts/plan_docker_command.py) to validate host paths and print:

- a safe `docker run ... alphafold ...` command plan for an already built AlphaFold image;
- the container-internal `run_alphafold` arguments;
- bind-mount source/target mappings;
- GPU/runtime environment notes;
- warnings about missing databases or risky path choices.

The helper does not import Docker, contact the Docker daemon, create directories, or start containers.

## User-Supervised External Operations

When a user explicitly wants to proceed, clearly mark commands like these as external operations:

```bash
docker build -f docker/Dockerfile -t alphafold .
docker run --rm --gpus all \
  --mount type=bind,source=<FASTA_DIR>,target=/mnt/fasta_path_0,ro \
  --mount type=bind,source=<DOWNLOAD_DIR>,target=/mnt/data_dir,ro \
  --mount type=bind,source=<ABS_OUTPUT_DIR>,target=/mnt/output \
  alphafold \
  --fasta_paths=/mnt/fasta_path_0/<FASTA_NAME> \
  --max_template_date=<YYYY-MM-DD> \
  --data_dir=/mnt/data_dir \
  --output_dir=/mnt/output
```

Before presenting such commands, state the storage, GPU, Docker daemon, and runtime dependency assumptions they rely on.
