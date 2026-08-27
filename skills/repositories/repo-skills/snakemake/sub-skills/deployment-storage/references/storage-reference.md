# Storage Reference

Snakemake 9.23.1 uses storage provider plugins to map workflow input and output paths to local or remote backends. This reference covers default storage, explicit storage calls, local-copy behavior, access patterns, shared filesystem settings, and executor interactions.

## Install and activate provider plugins

Storage providers are external plugins. Install the provider package in the environment where Snakemake runs, and include it in workflow global dependencies if the Snakefile imports or registers it while parsing.

Examples:

```bash
pip install snakemake-storage-plugin-s3
mamba install -c conda-forge -c bioconda snakemake-storage-plugin-s3
```

If the workflow needs a plugin during parsing, add it to a global environment and run with Conda deployment:

```python
conda:
    "envs/global.yaml"
```

```yaml
channels:
  - conda-forge
  - bioconda
  - nodefaults
dependencies:
  - snakemake-storage-plugin-s3
```

```bash
snakemake --cores 8 --sdm conda
```

## Default storage provider

Use `--default-storage-provider` to map ordinary paths to a provider unless they are explicitly local or already mapped to another provider.

```bash
snakemake --cores 8 \
  --default-storage-provider s3 \
  --default-storage-prefix s3://mybucket/project/
```

Provider-specific settings become provider-specific CLI flags, for example:

```bash
snakemake --cores 8 \
  --default-storage-provider s3 \
  --default-storage-prefix s3://mybucket/project/ \
  --storage-s3-max-requests-per-second 10
```

Source paths are not mapped to default storage. Local files can be protected from default mapping with `local(...)`:

```python
rule example:
    input:
        local("resources/example-input.txt")
    output:
        "example-output.txt"
    shell:
        "tool {input} > {output}"
```

## Workflow-registered storage

Register a provider for selected files:

```python
storage:
    provider="s3",
    max_requests_per_second=10

rule selected_remote_input:
    input:
        storage.s3("s3://mybucket/input.txt")
    output:
        "results/output.txt"
    shell:
        "tool {input} > {output}"
```

Register tagged instances of the same provider when different endpoints, credentials, or settings are needed:

```python
storage:
    provider="s3",
    max_requests_per_second=10

storage awss3:
    provider="s3",
    endpoint_url="s3.us-east-2.amazonaws.com"

rule tagged_remote_input:
    input:
        storage.awss3("s3://mybucket/input.txt")
    output:
        "results/output.txt"
    shell:
        "tool {input} > {output}"
```

Let Snakemake infer a provider only when the installed plugins make the query unambiguous:

```python
rule inferred:
    input:
        storage("s3://mybucket/input.txt", retries=10)
    output:
        "results/output.txt"
    shell:
        "tool {input} > {output}"
```

Expected failure signals from provider inference:

- `No storage provider found for query ...`: install the required plugin or use an explicit provider.
- `Multiple suitable storage providers found for query ...`: specify the provider/tag explicitly.
- `Error applying storage provider ...`: the query does not satisfy that provider's query rules or required settings.

## Credentials and provider settings

Credentials are provider-specific. Many providers support environment variables; for S3-style plugins, patterns include:

```bash
export SNAKEMAKE_STORAGE_S3_ACCESS_KEY=...
export SNAKEMAKE_STORAGE_S3_SECRET_KEY=...
```

Avoid embedding secrets in Snakefiles, config files committed to version control, archives, or profiles that will be shared. When diagnosing credentials, verify that the variable names match the provider package version and that the executor's remote job environment receives them.

## Local staging behavior

Remote files are usually staged locally before jobs access them. Control this globally:

```bash
snakemake --cores 8 --keep-storage-local-copies
snakemake --cores 8 --not-retrieve-storage
snakemake --cores 8 --keep-storage-local-copies --not-retrieve-storage
```

Equivalent settings can be attached to provider registration or a single storage call:

```python
storage:
    provider="http",
    retrieve=False

storage http_local:
    provider="http",
    keep_local=True

rule remote_no_retrieve:
    input:
        storage.http("https://example.org/file.txt", retrieve=False)
    output:
        "results/from-remote.txt"
    shell:
        "tool {input} > {output}"

rule remote_keep_local:
    input:
        storage.http_local("https://example.org/file.txt", keep_local=True)
    output:
        "results/from-local-copy.txt"
    shell:
        "tool {input} > {output}"
```

Storage-related settings reflected in Snakemake's `StorageSettings` include:

