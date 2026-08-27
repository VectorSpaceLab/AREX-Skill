# Runtime Troubleshooting

Start with the safe preflight checker:

```bash
python scripts/check_runtime_requirements.py \
  --model_dir model_parameters \
  --db_dir public_databases
```

It does not download data, run inference, format disks, or modify installed resources.

## Help Prints Flags but Exits Non-Zero

Symptom:

- `python run_alphafold.py --help` renders flags but exits with status `1`.

Likely cause:

- `run_alphafold.py` marks `--output_dir` as required through Abseil. Help text can still be useful even when process status is non-zero.

Fix:

- Treat the rendered help as valid reference.
- For script-based smoke checks, accept exit code `1` if help text was printed and no actual run was attempted.

## Missing Model Parameters

Symptoms:

- Failure while checking or loading model parameters.
- Errors around model parameter files in `--model_dir`.

Likely causes:

- Model parameters were not obtained or unpacked.
- `--model_dir` points to the parent of the real parameter directory, a read-protected directory, or an empty mount.
- Docker command forgot to mount model parameters into the container.

Fixes:

- Confirm the user obtained AlphaFold 3 model parameters directly under the applicable terms.
- Pass `--model_dir` explicitly and ensure it is readable inside the runtime environment.
- In Docker, verify the host path and container path match the `--volume` and `--model_dir` values.
- Do not replace missing official parameters with random parameters for scientific prediction; random parameters are only for performance plumbing experiments.

## Missing or Incomplete Databases

Symptoms:

- `FileNotFoundError` for `${DB_DIR}/...` paths.
- Template search cannot find `mmcif_files` or `pdb_seqres_2022_09_28.fasta`.
- Protein/RNA MSA search fails before meaningful model inference.

Likely causes:

- `--db_dir` points to the wrong directory.
- Full database download/decompression did not finish.
- Database files have different names than the defaults.
- Database directory is not readable from inside Docker.

Fixes:

- Check the expected database entries listed in `setup-and-performance.md`.
- Use repeated `--db_dir` values when databases are spread across roots and default names are preserved.
- Use explicit `--*_database_path` flags when names or locations differ.
- Ensure database directory permissions allow read and execute access for the runtime user.
- Keep databases outside source checkouts and image build contexts.

## Database Permission and Disk Issues

Symptoms:

- Opaque external-tool errors from MSA tools.
- Writes fail during download/decompression or output creation.
- Very slow data pipeline despite many CPUs.

Likely causes:

- Database files are not readable by the user/container.
- Output directory is not writable.
- Databases are on slow disks or network storage.
- Full databases exceed available disk space; unpacked size is much larger than compressed size.

Fixes:

- Check read/execute permissions on database directories and write permissions on output directories.
- Prefer SSD-backed database storage for genetic search.
- Ask before changing permissions recursively on shared systems.
- Ask before running any large database download, copy-to-SSD, disk format, or mount operation.

## Missing HMMER Binaries

Symptoms:

- `jackhmmer`, `nhmmer`, `hmmalign`, `hmmsearch`, or `hmmbuild` path is `None` or not executable.
- Data pipeline fails immediately when starting MSA/template search.
- A workflow specifically fails with missing `hmmbuild` while other HMMER tools exist.

Likely causes:

- HMMER suite is not installed in the local environment.
- Minimal Docker image lacks one binary.
- `PATH` differs between shell, batch scheduler, and container runtime.

Fixes:

- Run `scripts/check_runtime_requirements.py --check_hmmer`.
- Install a complete HMMER suite in the runtime environment.
- Pass explicit `--jackhmmer_binary_path`, `--nhmmer_binary_path`, `--hmmalign_binary_path`, `--hmmsearch_binary_path`, and `--hmmbuild_binary_path` values when `PATH` discovery is unreliable.
- For data-pipeline-only CPU jobs, HMMER is still required; for inference-only jobs with precomputed MSA/template data, HMMER is not used.

## Generated CCD Resources Missing

Symptoms:

- Import succeeds, but ligand/CCD-related code fails looking for `ccd.pickle` or `chemical_component_sets.pickle`.
- Failures occur around chemical components, custom ligands, glycans, or mmCIF conversion.

