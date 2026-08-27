# DeepVariant Reports and Visualization

This reference helps agents plan and interpret DeepVariant post-run reports without depending on the source checkout. Commands are previews until the user confirms a compatible DeepVariant runtime, data mounts, output location, and runtime budget.

## Artifact Map

| User goal | Required input | Tool or flag | Primary output | Notes |
| --- | --- | --- | --- | --- |
| Add a VCF summary to a new run | Planned DeepVariant wrapper run | `run_deepvariant --vcf_stats_report=true` | `<output_vcf_base>.visual_report.html` | Route actual run planning to a calling sub-skill. |
| Summarize an existing VCF | Single-sample VCF, usually `.vcf.gz` plus `.tbi` | `vcf_stats_report --input_vcf --outfile_base --title` | `<outfile_base>.visual_report.html` | Requires exactly one sample and a `GT` FORMAT field. |
| Create runtime TSVs during a new run | Planned wrapper run with logging | `run_deepvariant --runtime_report=true --logging_dir=...` | Runtime TSV shard(s) plus HTML report under `logging_dir` | `--runtime_report` works only with `--logging_dir`. |
| Visualize existing runtime TSVs | One runtime TSV or sharded TSV spec | `runtime_by_region_vis --input --output --title` | HTML runtime report | The tool appends `.html` if `--output` does not already end in `html`. |
| Inspect examples visually | `make_examples` TFRecord, preferably with `example_info.json` | `show_examples --examples --output ...` | PNG files, optional curation TSV, optional filtered TFRecords | Use filters and limits to avoid huge output directories. |
| Translate notebook exploration | Existing examples TFRecord | `show_examples` or a small bounded script | PNGs or selected example metadata | Prefer the command-line tool for repeatable workflows. |

## VCF Stats Report

DeepVariant can create an HTML visual report from a VCF. For a new run, enable the wrapper flag `--vcf_stats_report=true`. For an existing VCF, plan a direct report-binary invocation.

Preview command:

```bash
docker run \
  -v /host/output:/output \
  google/deepvariant:1.10.0 \
  /opt/deepvariant/bin/vcf_stats_report \
  --input_vcf=/output/sample.vcf.gz \
  --outfile_base=/output/sample \
  --title='HG002 WGS DeepVariant report'
```

Expected output:

```text
/output/sample.visual_report.html
```

Pre-flight checks:

- The VCF path must be visible inside the runtime container or binary environment.
- A bgzipped VCF should have a colocated `<vcf>.tbi` index for reliable downstream tooling and mounted-runtime access.
- The VCF must contain exactly one sample; split or select a sample before reporting on a cohort VCF.
- The VCF must include `GT` in the FORMAT header; the report fails early when genotype information is absent.
- `--outfile_base` is a base path, not the final HTML filename. If it ends in `.html`, DeepVariant still appends `.visual_report.html`.
- `--num_records` can be useful for smoke checks, but full report interpretation should use the complete VCF.

Interpretation checklist:

- **Variant types**: Counts distinguish SNPs, insertions, deletions, MNPs, multiallelic categories, and RefCalls. Failed or reference-like records are not equivalent to PASS variants.
- **Depth (`DP`)**: The depth histogram uses the `DP` FORMAT field and ignores entries without `DP`. Multi-modal or low-depth patterns may reflect assay design, region filtering, downsampling, copy number, or mapping difficulty.
- **Quality (`QUAL`) and genotype quality (`GQ`)**: High `QUAL` can coexist with low `GQ` when the model is confident that variation exists but uncertain about zygosity.
- **Variant allele frequency (`VAF`)**: Heterozygous calls often cluster near 0.5 and homozygous alternate calls near 1.0, but assay, mapping, copy number, mosaicism, and filtering can shift distributions.
- **Base changes and Ti/Tv**: Treat Ti/Tv as a broad sanity signal only. Expected ranges vary by genome region, assay, truth set, and filters.
- **Indel size distribution**: Watch for unexpected long-tail patterns or asymmetric insertions/deletions, but confirm with benchmark or targeted review before drawing conclusions.

## Runtime-by-Region Report

`make_examples` can emit a TSV row per region with timings for `get reads`, `find candidates`, `make pileup images`, and `write outputs`, plus counts such as `num reads`, `num candidates`, and `num examples`. DeepVariant 1.10 runtime reports can also include small-model timing columns when those paths are active.

Wrapper-created runtime artifacts commonly look like:

```text
<logging_dir>/make_examples_runtime_by_region/make_examples_runtime-00000-of-00001.tsv
<logging_dir>/make_examples_runtime_by_region/make_examples_runtime@64.tsv
<logging_dir>/make_examples_runtime_by_region_report.html
```

Standalone visualization preview:

```bash
docker run \
  -v /host/output:/output \
  google/deepvariant:1.10.0 \
  /opt/deepvariant/bin/runtime_by_region_vis \
  --input=/output/logs/make_examples_runtime_by_region/make_examples_runtime@64.tsv \
  --output=/output/logs/make_examples_runtime_by_region_report.html \
  --title='HG002 WGS make_examples runtime'
```

