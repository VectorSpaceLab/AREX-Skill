# Deployment Reference

This reference covers Snakemake 9.23.1 software deployment surfaces: Conda, Apptainer/Singularity containers, environment modules, source deployment, archives, caches, and executor jobscripts.

## Command switches to know

- `--software-deployment-method conda`, shorthand `--sdm conda`: build and use rule-level `conda:` environments and wrapper environments.
- `--software-deployment-method apptainer`, shorthand `--sdm apptainer`: run jobs with `container:` / `containerized:` via Apptainer or Singularity.
- `--software-deployment-method conda apptainer`: combine containerized OS images with rule-level Conda environments.
- `--use-conda`, `--use-apptainer` / `--use-singularity`, `--use-envmodules`: convenience flags that imply the respective deployment method.
- `--conda-prefix DIR`: place Conda environments and archives below a chosen work/cache directory; pair with Conda deployment.
- `--conda-create-envs-only`: create required Conda environments and exit, useful before offline or scheduled execution.
- `--list-conda-envs`: list environment definitions and concrete environment locations.
- `--conda-cleanup-envs`: remove unused environments.
- `--conda-cleanup-pkgs tarballs|cache`: clean package tarballs or package cache after environment creation.
- `--conda-base-path DIR`: point Snakemake at a particular Conda base installation when command discovery is ambiguous.
- `--conda-not-block-search-path-envvars`: allow path-mutating environment variables such as `PYTHONPATH` or `R_LIBS`; use only when the workflow deliberately relies on them.
- `--apptainer-prefix DIR` / `--singularity-prefix DIR`: control where images are stored; if omitted, `APPTAINER_CACHEDIR` may be used.
- `--apptainer-args '...'` / `--singularity-args '...'`: pass engine-specific options, for example `--cleanenv` or bind mounts.
- `--containerize` or `--containerize apptainer`: emit a container specification from Conda environments instead of executing jobs.
- `--archive FILE.tar.gz`: create a workflow archive with tracked workflow files, inputs, and Conda packages for later reproduction on the same platform family.
- `--cache [RULE ...]`: enable between-workflow output caching for named rules or every rule with a `cache:` directive.

Example dry-run planning commands:

```bash
snakemake --cores 1 --dry-run --printshellcmds --sdm conda
snakemake --cores 1 --dry-run --printshellcmds --sdm conda apptainer --apptainer-args '--cleanenv'
snakemake --cores 1 --dry-run --printshellcmds --use-envmodules
```

## Conda directives

Rule-level Conda environments are declared with `conda:`. Relative environment paths are resolved relative to the Snakefile that contains the rule, not necessarily the shell's current directory.

```python
rule plot:
    input: "table.txt"
    output: "plots/myplot.pdf"
    conda: "envs/plot.yaml"
    script: "scripts/plot.R"
```

Environment YAML should pin channels and important package versions:

```yaml
channels:
  - conda-forge
  - bioconda
  - nodefaults
dependencies:
  - r-base=4.3
  - r-ggplot2=3.5
```

Snakemake stores generated Conda environments under `.snakemake/conda/<hash>` by default. The hash is based on environment definition content and, when applicable, container image identity. Changing the environment file creates a different environment instead of mutating the old one in place.

### Exact pins

If `envs/tool.yaml` has a sibling file named for the current platform, such as `envs/tool.linux-64.pin.txt`, Snakemake first tries Conda's explicit specification format from the pin file and falls back to the YAML if that fails. Treat pin files as release artifacts: update them whenever the YAML changes.

### Post-deploy scripts

A sibling `envs/tool.post-deploy.sh` can patch a generated environment after Conda installation. The environment path is available as `$CONDA_PREFIX` inside the script.

```bash
#!env bash
set -o pipefail
Rscript --no-environ -e 'Sys.setenv(R_REMOTES_NO_ERRORS_FROM_WARNINGS="false"); remotes::install_github("org/package", ref="v1.2.3", upgrade="never")'
```

Use a shebang when relying on shell-specific behavior. Avoid inheriting user-level package paths into post-deployment scripts unless that is intentional.

### Existing named environments

`conda: "name"` or `conda: "/path/to/env"` activates an existing environment rather than creating one. This is convenient for local development but weak for reproducibility. Prefer environment definition files for portable workflows.

### Global workflow dependencies

A global `conda:` directive near the beginning of the Snakefile can inject dependencies needed before any rule executes, such as storage plugins or Python packages used while parsing the workflow:

```python
conda:
    "envs/global.yaml"
```

Global dependencies still require Conda deployment, for example:

```bash
snakemake --cores 8 --sdm conda
```

## Containers

Use a rule-level `container:` or global `container:` directive with Apptainer-compatible image URLs. `docker://...` is a common portable choice.

```python
container: "docker://continuumio/miniconda3:24.1.2-0"

rule plot:
    input: "table.txt"
    output: "plots/myplot.pdf"
    conda: "envs/plot.yaml"
    shell: "Rscript scripts/plot.R {input} {output}"
```

Run with both OS and package deployment:

```bash
snakemake --cores 8 --sdm conda apptainer --apptainer-args '--cleanenv'
```

