# Nextflow pipeline preflight

The three registered nf-core wrappers are intentionally gated launchers, not
arbitrary `nextflow run` passthroughs:

| ClawBio skill | Upstream contract | Typical handoff |
|---|---|---|
| `scrnaseq-pipeline` | nf-core/scrnaseq 4.1.0; FASTQ samplesheet to scRNA outputs | confirmed `preferred_h5ad` to `scrna` or `scrna-embedding` |
| `rnaseq-pipeline` | nf-core/rnaseq 3.26.0; bulk FASTQ/BAM samplesheet to counts | confirmed `preferred_counts_tsv` to `rnaseq` / DE workflow |
| `sarek-pipeline` | nf-core/sarek 3.8.1; FASTQ/BAM/CRAM/VCF steps to variant outputs | confirmed VCF/CRAM handoff to the named downstream skill |

Read the selected wrapper's own `SKILL.md` for the exhaustive flag and
version-specific rule set. This reference is the integration-level checklist;
it does not replace those contracts.

## Before a real run

1. Identify the input mode and intended downstream handoff. A samplesheet is
   not interchangeable across scrnaseq, rnaseq, and sarek.
2. Select a fresh output directory outside the ClawBio source tree. Pipeline
   outputs can be many GB or TB; never write them into `skills/`, the checkout,
   or a bot runtime directory.
3. Use `--check` with the exact input/reference/profile flags before starting
   Nextflow. `--check` must not start Nextflow. It validates inputs and runtime
   prerequisites but may defer some engine-version detail depending on the
   wrapper; a passing check is not a completed pipeline.
4. Confirm `python3`, Java (>=17), `nextflow` at the wrapper's pinned minimum,
   and the selected execution backend (`docker`, `podman`, `singularity`,
   `apptainer`, `conda`, `mamba`, `shifter`, or `charliecloud`) are available.
   `wave`, `gpu`, and institutional profile modifiers have their own runtime
   implications; an importable Python wrapper does not prove backend readiness.
5. Decide whether the data and references are local. Local-first is the default:
   remote FASTQ/BAM/CRAM/reference URIs are rejected as
   `REMOTE_INPUT_NOT_ALLOWED`. `--allow-remote-inputs` is an explicit opt-in,
   prints the paths that will be fetched, and requires network access. Public
   iGenomes bases and remote object-store work directories are separate
   documented cases; do not conflate them with a local analysis.
6. Check available disk, RAM, scratch/work storage, and container/cache space.
   STAR/Cell Ranger/reference construction and saved alignment intermediates
   can dominate the budget. `--save-align-intermeds` or scrnaseq's default
   intermediate behavior may create very large outputs; disable only with the
   exact supported wrapper flag when appropriate.
7. Pin or verify the pipeline source. Local sibling checkouts are used only
   when their version/commit is verifiable; dirty local sources and version
   overrides require explicit flags and are recorded. Remote sources require
   network access and use the pinned tag.
8. Treat every `-c`, `--config`, and `--nextflow-config` file as trusted
   executable Groovy. The launcher normalizes all three spellings and forwards
   each config to every nf-core wrapper. Configs are not a sandbox; they can
   alter process commands, executors, resources, and includes. Use only files
   you authored or trust. Wrapper-specific params controls and config linting
   still apply; do not use configs to bypass the audited scientific surface.
9. Inspect the preflight output and fix all hard errors before running. Preserve
   warnings about network, timeout, output portability, references, memory, or
   backend. Do not turn a warning into a made-up assurance.

## Exact CLI boundary

At the integrated launcher layer, common controls include:

```bash
clawbio run <pipeline> --input <samplesheet> --output <out> --check
clawbio run <pipeline> --demo --output <out>
clawbio run <pipeline> --profile docker --pipeline-version <tag>
clawbio run <pipeline> -c site.config --nextflow-config extra.config
clawbio run <pipeline> --resume
```

`--demo`, `--input`, and `--output` are runner-managed. Do not pass these as
`extra_args`; the runner blocks them. Extra pipeline flags are filtered through
the per-skill allowlist. For the three nf-core skills, both hyphenated wrapper
flags and nf-core-native snake_case spellings are canonicalized to the wrapper's
hyphenated spelling, but unknown flags remain blocked. Use the exact spelling
shown by the selected wrapper's help, not a guessed parameter.

