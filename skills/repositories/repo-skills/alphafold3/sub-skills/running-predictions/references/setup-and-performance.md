# Setup and Performance Guidance

AlphaFold 3 runtime planning is mostly about separating four resources: input JSONs, model parameters, genetic/template databases, and GPU inference capacity. Keep commands explicit about all four so future agents can move work between Docker, local Python, CPU-only hosts, and GPU hosts.

## Runtime Prerequisites

- Linux is the supported operating system family.
- Full inference needs model parameters obtained externally under the AlphaFold 3 model-parameter terms; they are not bundled with the Python package or source code.
- Full data-pipeline runs need public genetic/template databases; expect large downloads and unpacked storage, and prefer SSD-backed storage for search speed.
- Data-pipeline runs need HMMER binaries: `jackhmmer`, `nhmmer`, `hmmalign`, `hmmsearch`, and `hmmbuild`.
- Inference needs JAX with a working GPU backend and model parameters readable from `--model_dir`.
- Installed Python package resources may require generated CCD pickle data after installation; run the safe checker before diagnosing ligand/CCD failures.

## Docker Workflow

Build or use an AlphaFold 3 container that contains the package, `run_alphafold.py`, HMMER tools, CUDA/JAX dependencies, and default runtime environment variables. Mount user-controlled host directories into stable container paths:

```bash
docker run --rm -it \
  --volume "$AF_INPUT:/root/af_input:ro" \
  --volume "$AF_OUTPUT:/root/af_output" \
  --volume "$AF_MODEL_DIR:/root/models:ro" \
  --volume "$AF_DB_DIR:/root/public_databases:ro" \
  --gpus all \
  alphafold3 \
  python run_alphafold.py \
  --json_path=/root/af_input/fold_input.json \
  --model_dir=/root/models \
  --db_dir=/root/public_databases \
  --output_dir=/root/af_output
```

Guidelines:

- Mount input and model/database directories read-only unless the workflow intentionally writes there.
- Mount output read-write and ensure the container user can create subdirectories.
- Use `--gpus all` for simple single-GPU setups; on multi-GPU machines, pair container GPU filtering with `--gpu_device` if needed.
- Avoid placing full databases inside a source checkout or Docker build context; they can make image builds extremely slow and huge.

## Local Python Workflow

Local Python is useful for development or controlled HPC environments. Keep it explicit:

```bash
python run_alphafold.py \
  --json_path=fold_input.json \
  --output_dir=af_output \
  --model_dir=model_parameters \
  --db_dir=public_databases
```

Before a local run:

- Confirm `python -c "import alphafold3"` succeeds.
- Confirm generated CCD resources exist if the install process requires a post-install data build.
- Confirm HMMER binaries are on `PATH` or provide the `--*_binary_path` flags.
- Confirm JAX can see the intended GPU for inference-only or full runs.

## Split CPU/GPU Workflow

The data pipeline is CPU/RAM/disk intensive and does not require a GPU. Inference requires a GPU. Splitting can reduce GPU idle time.

CPU data-pipeline stage:

```bash
python run_alphafold.py \
  --json_path=fold_input.json \
  --output_dir=af_output \
  --db_dir=public_databases \
  --run_inference=false
```

This stage needs the genetic/template databases and HMMER tools, but not model parameters or a GPU because inference is disabled.

GPU inference stage, using the enriched JSON emitted by the data-pipeline stage:

```bash
python run_alphafold.py \
  --json_path=af_output/<job_name>/<job_name>_data.json \
  --output_dir=af_output \
  --model_dir=model_parameters \
  --run_data_pipeline=false \
  --force_output_dir=true
```

Notes:

- The exact enriched JSON filename is based on the sanitised job name from the input.
- Use the same parent `--output_dir` when you want outputs grouped consistently; add `--force_output_dir=true` if the job directory already exists.
- Inference-only input must contain MSA/template fields from a previous pipeline run, or those fields must be explicitly empty when intentionally running MSA/template-free.
- Model parameters and GPU/JAX readiness are required for the inference stage, not for CPU-only data-pipeline generation.
- This split also supports reusing fixed-chain MSA/template results across many assembled multimer inputs; route assembly details to `../input-preparation/`.

