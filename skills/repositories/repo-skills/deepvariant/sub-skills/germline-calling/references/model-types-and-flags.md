# Model Types and `run_deepvariant` Flags

DeepVariant `1.10.0` exposes standard single-sample germline calling through `/opt/deepvariant/bin/run_deepvariant` in the released container or through Bazel/source-built binaries. The lightweight Python package does not expose console scripts and is not enough for production variant calling.

## Model-Type Selection

| Model type | Use when | Avoid when |
| --- | --- | --- |
| `WGS` | Illumina short-read whole-genome sequencing. | Exome/capture data, long reads, RNA/MAS-Seq, trio-specific calling. |
| `WES` | Illumina short-read exome or capture sequencing, usually with a BED in `--regions`. | Whole-genome or long-read data. |
| `PACBIO` | PacBio HiFi germline reads aligned to the selected reference. | ONT, Illumina-only, or hybrid evidence that expects the hybrid model. |
| `ONT_R104` | Oxford Nanopore R10.4.1 simplex or duplex germline reads. | Older ONT chemistry, PacBio HiFi, Illumina. |
| `HYBRID_PACBIO_ILLUMINA` | Combined PacBio HiFi and Illumina evidence prepared for the hybrid model. | Separate unmerged read files or a merged file with incompatible read preparation. |
| `MASSEQ` | MAS-Seq data matching the r1.10 model assumptions. | General RNA-seq, DNA WGS/WES, or generic Iso-Seq workflows without matching model provenance. |
| `RNASEQ` | RNA-seq reads, usually restricted to expressed or target regions. | DNA WGS/WES/long-read calling. |

If the user provides a custom model, still set the closest `--model_type`. The wrapper uses model type to select model-specific `make_examples` behavior and defaults; `--customized_model` replaces the checkpoint used by `call_variants` but does not make an arbitrary assay compatible.

## Required Flags

| Flag | Meaning | Validation |
| --- | --- | --- |
| `--model_type` | One of the seven supported model families. | Must match assay, chemistry, and intended model metadata. |
| `--ref` | FASTA or bgzipped FASTA reference visible inside the container. | Needs `.fai`; contig names must match reads and regions. |
| `--reads` | Aligned, sorted, indexed BAM or CRAM visible inside the container. | BAM needs `.bai`; CRAM needs `.crai`; must be aligned to a compatible reference. |
| `--output_vcf` | Final VCF path, normally `*.vcf.gz`, in a mounted writable output directory. | Parent directory must exist and be mounted; expect `.tbi` after success. |

## Common Optional Flags

| Flag | Use | Notes |
| --- | --- | --- |
| `--output_gvcf` | Emit a final gVCF containing variant and non-variant reference-block records. | Required for many cohort merge or joint-genotyping workflows; expect `.tbi`; increases postprocess runtime and memory. |
| `--regions` | Limit calling to contig, interval, space-separated intervals, BED, or BEDPE. | Contig names must exist in reference and reads; quote space-separated lists. |
| `--num_shards` | Parallelism for `make_examples`. | Usually set to available CPU cores; too high can overuse memory or storage. |
| `--vcf_stats_report=true` | Produce VCF visual report HTML. | The report is based on the output VCF; output path derives from the VCF basename. |
| `--report_title` | Set a human-readable title for VCF stats and runtime reports. | Optional; otherwise the wrapper infers a title where possible. |
| `--logging_dir` | Save per-stage logs and runtime outputs. | Must be writable and mounted; required for `--runtime_report=true`. |
| `--runtime_report=true` | Generate make-examples runtime-by-region data and report. | Only works with `--logging_dir`; creates runtime TSV shards and an HTML report. |
| `--intermediate_results_dir` | Keep intermediate TFRecords and call-variants output. | Must be visible inside container; useful for debugging or stage-by-stage reruns. |
| `--dry_run=true` | Print stage commands without executing them. | Use for planning, routing to stage customization, or reviewing model-specific flags. |
| `--sample_name` | Override sample name from read group `SM` tag. | Use cautiously because the final VCF sample name changes. |

## gVCF Behavior

When `--output_gvcf` is set, `run_deepvariant` wires gVCF support through the internal stages:

- `make_examples` writes sharded non-variant-site TFRecords.
- `postprocess_variants` consumes those TFRecords with variant calls and writes the final gVCF.
- The final VCF contains variant records; the final gVCF contains variant records plus non-variant reference blocks with `<*>` alleles.
- gVCF support is for calling mode, not training mode.
- Low-depth data can produce larger gVCFs because fewer adjacent reference blocks can be merged at high genotype quality.

To include `MED_DP` in gVCF records, route the setting through `--make_examples_extra_args`:

```bash
--make_examples_extra_args="include_med_dp=true"
```

To change reference-block binning, use a dry run and pass the relevant make-examples flag through extra args only after confirming downstream requirements:

```bash
--make_examples_extra_args="gvcf_gq_binsize=5"
```

## VCF Stats and Runtime Reports

`--vcf_stats_report=true` adds a visual report command after the VCF is produced. Use `--report_title` when the report needs a specific human-readable title.

`--runtime_report=true` requires `--logging_dir`. It adds make-examples runtime-by-region output and a runtime visualization command. Use it for performance debugging; it is not needed for routine calling.

## Haploid and PAR Flags

DeepVariant is a diploid caller by default. For regions that should be treated as haploid, use:

```bash
--haploid_contigs="chrX,chrY"
--par_regions_bed=/input/GRCh38_PAR.bed
```

Rules:

- Use `chrX,chrY` with GRCh38-style references and `X,Y` with GRCh37-style references.
- Use haploid flags for XY samples when non-PAR X/Y regions should not emit heterozygous genotypes.
- Do not use `--haploid_contigs` for XX samples by default.
- `--par_regions_bed` must match the same reference naming and coordinates as `--ref`; PAR regions are excluded from haploid genotype adjustment.
- The wrapper passes haploid/PAR settings into both `make_examples` and `postprocess_variants` behavior.

## Long-Read Phasing Flag

`--phase_vcf` controls whether long-read models emit phasing information in VCF output. The r1.10 wrapper defaults this on for `PACBIO` and `ONT_R104` and off for other models. Setting `--phase_vcf=true` for non-long-read models is invalid.

## Small Model Flags

The small model can reduce work in `make_examples` by classifying easy candidates before CNN evaluation. Behavior is model-metadata-driven in r1.10.

| Flag | Effect |
| --- | --- |
| `--disable_small_model=true` | Disable small-model candidate classification entirely. |
| `--customized_small_model` | Use a custom small-model checkpoint for `make_examples`. |
| `--make_examples_extra_args="small_model_snp_gq_threshold=N"` | Change the SNP GQ threshold for accepting small-model calls; `-1` disables SNP small-model calls. |
| `--make_examples_extra_args="small_model_indel_gq_threshold=N"` | Change the indel GQ threshold; `-1` disables indel small-model calls. |

Use `--disable_small_model=true` when a custom model lacks compatible metadata, when every candidate should pass through the CNN for review, or when a documented assay workflow recommends it, such as RNA-seq examples.

## Custom Model Flags

Use `--customized_model` for a custom checkpoint prefix or SavedModel directory. In r1.10, the model must have compatible model metadata:

- Checkpoint prefix form requires files like `model.ckpt.data-00000-of-00001` and `model.ckpt.index`.
- SavedModel directory form requires `saved_model.pb` inside the directory.
- The model directory should contain `model.example_info.json`, or the command should provide `--customized_model_json` pointing to it.
- Metadata describes `make_examples` behavior; missing or mismatched metadata can produce incorrect examples even if `call_variants` can load weights.

When a user has a trained checkpoint and asks how to use it, route training and metadata validation to `../training-custom-models/SKILL.md`, then return here for the final inference command.

## Extra-Args Formatting

The wrapper accepts comma-separated `flag_name=flag_value` lists for stage-specific flags:

```bash
--make_examples_extra_args="include_med_dp=true,min_mapping_quality=1"
--call_variants_extra_args="batch_size=1024"
--postprocess_variants_extra_args="qual_filter=2.0"
```

Formatting rules:

- Use commas between assignments, not spaces.
- Use `true` or `false` for booleans.
- Quote the whole string in the shell.
- If a value itself contains spaces or commas, quote the value inside the assignment and test with `--dry_run=true`.
- Do not use extra args to paper over a model/data mismatch; route low-level stage choices to `../pipeline-stages/SKILL.md`.

## CRAM Notes

CRAM input is supported. The command should still pass a compatible `--ref`; modern DeepVariant releases use that reference for CRAM decoding by default rather than relying on the reference URI encoded in the CRAM. Ensure CRAM index and reference index paths are mounted and visible. If a user asks about `use_ref_for_cram`, treat it as a lower-level `make_examples` flag and verify the generated stage command with `--dry_run=true`.

## Dry-Run Planning

Use `--dry_run=true` when:

- The user wants to run stages separately.
- You need to inspect model-specific `make_examples` flags.
- You are debugging custom-model metadata, haploid flags, gVCF wiring, small-model settings, phasing behavior, or extra args.
- You want a safe native verification candidate without full Docker execution.

A dry run prints commands but still requires the container and wrapper binary if executed inside Docker/Singularity.