The CLI has a special profile distinction: for pipeline skills, `--profile`
means a Nextflow backend/profile list (for example `docker` or `docker,arm64`),
not a patient JSON profile. The CLI recognizes this before calling the common
runner. A patient profile is a separate core-runner concept.

## Pipeline-specific checks

### scRNA (`scrnaseq-pipeline`)

- Samplesheet requires the wrapper's required columns (`sample`, `fastq_1`,
  `fastq_2`) and preset-specific fields. The wrapper validates FASTQs, sample
  values, reference/index combinations, protocol, and backend before launch.
- Presets include `standard`, `star`, `kallisto`, `cellranger`,
  `cellrangerarc`, and `cellrangermulti`. Do not combine `--genome` with a
  conflicting explicit genome FASTA or genome-level index. Explicit references
  may cause `igenomes_ignore` to be set automatically.
- `--demo` runs the upstream public test profile, forces its own preset/config,
  and requires network access to fetch public test data and references. It is
  not an offline substitute for local synthetic data. `NXF_OFFLINE` should
  produce the documented demo network failure rather than a long attempt.
- `--run-downstream` is opt-in. Chain only when the wrapper confirms a
  `preferred_h5ad`; an ambiguous per-sample-only result has
  `handoff_available=false`.

### bulk RNA-seq (`rnaseq-pipeline`)

- Real samplesheets require the nf-core/rnaseq columns and valid strandedness;
  BAM reprocessing has additional BAM fields and should use the same aligner
  route that produced the BAMs.
- Choose one compatible reference strategy (`--genome` or explicit reference /
  indices), with only documented additive annotation/transcriptome overrides.
- `hisat2` alignment-only mode does not produce the usual count handoff unless
  a supported pseudo-aligner route is also selected. `--run-downstream` only
  launches DE when its required metadata, formula, and contrast are present;
  otherwise the wrapper emits a copy-paste template or report guidance.
- `--demo` uses upstream test data and network. It does not exercise a local
  patient/cohort input.

### variant pipeline (`sarek-pipeline`)

- Input formats and required columns depend on `--step`: mapping, duplicate
  marking, recalibration, variant calling, or annotation. Sample status drives
  germline/tumor/normal mode; there is no invented `--tumor-only` shortcut.
- Reference and caller resources are validated before launch. BQSR known-sites,
  Mutect2 germline/PON resources, ASCAT resources, annotation caches, and
  Sentieon licensing are real prerequisites; do not silently skip them.
- `--demo` clears user reference/input overrides and uses the public upstream
  test profile. `--resume` is valid only when the stored manifest agrees on
  source/version/profile/step/parameters/references/samplesheet.
- Downstream chaining is opt-in with the wrapper's supported
  `--run-downstream --downstream-skill` contract. It does not perform clinical
  interpretation itself.

## Profiles, work dirs, and resume

The default backend/profile must be selected deliberately. Docker and
Singularity/Apptainer need daemon/image/runtime access; Conda/Mamba may resolve
packages from network channels unless caches are already warm; GPU profiles need
compatible hardware and drivers; ARM/Wave may need an external Wave service or
mirrored images. A present binary is not proof of a usable image, daemon,
license, driver, registry, or site profile.

Wrappers use a reproducibility bundle with normalized inputs, effective
`params.yaml`, command/config snapshots, checksums, manifests, and logs. The
work directory defaults under the output bundle, but `--work-dir` can target an
object store for supported execution contexts. Published results remain local
where the wrapper needs to parse them and make a handoff. Remote work does not
make local output or credentials portable.

Use `--resume` only for a compatible prior run. Resume state can include the
pipeline source/version, composed profile, step/preset/aligner, effective
parameter checksum, samplesheet/reference checksums, and work directory. If a
wrapper returns `INVALID_RESUME_STATE`, use a new output directory or restore
exactly the recorded state; never override the guard by hand.

## After execution

Treat success as a bundle inspection task. Verify `result.json` and `report.md`,
then inspect logs and confirmed paths. The common integration handoff fields are
pipeline-specific:

- scrnaseq: `preferred_h5ad`, `handoff_available`.
- rnaseq: `preferred_counts_tsv` and any DE handoff/template.
- sarek: detected CRAM/VCF/annotation artifacts and any explicit downstream
  handoff.

Point normal output parsing and replay questions to
[core-runner](../../core-runner/SKILL.md). Point scientific analysis to the
specialist skill; a wrapper's existence of a VCF/count matrix/h5ad is not a
scientific conclusion.