## Database Layout

A standard full database directory contains these entries:

- `bfd-first_non_consensus_sequences.fasta`
- `mgy_clusters_2022_05.fa`
- `uniprot_all_2021_04.fa`
- `uniref90_2022_05.fa`
- `nt_rna_2023_02_23_clust_seq_id_90_cov_80_rep_seq.fasta`
- `rfam_14_9_clust_seq_id_90_cov_80_rep_seq.fasta`
- `rnacentral_active_seq_id_90_cov_80_linclust.fasta`
- `pdb_seqres_2022_09_28.fasta`
- `mmcif_files/`

Use `--db_dir` when the default names exist under one or more database roots. Use explicit database path flags when names differ, data is split across storage devices, or sharded database specs are used.

Database downloads and SSD copy/mount scripts are intentionally not bundled here because they perform large network, disk, or system mutations. Future agents should ask for explicit user approval before downloading hundreds of GB, formatting/mounting disks, or copying full databases.

## Sharded Databases

Sharding can speed genetic search on many-core machines with very fast storage. Each shard filename must follow:

```text
prefix-00000-of-00016
prefix-00001-of-00016
...
prefix-00015-of-00016
```

Pass the sharded database as `prefix@16`. Set the matching Z-value flag from the total number of sequences for protein databases or total megabases for RNA databases. Without the Z-value, sharded searches can produce incorrect E-value scaling or fail validation.

Example shape:

```bash
python run_alphafold.py \
  --json_path=fold_input.json \
  --output_dir=af_output \
  --model_dir=model_parameters \
  --small_bfd_database_path=/fastdb/bfd-first_non_consensus_sequences.fasta@64 \
  --small_bfd_z_value=65984053 \
  --jackhmmer_n_cpu=2 \
  --jackhmmer_max_parallel_shards=16
```

Tune CPUs as:

- Protein search core pressure is roughly `jackhmmer_n_cpu × jackhmmer_max_parallel_shards × 4` for four protein databases searched in parallel.
- RNA search core pressure is roughly `nhmmer_n_cpu × nhmmer_max_parallel_shards × 3` for three RNA databases searched in parallel.
- Fast SSD or RAM-backed storage matters; sharding on slow storage can bottleneck on I/O.

## GPU and Attention Choices

- A100 80 GB and H100 80 GB are the best-supported high-throughput single-GPU configurations.
- A100 40 GB can require unified memory and model config tuning for larger inputs, with lower throughput.
- CUDA capability 7.x GPUs such as V100 need `XLA_FLAGS` including `--xla_disable_hlo_passes=custom-kernel-fusion-rewriter` and should use `--flash_attention_implementation=xla`.
- `triton` flash attention is the default and fastest on supported newer NVIDIA GPUs; `cudnn` is another newer-GPU option; `xla` is the portable fallback.
- Use `--gpu_device` to pin a run to a device, especially when launching one process per GPU.

## Compilation Buckets and Cache

AlphaFold 3 compiles model shapes by token-size buckets. Defaults cover token sizes up to `5120`. Inputs larger than the largest bucket create an exact-size bucket and trigger a separate compile.

- Add a larger `--buckets` value when several large inputs have similar sizes.
- Use `--jax_compilation_cache_dir` to persist JAX compilation artifacts across runs.
- Fewer buckets reduce compilations but increase padding; more buckets reduce padding but increase compilations.

## Output and Throughput Knobs

- `--num_recycles` defaults to `10`; reducing it speeds inference but can reduce quality.
- `--num_diffusion_samples` defaults to `5`; increasing it adds samples, runtime, and output size.
- `--num_seeds` expands a single input seed into multiple sequential seeds; useful for repeated inference from one JSON.
- `--save_embeddings` and `--save_distogram` produce large token-scaling arrays; enable only when downstream analysis needs them.
- `--compress_large_output_files=true` reduces large mmCIF/confidence JSON size at extra CPU cost.
