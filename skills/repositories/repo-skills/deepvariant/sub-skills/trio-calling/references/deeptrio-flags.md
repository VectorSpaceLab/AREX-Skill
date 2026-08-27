# DeepTrio Flags And Data Contracts

DeepTrio production commands use `/opt/deepvariant/bin/deeptrio/run_deeptrio` from a DeepTrio Docker image or equivalent Bazel-built binary. The wrapper orchestrates DeepTrio `make_examples`, shared DeepVariant `call_variants`, and shared `postprocess_variants` for child and parent samples.

## Required Flag Groups

| Group | Trio requirement | Duo requirement | Notes |
| --- | --- | --- | --- |
| `--model_type` | Required | Required | One of `WGS`, `WES`, `PACBIO`, `ONT` in the r1.10 wrapper. |
| `--ref` | Required | Required | FASTA must have a `.fai`; BAM contigs must be compatible. |
| `--reads_child` | Required | Required | Child sorted/indexed BAM. |
| `--sample_name_child` | Required by this skill | Required by this skill | The wrapper can infer from BAM headers, but this skill requires explicit names for safer family plans. |
| `--output_vcf_child` | Required | Required | Child VCF path. |
| `--reads_parent1` | Required by this skill | Required by this skill | The available parent for duo mode. |
| `--sample_name_parent1` | Required by this skill | Required by this skill | Must match the intended pedigree. |
| `--output_vcf_parent1` | Required by this skill | Required by this skill | Parent1 VCF path. |
| `--reads_parent2` | Required | Omit | Do not provide any parent2 flags in duo mode. |
| `--sample_name_parent2` | Required | Omit | Must be omitted with absent parent2. |
| `--output_vcf_parent2` | Required | Omit | Parent2 VCF path only in trio mode. |

The r1.10 wrapper enforces all-or-none parent groups: if any of `reads_parent1`, `output_vcf_parent1`, or `sample_name_parent1` is set, all three must be set; the same grouping applies to parent2. This skill treats parent1 as required because a DeepTrio family-calling plan needs child plus at least one parent.

## Model Type Selection

| `--model_type` | Use for | Important behavior |
| --- | --- | --- |
| `WGS` | Illumina whole-genome trio/duo data | Uses WGS child and parent checkpoints; small-model candidate calling is enabled by default unless disabled. |
| `WES` | Illumina whole-exome data | Pair with capture BED or target intervals in `--regions`; postprocess uses WES-specific multiallelic handling. |
| `PACBIO` | PacBio HiFi whole-genome data | Candidate partitioning is enabled automatically; long-read `make_examples` uses PacBio-specific pileup, phasing, and read-filter settings. |
| `ONT` | Oxford Nanopore trio/duo data when supported by the chosen image | Candidate partitioning is enabled automatically; verify image/model availability before production use. |

DeepTrio models in this evidence set are trained for human diploid germline calling. Do not imply production suitability for other organisms or copy-number regimes without a custom model and validation plan.

## Optional Outputs

| Flag | Meaning | Guidance |
| --- | --- | --- |
| `--output_gvcf_child` | Child gVCF | Required for GLnexus merge of the child. |
| `--output_gvcf_parent1` | Parent1 gVCF | Required for GLnexus merge of parent1. |
| `--output_gvcf_parent2` | Parent2 gVCF | Required only when parent2 is supplied. |
| `--vcf_stats_report` | Per-sample HTML stats report | Produces report files for each per-sample VCF output. |
| `--intermediate_results_dir` | Stage intermediates | Useful for debugging, dry-run stage inspection, and preserving TFRecords. |
| `--logging_dir` | Stage logs | Required with `--runtime_report`. |
| `--runtime_report` | Runtime-by-region HTML report | Only works with `--logging_dir`. |

If any gVCF is requested for a GLnexus workflow, request gVCFs for every supplied sample. Partial gVCF sets cause confusing merge failures and should be rejected during planning.

## Region And BED Handling

`--regions` accepts a space-separated list of region literals or BED/BEDPE paths visible inside the container. Examples include `chr20`, `chr20:10,000,000-10,010,000`, and `/input/exome_targets.bed`. Contig names must match the FASTA index and BAM headers.

For WES, pair `--model_type WES` with the capture BED or equivalent intervals when the user wants targeted calling. For WGS, PacBio, and ONT examples, `--regions` is often used to make demonstrations fast; full production runs may omit it.

## Candidate Partitioning

The wrapper can run `make_examples` in two candidate-partition modes:

1. `candidate_sweep` writes candidate positions.
2. Candidate-partition `calling` consumes those positions and creates examples.

For `PACBIO` and `ONT`, r1.10 turns candidate partitioning on automatically to reduce memory pressure. Users should expect extra `candidate_positions@N` outputs and two `make_examples` commands before `call_variants`. WGS/WES can also use candidate partitioning with wrapper flags, but that is lower-level stage customization and should be routed to the `pipeline-stages` sub-skill.

## Customization Flags

Route detailed stage customization to the `pipeline-stages` sub-skill, but recognize these wrapper flags when they appear in user requests:

- `--customized_model_child` and `--customized_model_parent`: override child/parent `call_variants` checkpoints.
- `--disable_small_model`: disables small-model candidate calling during `make_examples`.
- `--customized_small_model` and `--customized_small_model_parent`: use custom child/parent small models.
- `--make_examples_extra_args`, `--call_variants_extra_args`, `--postprocess_variants_child_extra_args`, `--postprocess_variants_parent1_extra_args`, `--postprocess_variants_parent2_extra_args`: comma-separated `flag=value` strings passed to lower-level stages.
- `--dry_run=true`: print underlying stage commands without executing them inside `run_deeptrio`.
- `--emit_vcf_by_small_model_gq_values`: experimental extra VCF outputs by small-model GQ thresholds.

Do not use the deprecated `--postprocess_variants_extra_args`; keep child, parent1, and parent2 postprocess extra args separate.

## GLnexus Config Handoff

GLnexus consumes DeepVariant/DeepTrio gVCFs. Match the config to assay and intent:

- WES trio/cohort merge: `DeepVariantWES`, usually with the same capture BED passed through `--bed`.
- WGS trio/cohort merge: `DeepVariantWGS` for standard best-practice merging; `DeepVariant_unfiltered` when the user explicitly requests unfiltered DeepVariant gVCF behavior.
- PacBio/ONT trio merge: `DeepVariant_unfiltered` is the safest documented handoff in this r1.10 evidence set unless the user supplies a validated long-read GLnexus configuration.

Always confirm all gVCFs were generated with the same reference, compatible region policy, model family, and sample naming plan before merging.
