# Container And HPC Reference

## Purpose

Use this reference to run pySCENIC CLI workflows in Docker, Podman, Singularity, Apptainer, or cluster environments without losing track of resource files, mounted paths, workers, and Dask filesystem constraints.

## Image Choices

- `aertslab/pyscenic:<version>`: CLI-oriented image with pySCENIC dependencies. Prefer this for `grn`, `ctx`, `aucell`, and non-interactive pipelines.
- `aertslab/pyscenic_scanpy:<version>`: larger image with scanpy, IPython kernel support, and downstream notebook-oriented dependencies. Use it only when the task needs scanpy/notebook extras, AnnData/h5ad checks confirm the needed packages, or interactive analysis.
- Locally built images from the repository Dockerfiles follow the same split: base CLI image versus scanpy-enabled image. A future agent should not assume build context or network access is available during normal skill use.

Keep image tags explicit when reproducibility matters. If the local installed package reports an untagged development version, record that separately in the run notes but do not copy local environment paths into commands.

## Mount Planning

Containers must see all expression, TF list, ranking database, motif annotation, output, and args-file paths under mounted directories. A single project mount is the simplest plan:

```bash
HOST_PROJECT="/host/path/project"
RUNTIME_PROJECT="/data"
IMAGE="aertslab/pyscenic:0.12.1"
```

Inside command templates, use `$RUNTIME_PROJECT/...` paths only. Do not mix host paths and container paths in one command.

Before full execution, check inside the container:

```bash
docker run --rm \
  -v "$HOST_PROJECT":"$RUNTIME_PROJECT" \
  "$IMAGE" \
  sh -lc 'pyscenic --help >/dev/null && test -r /data/expression_cells_by_genes.csv && test -d /data/databases'
```

For Podman, use the same command shape with `podman run`. On SELinux-enabled hosts, a volume suffix such as `:Z` or `:z` may be needed depending on local policy.

## Docker Or Podman Pipeline

```bash
docker run --rm \
  -v "$HOST_PROJECT":"$RUNTIME_PROJECT" \
  "$IMAGE" \
  pyscenic grn \
    --method grnboost2 \
    --num_workers 8 \
    --seed 777 \
    -o /data/out/adjacencies.tsv \
    /data/expression_cells_by_genes.csv \
    /data/tfs.txt

docker run --rm \
  -v "$HOST_PROJECT":"$RUNTIME_PROJECT" \
  "$IMAGE" \
  pyscenic ctx \
    /data/out/adjacencies.tsv \
    /data/databases/db1.genes_vs_motifs.rankings.feather \
    /data/databases/db2.genes_vs_motifs.rankings.feather \
    --annotations_fname /data/motif_annotations.tbl \
    --expression_mtx_fname /data/expression_cells_by_genes.csv \
    --mode custom_multiprocessing \
    --num_workers 8 \
    --output /data/out/regulons.csv

docker run --rm \
  -v "$HOST_PROJECT":"$RUNTIME_PROJECT" \
  "$IMAGE" \
  pyscenic aucell \
    /data/expression_cells_by_genes.csv \
    /data/out/regulons.csv \
    --num_workers 8 \
    --seed 777 \
    -o /data/out/auc_mtx.csv
```

Use `-u "$(id -u):$(id -g)"` when container-created files should be owned by the host user and the image supports that user mapping.

## Singularity Or Apptainer Pipeline

Build or obtain a `.sif` image outside the normal pySCENIC run plan. Use `exec` or `run` with explicit binds:

```bash
SIF="/host/path/aertslab-pyscenic.sif"
HOST_PROJECT="/host/path/project"
RUNTIME_PROJECT="/data"

singularity exec \
  -B "$HOST_PROJECT":"$RUNTIME_PROJECT" \
  "$SIF" \
  pyscenic grn \
    --method grnboost2 \
    --num_workers 8 \
    --seed 777 \
    -o /data/out/adjacencies.tsv \
    /data/expression_cells_by_genes.csv \
    /data/tfs.txt
```

For Apptainer, replace `singularity` with `apptainer`. If the site auto-binds home or scratch directories, still write commands with explicit `-B` entries for every data/database/output root so the plan remains portable.

## Args Files In Containers

Generate args files with runtime paths, then run them from the mounted directory:

```bash
python scripts/pyscenic_cli_smoke.py \
  --write-args-dir "$HOST_PROJECT/args" \
  --workdir /data \
  --workers 8

docker run --rm \
  -v "$HOST_PROJECT":"$RUNTIME_PROJECT" \
  "$IMAGE" \
  pyscenic @/data/args/ctx.args.txt
```

The args files must contain `/data/...` paths in this example, not `/host/path/project/...` paths.

## Local Versus Container Versus HPC Decisions

Choose local installed CLI when:

- The package imports and CLI help already work.
- All data and databases are on fast local storage.
- A single machine has enough CPU and memory for the selected worker counts.

Choose containers when:

- Dependency isolation matters more than direct Python API access.
- The host has Docker/Podman or Singularity/Apptainer already installed.
- All required resources can be mounted with stable runtime paths.

Choose HPC or scheduler execution when:

- Ranking databases and expression data exceed single-workstation memory or walltime.
- The scheduler grants enough CPU, memory, and shared filesystem access.
- Every worker can read the same database and input paths and write outputs or temporary files to approved locations.

Avoid cluster mode when workers cannot access the same paths as the scheduler/client. For pySCENIC `ctx --mode dask_cluster`, `--client_or_address` must point to an existing scheduler and database paths must be valid from every worker.

## Dask And Filesystem Constraints

- `grn` can use a local or remote Dask client through `--client_or_address`; the Dask-free `arboreto_with_multiprocessing.py` fallback is single-host only.
- `ctx` supports `custom_multiprocessing`, `dask_multiprocessing`, and `dask_cluster`; current local default is `custom_multiprocessing`.
- Dask cluster workers need access to the same ranking database, motif annotation, module/adjacency, and expression paths. Network filesystems must be mounted consistently.
- For `ctx`, large Feather databases are opened by workers; plan memory and I/O accordingly.
- On shared systems, prefer scheduler-provided scratch/output paths and avoid writing to container layers or read-only image filesystems.

## Reference-Only Source Scripts

The repository contained example HPC GRNBoost and prune scripts plus `.ini` files. They are not bundled as runnable skill scripts because they encode site-specific scheduler paths, private storage layouts, and older dependency assumptions. Their useful patterns are distilled here:

- Put data, database, and output roots in one configuration block or args file.
- Skip already-completed outputs only when rerun semantics are clear.
- Use Dask cluster addresses only when the scheduler is externally managed and shared paths are confirmed.
- Log command, worker count, mode, resource paths, and output names for every submitted job.

Release and deployment scripts are intentionally excluded from this runtime skill because they perform packaging or publication side effects rather than safe pySCENIC analysis orchestration.

## Container Preflight Checklist

1. Run `pyscenic --help` inside the image.
2. Run help for `grn`, `ctx`, `aucell`, and `arboreto_with_multiprocessing.py` inside the same image when relevant.
3. Verify `test -r` for expression, TF list, annotations, and each database path inside the runtime mount namespace.
4. Verify `test -w` for the output directory inside the runtime mount namespace.
5. Confirm host and runtime path mapping is one-to-one and no command contains unmounted host paths.
6. Confirm whether the scanpy image is actually needed for notebooks, scanpy-dependent analysis, or missing AnnData/h5ad dependencies; otherwise prefer the CLI image.