Likely causes:

- The installed package needs a post-install data build step to generate CCD pickle resources.
- The install environment lacks `components.cif` from `libcifpp` data.

Fixes:

- Run the safe checker to confirm whether generated CCD pickle resources are present.
- If missing, run the package-provided data build command in the target environment only after confirming it is appropriate for that install.
- Re-run the checker after building resources.

## CUDA, JAX, and GPU Visibility

Symptoms:

- `jax.local_devices(backend='gpu')` is empty.
- Inference fails before model execution.
- Docker cannot see `nvidia-smi` or GPUs.
- Wrong GPU is used on a multi-GPU host.

Likely causes:

- Host NVIDIA driver or container toolkit is missing/misconfigured.
- CUDA/JAX versions are incompatible with the environment.
- Docker run omitted `--gpus all` or equivalent device selection.
- `CUDA_VISIBLE_DEVICES` changes visible device numbering.

Fixes:

- Confirm host `nvidia-smi` works before running containers.
- Confirm the container can run `nvidia-smi` with GPU access.
- Confirm JAX can list GPU devices in the same environment that will run AlphaFold 3.
- Use `--gpu_device` after accounting for any `CUDA_VISIBLE_DEVICES` filtering.
- For local installs, align CUDA, cuDNN, driver, and JAX GPU package versions.

## V100 or CUDA Capability 7.x Failures

Symptoms:

- Error says CUDA compute capability 7.x requires `XLA_FLAGS`.
- Outputs have severe clashes or very low ranking scores on V100-class GPUs.
- Error says `--flash_attention_implementation` must be `xla`.

Fixes:

- Set `XLA_FLAGS` to include `--xla_disable_hlo_passes=custom-kernel-fusion-rewriter`.
- Run with `--flash_attention_implementation=xla`.
- Expect smaller feasible token sizes and lower throughput than A100/H100 configurations.

## Out-of-Memory or Excessive Compilation

Symptoms:

- GPU OOM during inference.
- First run of each input size spends a long time compiling.
- Inputs slightly above `5120` tokens trigger repeated recompilations.

Fixes:

- Use larger GPUs or smaller inputs when possible.
- Add larger `--buckets` values to group similar large token sizes.
- Enable `--jax_compilation_cache_dir` for repeated runs.
- Consider unified memory for larger inputs or smaller-memory GPUs, accepting slower runtime.
- Avoid `--save_embeddings` and `--save_distogram` unless required, because they add large outputs.

## Split Workflow Mistakes

Symptoms:

- Inference-only run fails with missing MSA/template fields.
- Second stage refuses to use an existing output directory.
- Inference-only stage still tries to run database search.

Likely causes and fixes:

- Use the enriched `_data.json` emitted by the data-pipeline stage, not the original minimal JSON.
- Add `--run_data_pipeline=false` for inference-only.
- Add `--force_output_dir=true` when reusing the same job output directory.
- Keep `--model_dir` for inference-only; omit or ignore `--db_dir` only when the data pipeline is disabled.

## Sharded Database Z-Value Diagnostics

Symptoms:

- Sharded path uses `@N` but a matching Z-value flag is missing.
- MSA sensitivity or E-value behavior looks inconsistent after sharding.
- Search does not use expected CPU parallelism.

Fixes:

- For every sharded protein database, pass the integer total sequence count as the matching `--*_z_value`.
- For every sharded RNA database, pass the total megabase count as the matching `--*_z_value`.
- Confirm shard filenames are zero-padded and follow `prefix-00000-of-00016` style.
- Tune `--jackhmmer_max_parallel_shards` and `--nhmmer_max_parallel_shards` against actual CPU count and storage bandwidth.

## Output Directory and Existing Results

Symptoms:

- Run fails because output directory exists or contains files.
- Data-pipeline-only stage wrote JSON but inference results are absent.

Fixes:

- Use a clean `--output_dir` for independent full runs.
- Use `--force_output_dir=true` when intentionally adding inference outputs to a data-pipeline job directory.
- Route questions about output files and ranking/confidence metrics to `../output-interpretation/`.