- `default_storage_provider`: provider selected by `--default-storage-provider`.
- `default_storage_prefix`: prefix prepended for default storage mapping.
- `keep_storage_local`: enabled by `--keep-storage-local-copies`.
- `retrieve_storage`: disabled by `--not-retrieve-storage`.
- `local_storage_prefix`: local staging path, default `.snakemake/storage`.
- `remote_job_local_storage_prefix`: remote-job staging path; defaults to the local storage prefix when not set.
- `shared_fs_usage`: set of filesystem surfaces assumed shared between controller and jobs.
- `wait_for_free_local_storage`: optional wait behavior when local staging space is constrained.

## Access pattern annotations

Access flags let storage providers optimize whether a remote file can be streamed, mounted, symlinked, or must be downloaded. Provider support varies; absence of optimization is not a Snakemake bug.

Set a default input access pattern:

```python
inputflags:
    access.sequential
```

Override specific files:

```python
rule access_patterns:
    input:
        random=access.random("remote/index.bin"),
        multi=access.multi("remote/shared.txt"),
        sequential="remote/reads.fastq"
    output:
        "results/summary.txt"
    shell:
        "tool --index {input.random} --shared {input.multi} {input.sequential} > {output}"
```

Interpretation:

- `access.sequential`: read from start to end; may be eligible for on-demand access if a single job uses it sequentially.
- `access.random`: non-sequential access; expect local staging.
- `access.multi`: multiple reads or parallel reads; expect local staging.
- No annotation: expect local staging.

## Shared filesystem planning

Executor plugins may need explicit storage and shared filesystem settings. The key question is which surfaces are visible both to the Snakemake controller and to worker jobs.

Important surfaces:

- `persistence`: metadata below `.snakemake` that tracks job and file state.
- `software-deployment`: Conda environments and container image prefixes.
- `sources`: Snakefiles, scripts, notebooks, config files, wrappers, and imported modules.
- `source-cache`: cached source files from `workflow.source_path(...)` and remote source references.
- `input-output`: ordinary workflow input/output files.
- `storage-local-copies`: local copies staged from storage providers.

A conservative non-shared plan often combines a storage provider with explicit source/cache handling:

```bash
snakemake --executor slurm --cores 32 \
  --default-storage-provider fs \
  --shared-fs-usage persistence software-deployment sources source-cache \
  --local-storage-prefix .snakemake/storage \
  --remote-job-local-storage-prefix .snakemake/remote-storage \
  --dry-run --printshellcmds
```

This is a planning shape, not a universal command. Executor plugins can require additional flags and resources.

## Remote jobs and spawned commands

For remote execution, Snakemake's spawned job command propagates storage flags such as:

- `--default-storage-prefix`
- `--default-storage-provider`
- `--shared-fs-usage`
- `--local-storage-prefix`
- `--keep-storage-local-copies`
- `--not-retrieve-storage` when retrieval is disabled
- deployment-related settings such as `--apptainer-prefix`, `--apptainer-args`, and `--cache`

If remote jobs behave differently from local dry-runs, compare the controller command, spawned job command, executor profile, and jobscript properties. Use `scripts/inspect_job_properties.py` from this sub-skill to inspect jobscript metadata.

## Storage and archives

Archives include input files required by the DAG and Conda packages, but not live external credentials. For workflows using storage providers:

- Ensure remote inputs required for archive creation are retrievable from the controller environment.
- Ensure storage plugin packages are included as global dependencies if the archived workflow needs them while parsing or running.
- Do not archive credential files accidentally.
- After unpacking, test with `snakemake --cores 1 --dry-run --printshellcmds` before claiming the archive is reproducible.

## Quick diagnosis matrix

| Symptom | Likely cause | Next check |
| --- | --- | --- |
| `No storage provider found for query` | Plugin missing or query not recognized | Install provider package; use explicit `storage.<provider>(...)` |
| `Multiple suitable storage providers found` | Ambiguous auto inference | Register/tag provider and call it explicitly |
| Remote job cannot see input | Shared FS assumptions wrong | Review `--shared-fs-usage`, storage prefix, and remote-job local storage prefix |
| Works locally but fails on executor | Credentials or plugin missing in worker job | Propagate env vars; include plugin in global env/profile |
| Excessive downloads | Access pattern not annotated or provider cannot stream | Add `access.sequential`; check provider capabilities |
| Disk fills under `.snakemake/storage` | Local staging retained or many remote files | Adjust `--local-storage-prefix`, cleanup policy, and `--keep-storage-local-copies` |
