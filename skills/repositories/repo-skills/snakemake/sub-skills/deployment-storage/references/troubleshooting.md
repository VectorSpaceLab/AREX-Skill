# Deployment and Storage Troubleshooting

Use this checklist when Snakemake 9.23.1 deployment, storage, cache, archive, or executor jobscript behavior differs from expectations.

## First triage commands

Run safe planning commands before executing external tools or jobs:

```bash
snakemake --cores 1 --dry-run --printshellcmds
snakemake --cores 1 --dry-run --printshellcmds --sdm conda
snakemake --cores 1 --dry-run --printshellcmds --sdm conda apptainer --apptainer-args '--cleanenv'
snakemake --cores 1 --dry-run --printshellcmds --default-storage-provider s3 --default-storage-prefix s3://bucket/prefix/
```

Remember: `--reason` is not a Snakemake 9.23.1 flag. Reasons can appear in dry-run output without requesting that option.

## Conda issues

### Conda command not found

Signals:

- Failure before job execution while creating environments.
- Messages about `conda`, `mamba`, activation, or base path discovery.

Checks:

```bash
conda --version
snakemake --cores 1 --dry-run --printshellcmds --sdm conda
snakemake --cores 1 --sdm conda --conda-create-envs-only
```

Recovery:

- Install Conda in the runtime environment or provide `--conda-base-path` to the intended base installation.
- Use `--conda-prefix DIR` to keep environments on storage visible to worker jobs.
- If workers do not share software deployment storage, adjust `--shared-fs-usage` and ensure each job can create or receive environments.

### Conda frontend confusion

Snakemake 9.23.1 normalizes alternative frontend settings back to `conda` and warns that alternative frontends are deprecated. Current Conda releases use libmamba solving internally, so do not rely on `--conda-frontend mamba` behavior for new plans.

### Environment changed but jobs still use old packages

Checks:

```bash
snakemake --list-conda-envs --sdm conda
snakemake --cores 1 --dry-run --printshellcmds --sdm conda
```

Recovery:

- Confirm the rule points to the intended `.yaml` / `.yml` file.
- Confirm platform pin files such as `envs/tool.linux-64.pin.txt` were updated together with the YAML.
- Run `snakemake --conda-cleanup-envs --sdm conda` to remove unused environments.
- Use `--conda-cleanup-pkgs tarballs` or `--conda-cleanup-pkgs cache` to reduce package cache side effects after creation.

### Post-deploy script succeeds but package is missing

Likely causes:

- Script ran under `sh` but required Bash features.
- User-level package paths such as `R_LIBS_USER`, `R_LIBS`, or `PYTHONPATH` redirected installation outside the environment.
- Tool emitted warnings but returned success.

Recovery:

- Add a shebang such as `#!env bash` and `set -o pipefail`.
- Use `$CONDA_PREFIX` explicitly.
- For R package installs, consider `Rscript --no-environ` and fail-on-warning settings for the installer.
- Avoid `--conda-not-block-search-path-envvars` unless the workflow intentionally depends on inherited paths.

## Apptainer/Singularity issues

### Engine unavailable or too old

Expected signal from Snakemake code:

- `The apptainer or singularity command has to be available in order to use apptainer/singularity integration.`
- `Minimum apptainer version is 1.0.0.`
- `Minimum singularity version is 2.4.1.`

Checks:

```bash
apptainer --version || singularity --version
snakemake --cores 1 --dry-run --printshellcmds --sdm apptainer
```

Recovery:

- Install Apptainer/Singularity on the controller and worker nodes.
- Ensure the executor environment sees the same binary as the login shell.
- Use `--apptainer-prefix DIR` on shared or intentionally staged storage for image reuse.

### Container sees unexpected host libraries or paths

Cause: Apptainer/Singularity can pass host environment variables through by default.

Recovery:

```bash
snakemake --cores 8 --sdm apptainer --apptainer-args '--cleanenv'
snakemake --cores 8 --sdm conda apptainer --apptainer-args '--cleanenv'
```

If a workflow needs explicit bind mounts, add them through `--apptainer-args`, but keep the command portable and profile-managed.

### Conda inside container fails

Checks:

- The container image must contain enough OS tooling for Conda environment creation.
- If using `--containerize`, build and push the generated image before using `containerized:`.
- Environment hashes include container image identity; image changes can trigger new Conda environments.

## Environment module issues

Signals:

- Jobs fail only with `--use-envmodules`.
- Module names exist on the login node but not on compute nodes.
- Portable users cannot reproduce the workflow.

Recovery:

- Treat `envmodules:` as site-specific acceleration, not the only reproducibility mechanism.
- Keep equivalent `conda:` or `container:` declarations for fallback.
- Verify module order matches the rule's command requirements.
- Test fallback separately:

```bash
snakemake --cores 1 --dry-run --printshellcmds --sdm conda
```

## Storage plugin and credential issues

### Provider not found

Signal:

- `No storage provider found for query ... Either install the required storage plugin or check your query.`

Recovery:

- Install the provider package in the Snakemake runtime environment.
- If the Snakefile registers the provider during parsing, include the plugin in a global `conda:` environment and run with `--sdm conda`.
- Replace ambiguous `storage("...")` calls with explicit `storage.<provider>("...")` calls.