Important behavior:

- Apptainer/Singularity must be available on the target host. Snakemake checks for `apptainer` first, then `singularity`.
- Minimum versions enforced by Snakemake are Apptainer 1.0.0 or Singularity 2.4.1.
- Apptainer/Singularity may pass host environment variables into containers. Add `--apptainer-args '--cleanenv'` when host contamination is a concern.
- `shell`, `script`, `wrapper`, `notebook`, and `run` interact differently with deployment. For `run`, Conda/container directives only affect shell calls launched from inside the Python `run` block because the block itself executes in the Snakemake process.
- Files resolved through `workflow.source_path(...)` are made available in containers via the source cache. Prefer `workflow.source_path(...)` in `input` rather than `params` when the file should be stable for rerun decisions.

Generate a container spec from Conda environments:

```bash
snakemake --containerize > Dockerfile
snakemake --containerize apptainer > workflow.def
```

Inside a workflow that uses a built image, use the `containerized:` directive:

```python
containerized: "docker://example/workflow:1.0.0"
```

## Environment modules

`envmodules:` is intended for HPC systems where optimized modules exist. Provide a Conda or container fallback whenever the workflow should run outside that site.

```python
rule align:
    input: "genome.fa", "reads.fq"
    output: "mapped.bam"
    conda: "envs/align.yaml"
    envmodules:
        "bio/bwa/0.7.17",
        "bio/samtools/1.19"
    shell:
        "bwa mem {input} | samtools view -Sbh - > {output}"
```

Site-specific run:

```bash
snakemake --cores 32 --use-envmodules
```

Portable fallback:

```bash
snakemake --cores 32 --sdm conda
```

## Source deployment and non-shared execution

Executor plugins may run jobs where working directories, source files, software deployments, persistence, or storage cache are not on a shared filesystem. Plan around these flags:

- `--shared-fs-usage ...`: declare which surfaces are shared. Values are executor-dependent but include concepts such as persistence, software deployment, sources, source cache, input/output, and storage-local-copies.
- `--job-deploy-sources` / `--no-job-deploy-sources`: control whether remote jobs receive a source archive when needed.
- `--runtime-source-cache-path PATH`: internal/runtime source cache path passed to spawned jobs; normally do not set manually.
- `--local-storage-prefix PATH`: local staging path for storage provider objects.
- `--remote-job-local-storage-prefix PATH`: local staging path for jobs that run remotely.

A cautious planning command for a non-shared cluster/cloud scenario:

```bash
snakemake --executor slurm --cores 32 \
  --sdm conda apptainer \
  --default-storage-provider fs \
  --shared-fs-usage persistence software-deployment sources source-cache \
  --local-storage-prefix .snakemake/storage \
  --dry-run --printshellcmds
```

Treat this as a template: executor plugins add their own required flags and resources.

## Between-workflow output cache

Output caching is for reusing expensive results across workflows or users. It is not needed for normal within-workflow up-to-date checking.

```bash
export SNAKEMAKE_OUTPUT_CACHE=/shared/snakemake-output-cache
snakemake --cores 8 --cache download_data create_index
```

Or mark rules:

```python
rule download_data:
    output: "results/data/worldcitiespop.csv"
    cache: True  # also accepts "all" or "omit-software"
    shell: "curl -L https://example.org/worldcitiespop.csv > {output}"
```

Then run:

```bash
snakemake --cores 8 --cache
```

Constraints and signals:

- Cacheable rules need output files. Multiple outputs must use `multiext(...)` or named outputs.
- Hashing includes software stack unless `cache: "omit-software"` is used.
- Shell/script code should receive variable information through `params`; direct use of uncaptured globals, `config`, or `wildcards` in scripts can make cache provenance invalid.
- Cache contents on local filesystems are made readable and writable for all users; do not use for private data.
- Missing or unreadable cache paths surface as cache-location errors involving `SNAKEMAKE_OUTPUT_CACHE`.

## Archives

Use archives to publish or transfer a reproducible workflow snapshot:

```bash
snakemake --archive workflow.tar.gz
```

The archive includes workflow files under version control, inputs required by the DAG, and Conda packages for declared environments. It is platform-specific: an archive produced on one platform family should be rerun on a compatible platform.

Expected follow-up:

```bash
tar -xf workflow.tar.gz
snakemake --cores 1 --dry-run --printshellcmds
```

Before creating an archive, check:

- Required scripts, configs, schemas, notebooks, and environment files are tracked or otherwise included through workflow inputs/source references.
- Every rule that needs software has `conda:`, `container:`, `containerized:`, or a documented module fallback.
- External secrets and credentials are not baked into files that will be archived.

## Jobscript deployment surface

The default jobscript template contains a properties header and an executable body:

```sh
#!/bin/sh
# properties = {properties}
{exec_job}
```

When using `--jobscript CUSTOM.sh`, preserve a parseable `# properties = ...` line if executor submit wrappers need rule, resources, threads, input, output, params, or wildcards. Use the bundled inspector to validate a generated jobscript:

```bash
python scripts/inspect_job_properties.py path/to/jobscript.sh --summary
```