Required TSV columns for standard interpretation:

```text
region	get reads	find candidates	make pileup images	write outputs	num reads	num candidates	num examples
```

Chart interpretation:

- **Overall runtime by stage** shows whether time concentrates in read fetching, candidate finding, pileup generation, output writing, or small-model work.
- **Pareto curve for each task** shows whether a small fraction of regions dominates a task's runtime.
- **Total runtime for each task** highlights shard imbalance; long shards often pair with steep Pareto curves.
- **Stage runtimes for each task** separates task-level distribution by stage and often exposes pileup-generation variability.
- **Top runtime regions and median runtime regions** compare pathological loci with normal workload regions.
- **Longest-running zero-example regions** identifies time spent on regions that produced no examples; this can point to read retrieval, local assembly, filtering, or dense reference contexts.
- **Trend grids** correlate read/candidate/example counts with stage timings to choose between data-density, region-selection, model-setting, or infrastructure investigations.

## show_examples Pileup Visualization

`show_examples` reads `make_examples` TFRecords and writes human-readable pileup PNGs. It is useful for inspecting candidate variants, benchmark false positives/false negatives, curation concepts, and channel issues. The tool was introduced in DeepVariant 1.0.0 and works with older examples if metadata is compatible.

To make examples available for later review, a calling workflow should preserve intermediates in a mounted location using `--intermediate_results_dir`. If a completed run did not preserve examples, this sub-skill should not rerun the caller; route rerun planning to the appropriate workflow sub-skill.

Preview command:

```bash
docker run \
  -v /host/output:/output \
  google/deepvariant:1.10.0 \
  /opt/deepvariant/bin/show_examples \
  --examples=/output/intermediate_results_dir/make_examples.tfrecord-00000-of-00001.gz \
  --example_info_json=/output/intermediate_results_dir/make_examples.tfrecord-00000-of-00001.gz.example_info.json \
  --output=/output/pileup/review \
  --num_records=20 \
  --image_type=channels \
  --curate
```

Important output behavior:

- `--output` is a filename prefix. A prefix like `/output/pileup/review` produces files such as `/output/pileup/review_chr20:10004146_A->G.png`.
- The tool internally appends an underscore to the prefix before locus IDs.
- `--image_type=both` writes two PNGs per selected example: channel rows and RGB composites.
- `--curate` writes a `<prefix>_curation.tsv` table of concept tags that can be filtered and reused with `--filter_by_tsv`.
- `--write_tfrecords` writes filtered TFRecords and should be treated as data generation, not just visualization.
- Training examples may include truth labels in filenames unless `--notruth_labels` is used; calling examples normally do not include labels.

Useful filters and bounds:

- `--regions 'chr20:10000000-10100000'` for region literals, BED files, or BEDPE files.
- `--vcf false_positives.vcf.gz` for a full or headerless VCF slice; the first four VCF columns must still be valid enough to identify chrom, position, and reference bases.
- `--num_records 20` to limit output after filters.
- `--max_examples_to_scan 50000` to bound total scanning work.
- `--image_type none --curate` to collect curation tags without PNG output.
- `--filter_by_tsv curated_subset.tsv` to rerun visualization on selected curation IDs.
- `--column_labels` only when an explicit or auto-discovered `example_info_json` is not used; the label count must match the example channel count.

## Notebook-to-Script Translation

The visualizing-examples notebook demonstrates the same conceptual flow as `show_examples`: read gzipped TFRecords, parse TensorFlow examples, extract variants/locus IDs/labels, and draw pileup images. For repeatable agent work:

1. Prefer `show_examples` when the goal is PNG generation, VCF/region/TSV filtering, curation TSVs, or filtered TFRecords.
2. Write a small custom script only when the user needs metadata extraction not exposed by `show_examples`, and keep it bounded to a small number of records.
3. Replace interactive notebook assumptions with explicit local paths, output prefixes, record limits, and user-approved network access when remote data is required.
4. Use `example_info_json` for channel labels when available; otherwise validate labels against channel count.
5. Stream examples and stop early; do not materialize full sharded TFRecords in memory.

## Safe Command Builder

The bundled helper prints command previews and warnings without executing them:

```bash
python scripts/report_command_builder.py vcf-stats \
  --input-vcf /host/output/sample.vcf.gz \
  --outfile-base /host/output/sample \
  --title 'Sample report'

python scripts/report_command_builder.py runtime \
  --runtime-tsv /host/output/logs/make_examples_runtime_by_region/make_examples_runtime@64.tsv \
  --output-html /host/output/logs/make_examples_runtime_by_region_report.html \
  --title 'Runtime report'

python scripts/report_command_builder.py show-examples \
  --examples /host/output/intermediate_results_dir/make_examples.tfrecord@64.gz \
  --output-prefix /host/output/pileup/review \
  --vcf /host/output/happy_false_positives.vcf.gz \
  --num-records 20 \
  --max-examples-to-scan 50000
```

Use the helper before proposing container execution, especially when paths cross host/container boundaries or the request could generate many files.
