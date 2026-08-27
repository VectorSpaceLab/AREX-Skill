# DeepTrio Workflows

Use this reference to plan family-level DeepTrio commands. It distills the repository README, DeepTrio details, quick start, WGS/PacBio case studies, GLnexus merge guidance, wrapper tests, and `run_deeptrio` source behavior into self-contained runtime guidance.

## Preflight Checklist

Confirm these facts before constructing a command:

- `family_mode`: a trio has child, parent1, and parent2; a duo has child and exactly one parent.
- `model_type`: use `WGS`, `WES`, `PACBIO`, or `ONT` to match the sequencing technology and the DeepTrio image/model contents.
- `ref`: the FASTA is container-visible and has a matching `.fai` index.
- `reads_*`: every child/parent BAM is sorted, indexed with `.bai`, physically present on disk, and aligned to a reference compatible with `--ref`.
- `sample_name_*`: explicit unique sample names are strongly preferred so output VCF/gVCF headers, pedigree files, and downstream checks agree.
- `output_vcf_*`: provide one VCF output path for every supplied sample.
- `output_gvcf_*`: provide one gVCF output path for every supplied sample when GLnexus or cohort merging is requested.
- `regions`: optional for WGS/PacBio/ONT slices; usually a capture BED or target interval for WES.
- `num_shards`: a positive integer sized to CPU cores available inside the container.

## Build A Duo WES Command

Use duo mode when only one parent is available. Omit every parent2 input, sample-name, VCF, and gVCF flag. If the user asks for child-only downstream analysis, still plan parent1 VCF/gVCF outputs for the DeepTrio run; downstream analysis can select the child files afterward.

```bash
python scripts/deeptrio_command_builder.py \
  --mode duo \
  --model-type WES \
  --bin-version 1.10.0 \
  --mount /host/ref:/reference \
  --mount /host/family:/input \
  --mount /host/output:/output \
  --ref /reference/GRCh38.fasta \
  --reads-child /input/child.exome.bam \
  --reads-parent1 /input/mother.exome.bam \
  --sample-name-child CHILD \
  --sample-name-parent1 MOTHER \
  --output-vcf-child /output/CHILD.deeptrio.vcf.gz \
  --output-vcf-parent1 /output/MOTHER.deeptrio.vcf.gz \
  --output-gvcf-child /output/CHILD.deeptrio.g.vcf.gz \
  --output-gvcf-parent1 /output/MOTHER.deeptrio.g.vcf.gz \
  --regions /input/exome_targets.bed \
  --num-shards 32 \
  --deeptrio-dry-run
```

Review the generated Docker command with the user. `--deeptrio-dry-run` adds `--dry_run=true` to `run_deeptrio`, causing DeepTrio to print underlying stage commands instead of executing them when the user later runs the command.

## Build A Trio WGS Command

For a complete trio, pass child, parent1, and parent2 input/sample/output groups together.

```bash
python scripts/deeptrio_command_builder.py \
  --mode trio \
  --model-type WGS \
  --bin-version 1.10.0 \
  --mount /host/ref:/reference \
  --mount /host/input:/input \
  --mount /host/output:/output \
  --ref /reference/GRCh38_no_alt_analysis_set.fasta \
  --reads-child /input/HG002.bam \
  --reads-parent1 /input/HG003.bam \
  --reads-parent2 /input/HG004.bam \
  --sample-name-child HG002 \
  --sample-name-parent1 HG003 \
  --sample-name-parent2 HG004 \
  --output-vcf-child /output/HG002.output.vcf.gz \
  --output-vcf-parent1 /output/HG003.output.vcf.gz \
  --output-vcf-parent2 /output/HG004.output.vcf.gz \
  --output-gvcf-child /output/HG002.g.vcf.gz \
  --output-gvcf-parent1 /output/HG003.g.vcf.gz \
  --output-gvcf-parent2 /output/HG004.g.vcf.gz \
  --regions chr20 \
  --intermediate-results-dir /output/intermediate_results_dir \
  --num-shards 64
```

