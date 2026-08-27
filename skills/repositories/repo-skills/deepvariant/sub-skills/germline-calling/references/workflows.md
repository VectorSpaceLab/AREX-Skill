# Germline `run_deepvariant` Workflows

This reference gives self-contained command patterns for single-sample DeepVariant germline calling with DeepVariant `1.10.0`. Commands are templates for user-reviewed Docker or Singularity execution; do not run them automatically without confirming container runtime, image availability, mounted data, CPU/GPU resources, and output locations.

## Preflight Checklist

Before building a command:

1. Choose one model type from the assay: `WGS`, `WES`, `PACBIO`, `ONT_R104`, `HYBRID_PACBIO_ILLUMINA`, `MASSEQ`, or `RNASEQ`.
2. Confirm `--ref` is an uncompressed or bgzipped FASTA with a matching `.fai` index visible inside the container.
3. Confirm `--reads` is an aligned, sorted, indexed BAM or CRAM. BAM needs `.bai`; CRAM needs `.crai` or a colocated CRAM index.
4. Confirm reads were aligned to a reference compatible with `--ref`. DeepVariant processes shared contigs; inconsistent `chr20` versus `20`, decoy, alt, or HLA contig naming can exclude regions or fail validation.
5. Confirm every input parent and output parent is mounted into the container path used by flags.
6. If `--regions` is present, use contig names from the FASTA/read headers and quote space-separated region lists.
7. Decide whether outputs need `--output_gvcf`, `--vcf_stats_report=true`, `--logging_dir`, `--runtime_report=true`, haploid/PAR flags, custom model flags, or `--dry_run=true`.
8. If `--customized_model` is present, confirm the checkpoint prefix or SavedModel directory is paired with `model.example_info.json` or `--customized_model_json`.

## Docker Command Shape

Use `google/deepvariant:1.10.0` for CPU or `google/deepvariant:1.10.0-gpu` with Docker GPU passthrough. `run_deepvariant` lives inside the released image.

```bash
BIN_VERSION="1.10.0"
INPUT_DIR="/host/input"
REFERENCE_DIR="/host/reference"
OUTPUT_DIR="/host/output"
mkdir -p "${OUTPUT_DIR}" "${OUTPUT_DIR}/logs" "${OUTPUT_DIR}/intermediate_results_dir"

sudo docker run \
  -v "${INPUT_DIR}":"/input" \
  -v "${REFERENCE_DIR}":"/reference" \
  -v "${OUTPUT_DIR}":"/output" \
  google/deepvariant:"${BIN_VERSION}" \
  /opt/deepvariant/bin/run_deepvariant \
  --model_type=WGS \
  --ref=/reference/GRCh38_no_alt_analysis_set.fasta \
  --reads=/input/sample.bam \
  --output_vcf=/output/sample.dv.vcf.gz \
  --output_gvcf=/output/sample.dv.g.vcf.gz \
  --regions="chr20" \
  --num_shards="$(nproc)" \
  --vcf_stats_report=true \
  --logging_dir=/output/logs \
  --runtime_report=true \
  --intermediate_results_dir=/output/intermediate_results_dir
```

Add `--dry_run=true` to print the internal `make_examples`, `call_variants`, `postprocess_variants`, optional `vcf_stats_report`, and optional runtime-report commands without executing them.

## GPU Docker Shape

GPU use is optional and environment-dependent. In the standard pipeline, `call_variants` is the GPU-accelerated step; `make_examples` and `postprocess_variants` are CPU-bound. Use one GPU for one sample unless the user has an external strategy for parallel independent samples.

```bash
sudo docker run --gpus 1 \
  -v "${INPUT_DIR}":"/input" \
  -v "${REFERENCE_DIR}":"/reference" \
  -v "${OUTPUT_DIR}":"/output" \
  google/deepvariant:"${BIN_VERSION}-gpu" \
  /opt/deepvariant/bin/run_deepvariant \
  --model_type=WGS \
  --ref=/reference/ref.fa \
  --reads=/input/sample.bam \
  --output_vcf=/output/sample.vcf.gz \
  --num_shards=8
```