### Multiple providers match

Signal:

- `Multiple suitable storage providers found for query ... Explicitly specify the storage provider.`

Recovery:

```python
storage:
    provider="s3"

rule explicit:
    input: storage.s3("s3://bucket/object.txt")
    output: "results/object.txt"
    shell: "cp {input} {output}"
```

### Credentials work locally but not on workers

Checks:

- Are credential environment variables exported in the executor submit environment?
- Does a profile sanitize environment variables?
- Does a container run with `--cleanenv` and omit required variables?
- Are credentials accidentally available only through an interactive shell startup file?

Recovery:

- Configure credentials through the provider's documented environment variables or secret mechanism.
- Pass required variables through executor/profile mechanisms rather than embedding them in Snakefiles.
- For containers, explicitly propagate safe variables or mount credential files only when policy allows.

## Shared filesystem and staging issues

Symptoms:

- Controller dry-run succeeds, submitted jobs cannot find Snakefiles/scripts/configs.
- Jobs recreate Conda environments or pull images repeatedly.
- Storage-local copies are missing on workers.
- `.snakemake/storage` fills local disks.

Checks:

```bash
snakemake --cores 1 --dry-run --printshellcmds \
  --default-storage-provider fs \
  --shared-fs-usage persistence software-deployment sources source-cache
```

Recovery:

- Decide which surfaces are truly shared: persistence, software deployment, sources, source cache, input/output, and storage-local-copies.
- Use `--local-storage-prefix` for controller-side staging and `--remote-job-local-storage-prefix` for worker-side staging when they differ.
- Keep software deployment prefixes on shared storage when workers should reuse environments/images.
- Disable source deployment only when every worker already sees the required sources.

## Output cache issues

### Cache path missing

Signal: errors mentioning `SNAKEMAKE_OUTPUT_CACHE` or unavailable cache backend.

Recovery:

```bash
export SNAKEMAKE_OUTPUT_CACHE=/shared/snakemake-output-cache
snakemake --cores 8 --cache
```

Ensure the cache path is readable and writable by intended users. Do not use this shared cache for private data.

### Rule not cacheable

Likely causes:

- Rule has no output.
- Multiple outputs are not named and do not use `multiext(...)`.
- Shell/script uses values not captured in `params`, making provenance unsafe.
- Rule is omitted from `--cache` and lacks `cache:` directive.

Recovery:

```python
rule index:
    input: "reference.fa"
    output:
        idx=multiext("reference", ".amb", ".ann", ".bwt", ".pac", ".sa")
    params:
        algorithm="bwtsw"
    cache: True
    shell:
        "bwa index -a {params.algorithm} {input}"
```

Use `cache: "omit-software"` only when software identity is irrelevant to the result.

## Archive issues

### Archive misses files

Likely causes:

- Required scripts/configs are not under version control and not declared as inputs/source files.
- Remote files cannot be retrieved during archive creation.
- Global dependencies or storage plugins are not represented in Conda environments.

Recovery:

- Declare scripts, notebooks, schemas, and configs through Snakemake mechanisms so they enter the DAG/source cache.
- Track workflow support files in version control before archiving.
- Add plugin packages and parsing-time dependencies to a global `conda:` environment.
- Verify the archive after unpacking:

```bash
tar -xf workflow.tar.gz
snakemake --cores 1 --dry-run --printshellcmds
```

### Archive is not portable across platforms

Expected behavior: Conda package archives are platform-specific. Recreate the archive on a compatible platform for the intended users.

## Jobscript and job properties issues

Custom jobscripts should preserve a properties header if submit wrappers inspect rule metadata:

```sh
#!/bin/sh
# properties = {properties}
{exec_job}
```

Inspect a generated jobscript:

```bash
python scripts/inspect_job_properties.py path/to/jobscript.sh --summary
python scripts/inspect_job_properties.py path/to/jobscript.sh --key resources
```

If parsing fails:

- Confirm the line begins with `# properties =`.
- Confirm the payload is JSON-like or Python-literal-like mapping data generated by Snakemake.
- Confirm custom templating did not quote, truncate, or wrap the properties line.
- Confirm the executor submit command receives the generated jobscript, not the template.

## Safe hard-case planning patterns

### HPC conda + Apptainer + non-shared cache plan

Use a dry-run-only command to reason about surfaces without running external tools:

```bash
snakemake --executor slurm --cores 32 \
  --sdm conda apptainer \
  --apptainer-args '--cleanenv' \
  --default-storage-provider fs \
  --shared-fs-usage persistence software-deployment sources source-cache \
  --local-storage-prefix .snakemake/storage \
  --remote-job-local-storage-prefix .snakemake/remote-storage \
  --dry-run --printshellcmds
```

Expected review output should identify which paths must be shared, which are staged, and which executor/plugin settings are still missing.

### Missing storage plugin or credential while preserving cache

Debug without deleting caches:

```bash
snakemake --cores 1 --dry-run --printshellcmds \
  --default-storage-provider s3 \
  --default-storage-prefix s3://bucket/project/ \
  --keep-storage-local-copies
```

Expected review output should distinguish plugin import/registration errors from credential errors, avoid embedding secrets, and avoid clearing `.snakemake/storage` or `SNAKEMAKE_OUTPUT_CACHE` until the cause is known.
