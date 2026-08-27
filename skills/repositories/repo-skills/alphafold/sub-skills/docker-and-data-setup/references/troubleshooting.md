# Docker and Data Troubleshooting

Use this reference to diagnose setup issues without running expensive Docker, download, or prediction operations automatically.

## Common Failures

| Symptom | Likely cause | Safe response |
| --- | --- | --- |
| Docker build is extremely slow or copies huge files | `data_dir` is inside the AlphaFold source checkout or build context | Move databases outside the repository; re-plan with `plan_docker_command.py`; do not build until the data path is outside the checkout. |
| `Cannot connect to the Docker daemon` | Docker service not running or current user lacks permission | Ask the user to start Docker or adjust group/rootless setup; do not retry privileged commands automatically. |
| GPU smoke check does not list GPUs | NVIDIA driver/toolkit/container runtime is missing or misconfigured | Ask the user to verify NVIDIA Container Toolkit and host drivers; CPU-only planning may still be possible with `--use_gpu=false`, but full inference will be slow or unsupported for many workloads. |
| `aria2c could not be found` | Download prerequisite missing | Tell the user to install `aria2`/`aria2c`; the planner can still show required actions. |
| `rsync could not be found` | PDB mmCIF prerequisite missing | Tell the user to install `rsync`; PDB mmCIF refresh cannot use the official workflow without it. |
| Reduced-dbs command cannot find BFD path | `--db_preset` mismatches downloaded data | Use `--db_preset=reduced_dbs` only with `small_bfd/`; use `--db_preset=full_dbs` with `bfd/` and `uniref30/`. |
| Full-dbs command cannot find `small_bfd` | Same preset/data mismatch in the opposite direction | Re-plan using the selected mode; do not mix BFD layouts across presets. |
| Multimer command misses UniProt or PDB SeqRes | Multimer requires extra databases | Download/verify `uniprot/uniprot.fasta` and `pdb_seqres/pdb_seqres.txt`, then re-plan. |
| Template or multimer search fails after update | PDB mmCIF and PDB SeqRes are from different dates | Refresh PDB mmCIF and PDB SeqRes together, with PDB mmCIF before PDB SeqRes. |
| Opaque MSA/template tool errors | Database permissions or missing files | Check that database directories and files are readable/executable as needed by the container/user; documented broad read/write guidance is `chmod 755 --recursive` under user supervision. |
| Model parameter load errors after code update | `params/` is stale or from deprecated weights | Refresh `params/` with the current parameter archive unless deliberately using deprecated multimer weights. |
| Relaxation crashes or is unstable on GPU | GPU OpenMM relaxation can be less stable | Plan `--enable_gpu_relax=false` or `--models_to_relax=none` if appropriate; route relaxation internals to `relaxation`. |
| User asks the agent to run all downloads | Downloads are network-heavy and huge | Refuse automatic execution; provide `plan_data_downloads.py` output and supervised command sequence. |

## Path and Permission Checks

- Prefer absolute paths for `--output_dir` and `--data_dir` when constructing Docker instructions.
- Keep `data_dir` outside the AlphaFold repository and outside any Docker build context.
- Ensure `output_dir` exists and is writable before a user-supervised Docker run.
- Ensure every FASTA basename is unique; duplicate basenames can collide in output directories.
- Ensure database paths exist for the chosen `model_preset` and `db_preset` before promising that a command is runnable.
- For shared/HPC storage, verify UID/GID and bind-mount permissions before recommending `docker_user` changes.

## GPU and Relaxation Notes

- The official Docker launcher defaults to `--use_gpu=true`, `--gpu_devices=all`, and `--enable_gpu_relax=true`.
- Effective GPU relaxation is `enable_gpu_relax AND use_gpu`; if GPU use is disabled, relaxation should be CPU or skipped.
- The launcher sets `NVIDIA_VISIBLE_DEVICES` to the requested GPU devices and uses NVIDIA GPU device requests when GPU is enabled.
- For stability-sensitive workflows, prefer `--enable_gpu_relax=false` while still allowing GPU inference, or `--models_to_relax=none` when relaxation is intentionally skipped.

## Update-Specific Pitfalls

- Update databases in a controlled order rather than mixing old and new directories.
- Refresh UniProt, UniRef30, UniRef90, and MGnify before refreshing PDB resources.
- Remove and refresh PDB mmCIF before PDB SeqRes so template data stays date-aligned.
- Refresh model parameters after database/code updates when moving to AlphaFold `2.3.2` expectations.
- Re-run the dry-run planners after any update to catch missing mode-specific paths.

## Safe Escalation Template

When handing off to a user for external execution, include:

1. Operation class: Docker build, Docker run, full download, reduced download, or incremental update.
2. Expected prerequisites: Docker, NVIDIA runtime, `aria2c`, `rsync`, disk, bandwidth, permissions.
3. Why the agent is not running it automatically.
4. The exact user-supervised command sequence.
5. A dry-run planner command the agent can run before or after the user operation.