If the user has a GPU but omits either `--gpus 1` or the `-gpu` image tag, flag the mismatch. If Docker lacks NVIDIA runtime support, do not install drivers automatically.

## Singularity Shape

Singularity commands depend on the user's host setup and image cache. Bind host paths explicitly. Use `--nv` only with the GPU image and a GPU-capable host. Use `--cleanenv` if host Python/library variables interfere with the container.

```bash
BIN_VERSION="1.10.0"
singularity pull docker://google/deepvariant:"${BIN_VERSION}"

singularity run --cleanenv \
  -B "${INPUT_DIR}":"/input" \
  -B "${REFERENCE_DIR}":"/reference" \
  -B "${OUTPUT_DIR}":"/output" \
  docker://google/deepvariant:"${BIN_VERSION}" \
  /opt/deepvariant/bin/run_deepvariant \
  --model_type=WGS \
  --ref=/reference/ref.fa \
  --reads=/input/sample.bam \
  --output_vcf=/output/sample.vcf.gz \
  --num_shards=8
```

GPU Singularity pattern:

```bash
singularity run --nv --cleanenv \
  -B "${INPUT_DIR}":"/input" \
  -B "${REFERENCE_DIR}":"/reference" \
  -B "${OUTPUT_DIR}":"/output" \
  docker://google/deepvariant:"${BIN_VERSION}-gpu" \
  /opt/deepvariant/bin/run_deepvariant \
  --model_type=WGS \
  --ref=/reference/ref.fa \
  --reads=/input/sample.bam \
  --output_vcf=/output/sample.vcf.gz \
  --num_shards=8
```

## Assay Recipes

### Illumina WGS

Use `--model_type=WGS` for Illumina whole-genome germline data. Common extras are `--output_gvcf`, `--vcf_stats_report=true`, `--logging_dir`, and `--runtime_report=true`.

```bash
/opt/deepvariant/bin/run_deepvariant \
  --model_type=WGS \
  --ref=/reference/ref.fa \
  --reads=/input/wgs.bam \
  --regions="chr20" \
  --output_vcf=/output/wgs.dv.vcf.gz \
  --output_gvcf=/output/wgs.dv.g.vcf.gz \
  --vcf_stats_report=true \
  --num_shards=32
```

### Illumina WES

Use `--model_type=WES` and usually set `--regions` to a capture BED visible inside the container. The wrapper uses safer postprocess CPU defaults for WES when it controls stage commands.

```bash
/opt/deepvariant/bin/run_deepvariant \
  --model_type=WES \
  --ref=/reference/ref.fa \
  --reads=/input/exome.bam \
  --regions=/input/capture_targets.bed \
  --output_vcf=/output/exome.dv.vcf.gz \
  --output_gvcf=/output/exome.dv.g.vcf.gz \
  --num_shards=16
```

### PacBio HiFi

Use `--model_type=PACBIO` for PacBio HiFi germline data. Long-read models can emit phasing information by default in the r1.10 wrapper. Use haploid/PAR flags only when sample karyotype and reference naming justify them.

```bash
/opt/deepvariant/bin/run_deepvariant \
  --model_type=PACBIO \
  --ref=/reference/ref.fa \
  --reads=/input/pacbio_hifi.bam \
  --regions="chr20" \
  --output_vcf=/output/pacbio.dv.vcf.gz \
  --output_gvcf=/output/pacbio.dv.g.vcf.gz \
  --num_shards=32
```

### Oxford Nanopore R10.4

Use `--model_type=ONT_R104` for Oxford Nanopore R10.4.1 simplex or duplex reads matching the model's intended chemistry.

```bash
/opt/deepvariant/bin/run_deepvariant \
  --model_type=ONT_R104 \
  --ref=/reference/ref.fa \
  --reads=/input/ont_r104.bam \
  --regions="chr20" \
  --output_vcf=/output/ont.dv.vcf.gz \
  --output_gvcf=/output/ont.dv.g.vcf.gz \
  --num_shards=32
```

### Hybrid PacBio plus Illumina