Expected final outputs after an approved DeepTrio run are one compressed/indexed VCF per supplied sample and one compressed/indexed gVCF per supplied sample when gVCFs are requested. With `--intermediate_results_dir`, expect sample-specific `make_examples_*`, `call_variants_output_*`, and `gvcf_*` intermediates.

## PacBio Or ONT Trio With Candidate Partitioning

The r1.10 wrapper always enables candidate partitioning for `PACBIO` and `ONT` model types because direct long-read `make_examples` can run out of memory. Expect a candidate-sweep `make_examples` phase and then a candidate-partition inference phase before `call_variants`.

```bash
python scripts/deeptrio_command_builder.py \
  --mode trio \
  --model-type PACBIO \
  --bin-version 1.10.0 \
  --mount /host/ref:/reference \
  --mount /host/pacbio:/input \
  --mount /host/output:/output \
  --ref /reference/GRCh38_no_alt_analysis_set.fasta \
  --reads-child /input/HG002.hifi.bam \
  --reads-parent1 /input/HG003.hifi.bam \
  --reads-parent2 /input/HG004.hifi.bam \
  --sample-name-child HG002 \
  --sample-name-parent1 HG003 \
  --sample-name-parent2 HG004 \
  --output-vcf-child /output/HG002.deeptrio.vcf.gz \
  --output-vcf-parent1 /output/HG003.deeptrio.vcf.gz \
  --output-vcf-parent2 /output/HG004.deeptrio.vcf.gz \
  --output-gvcf-child /output/HG002.deeptrio.g.vcf.gz \
  --output-gvcf-parent1 /output/HG003.deeptrio.g.vcf.gz \
  --output-gvcf-parent2 /output/HG004.deeptrio.g.vcf.gz \
  --regions chr20 \
  --num-shards 64 \
  --emit-glnexus \
  --glnexus-config DeepVariant_unfiltered \
  --merged-vcf-host /host/output/HG002_trio_merged.vcf.gz
```

If the user asks why long-read runs have extra intermediates, explain that candidate positions are swept first and then reused to balance candidate partitions and reduce memory pressure.

## GLnexus Merge Handoff

DeepTrio writes per-sample VCFs and, when requested, per-sample gVCFs. GLnexus merging consumes gVCFs, not ordinary VCFs. Use a GLnexus command only after all expected `.g.vcf.gz` files and `.g.vcf.gz.tbi` indexes exist.

Config guidance:

- `WES`: use `DeepVariantWES`; include the capture BED with `--bed` when applicable.
- `WGS`: use `DeepVariantWGS` for standard best-practice cohort merging, or `DeepVariant_unfiltered` when the user explicitly wants the less-filtered DeepVariant gVCF behavior used in DeepTrio case-study commands.
- `PACBIO` and `ONT`: prefer `DeepVariant_unfiltered` unless the user has a validated GLnexus preset for the long-read workflow.

The command builder emits GLnexus as a shell pipeline. The gVCF inputs must be container-visible paths, while the final `>` redirect path is evaluated by the host shell.

## Sex Chromosome Caveat

For non-PAR regions of X and Y, run DeepTrio with only the parent who contributed the child's chromosome. For example, a son's non-PAR X should use child plus mother, and non-PAR Y should use child plus father. Keep PAR regions and autosomes in the normal trio/duo plan unless the user has a separate haploid/sex-chromosome strategy.

## Output Validation After An Approved Run

Check for:

- One `.vcf.gz` plus `.vcf.gz.tbi` per supplied sample.
- One `.g.vcf.gz` plus `.g.vcf.gz.tbi` per supplied sample when gVCF output was requested.
- VCF/gVCF header sample names matching intended child/parent identities.
- Sample-specific intermediates when `--intermediate_results_dir` was set.
- GLnexus merged VCF generated only from gVCFs with compatible reference, region policy, model family, and sample naming.