Use `--model_type=HYBRID_PACBIO_ILLUMINA` for a single aligned reads file representing the combined PacBio HiFi and Illumina evidence expected by the model. If the user has separate BAMs, decide first whether they have already been merged, sorted, and indexed in a compatible way.

```bash
/opt/deepvariant/bin/run_deepvariant \
  --model_type=HYBRID_PACBIO_ILLUMINA \
  --ref=/reference/ref.fa \
  --reads=/input/hybrid_illumina_pacbio.bam \
  --regions="chr20" \
  --output_vcf=/output/hybrid.dv.vcf.gz \
  --output_gvcf=/output/hybrid.dv.g.vcf.gz \
  --disable_small_model=true \
  --num_shards=32
```

When a hybrid command also uses `--customized_model`, mount the model directory and validate that the checkpoint/SavedModel and `model.example_info.json` were produced for the hybrid evidence representation.

### MAS-Seq

Use `--model_type=MASSEQ` for MAS-Seq data aligned to a compatible reference. The documented pattern uses VCF output and target regions; add gVCF only if downstream processing truly requires it.

```bash
/opt/deepvariant/bin/run_deepvariant \
  --model_type=MASSEQ \
  --ref=/reference/ref.fa \
  --reads=/input/masseq.bam \
  --regions="chr20" \
  --output_vcf=/output/masseq.dv.vcf.gz \
  --num_shards=16
```

### RNA-seq

Use `--model_type=RNASEQ` for RNA-seq data and usually restrict calling to expressed or targeted regions. The documented case-study pattern disables the small model.

```bash
/opt/deepvariant/bin/run_deepvariant \
  --model_type=RNASEQ \
  --ref=/reference/ref.fa \
  --reads=/input/rnaseq.bam \
  --regions=/input/expressed_regions.bed \
  --output_vcf=/output/rnaseq.dv.vcf.gz \
  --disable_small_model=true \
  --num_shards=16
```

## CRAM and bgzipped FASTA Case

For CRAM input, ensure the `.crai` index, `--ref` FASTA, and FASTA `.fai` are visible inside the container. DeepVariant uses the reference passed by `--ref` for CRAM decoding by default in modern releases, rather than relying on the CRAM header URI. If a lower-level workflow changes `use_ref_for_cram`, verify the dry-run stage command and route details to `../pipeline-stages/SKILL.md`.

Example planning command:

```bash
/opt/deepvariant/bin/run_deepvariant \
  --model_type=WGS \
  --ref=/reference/GRCh38.fa.gz \
  --reads=/input/sample.cram \
  --regions="chr20" \
  --output_vcf=/output/sample.dv.vcf.gz \
  --output_gvcf=/output/sample.dv.g.vcf.gz \
  --vcf_stats_report=true \
  --logging_dir=/output/logs \
  --runtime_report=true \
  --num_shards=16 \
  --dry_run=true
```

If contig names in `--regions` are not in the FASTA `.fai`, fix the region string before running. If the CRAM header uses incompatible contigs or was aligned to a different reference, regenerate or realign input rather than forcing the command.

## Outputs to Expect

A successful run can produce:

- `*.vcf.gz` and `*.vcf.gz.tbi` from `--output_vcf`.
- `*.g.vcf.gz` and `*.g.vcf.gz.tbi` from `--output_gvcf`.
- `*.visual_report.html` when `--vcf_stats_report=true`.
- Per-stage logs under `--logging_dir`, if set.
- `make_examples_runtime_by_region_report.html` under `--logging_dir` when `--runtime_report=true`.
- TFRecord intermediates under `--intermediate_results_dir`, if set; otherwise the wrapper may use a temporary directory.

## Dry-Run Planning and Native Candidates

Use `--dry_run=true` when the user wants to run stages separately, inspect model-specific `make_examples` flags, debug gVCF wiring, review small-model settings, confirm haploid/PAR propagation, or validate custom model metadata. A dry run is a safe help-oriented native candidate, but it still requires a working container and mounted paths if executed inside Docker/Singularity.

Native verification candidates for this sub-skill should be classified as safe/help-only for `--help` and command-builder checks, or skip-docker unless the user explicitly provides runtime approval, data, image access, and resources.
