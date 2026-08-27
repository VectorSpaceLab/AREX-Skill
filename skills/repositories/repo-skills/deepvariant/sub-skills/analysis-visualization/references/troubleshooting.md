# Analysis and Visualization Troubleshooting

Use this matrix for DeepVariant report-generation and benchmark-interpretation failures. If the fix requires rerunning variant calling, route planning to the relevant calling or pipeline-stage sub-skill instead of executing a new run from this sub-skill.

## VCF Stats Report

| Symptom | Likely cause | Checks | Recovery |
| --- | --- | --- | --- |
| `vcf_stats_report` cannot open the VCF | Host/container path mismatch or missing local file | Confirm the host file exists and the command uses the in-runtime path. | Regenerate a preview with `report_command_builder.py` and correct the bind mount or path. |
| Missing `.tbi` or random-access errors | VCF is bgzipped but not indexed, or is plain gzip | Check for `<vcf>.tbi` and confirm block gzip format. | Use a user-approved tabix/bgzip environment, or use the indexed VCF from DeepVariant postprocessing. |
| `There must be exactly one sample in VCF` | Multi-sample VCF supplied | Inspect VCF header sample columns. | Split/select one sample before running `vcf_stats_report`; do not use a cohort VCF directly. |
| `No GT sub-column in VCF` | FORMAT header lacks genotype (`GT`) | Inspect the VCF FORMAT header. | Use a DeepVariant output VCF with genotype calls or regenerate a compatible single-sample VCF. |
| Output filename is surprising | `--outfile_base` is a base, not the final HTML path | Remember DeepVariant appends `.visual_report.html`. | Set `--outfile_base=/output/sample` when you want `/output/sample.visual_report.html`. |
| Report seems to include reference or filtered calls | Charts use all relevant VCF records with per-chart variant/refcall logic | Check FILTER, GT, and chart definitions. | Explain that VCF stats are not a PASS-only benchmark; use hap.py PASS rows for headline accuracy. |

## Runtime-by-Region Report

| Symptom | Likely cause | Checks | Recovery |
| --- | --- | --- | --- |
| `--runtime_report` produced no report | `--logging_dir` was omitted, not writable, or not mounted | Check wrapper flags and logs. | Rerun planning must include both `--runtime_report=true` and a writable `--logging_dir`. |
| TSV shard path not found | Sharded spec and expanded filenames confused | For `make_examples_runtime@64.tsv`, expect `make_examples_runtime-00000-of-00064.tsv` through `-00063-of-00064.tsv`. | Pass the sharded spec when all shards exist, or pass one expanded TSV for a single-shard report. |
| HTML output has an extra `.html` | `runtime_by_region_vis --output` appends `.html` when the value does not end in `html` | Inspect the previewed `--output` value. | Use a final filename ending in `.html` for exact naming. |
| Report has missing small-model charts or columns | TSV came from a version/config without small-model timing columns | Inspect the TSV header. | Interpret available columns only; do not infer that small-model work ran. |
| HTML generation is slow or huge | Many regions/shards and embedded chart data | Check TSV size, row count, and shard count. | Generate the report in a suitable environment or use region-scoped profiling for investigation. |
| Pareto curve shows one shard dominates | Load imbalance or localized expensive regions | Compare task runtime chart and top-region chart. | Investigate top regions, read density, candidate counts, storage, and flags before changing global resources. |
| Long zero-example regions dominate | Regions consume read/candidate/pileup work but emit no examples | Review zero-example chart and TSV rows for stage timing. | Inspect region complexity, mapping density, filters, and reference/target design before scaling resources. |

## show_examples

| Symptom | Likely cause | Checks | Recovery |
| --- | --- | --- | --- |
| Examples TFRecord is missing | The run did not preserve intermediates outside the runtime | Check whether `--intermediate_results_dir` was set in the original run. | Future run planning should include a mounted `--intermediate_results_dir`; current review may require a rerun routed elsewhere. |
| `example_info_json` not found | Auto-discovery cannot find `*example_info.json` near the examples path | List files next to the TFRecord. | Pass `--example_info_json` explicitly, or use `--column_labels` with exactly the right channel count. |
| `--column_labels must have ...` error | Label count does not match example channel count | Count channel names and compare to example metadata. | Use `example_info_json` when available; otherwise provide one label per channel. |
| No images are produced | Filters are too restrictive or coordinates do not match examples | Check `--regions`, `--vcf`, contig naming, VCF normalization, and scan limits. | Start with a known-covered region, increase `--max_examples_to_scan`, or remove one filter at a time. |
| Output directory fills with PNGs | `--num_records` missing, sharded examples scanned broadly, or `--image_type=both` doubles output | Check command flags and output prefix. | Use a dedicated prefix, add `--num_records`, add `--max_examples_to_scan`, and prefer `--image_type=channels` or `none` for curation-only passes. |
| Files appear in a parent directory instead of a folder | `--output` is a filename prefix | Inspect generated filenames. | Use a prefix such as `/output/pileup/review` after ensuring `/output/pileup` exists; expect `review_chr...png` filenames. |
| Headerless hap.py VCF slice does not match examples | Columns are malformed, positions are not normalized, contigs differ, or references differ | Check the first four VCF columns and contig names. | Keep valid VCF-like rows with chrom, pos, ID, REF, ALT; normalize and match reference/contig naming. |
| Huge sharded examples scan takes too long | Broad `make_examples.tfrecord@N.gz` input without filters | Check shard count and filters. | Add `--regions`, `--vcf`, `--filter_by_tsv`, `--num_records`, or `--max_examples_to_scan`. |
| GCS examples appear empty | Remote path missing, permission issue, or sharded spec expands to empty shards | Verify only with user-approved cloud tools. | Ask the user to stage data locally or approve cloud access; do not silently run network commands. |

## Benchmark Interpretation

| Symptom | Likely cause | Checks | Recovery |
| --- | --- | --- | --- |
| F1 differs from release metrics | Different version, sample, truth set, regions, coverage, hardware, model type, or flags | Record all benchmark conditions. | Compare only like-for-like settings and present release metrics as context. |
| PASS-only and all-filter rows disagree | One row includes filtered/non-PASS calls and another does not | Check hap.py filter/subset columns. | Use PASS rows for headline call accuracy when appropriate and explain the denominator difference. |
| SNP looks strong but INDEL looks weak, or vice versa | Technology, model, truth representation, or normalization differences | Compare SNP and INDEL rows separately. | Investigate variant-class-specific FP/FN loci with `show_examples` when examples exist. |
| Query/Truth totals are unexpectedly small | Confident regions, target BED, contig names, sample, or reference build mismatch | Check input headers, sample names, and hap.py region arguments. | Fix benchmark inputs before interpreting precision/recall. |
| Runtime comparison is misleading | Hardware, storage, shard count, report flags, or container overhead differs | Compare stage logs and runtime TSVs. | Normalize conditions or report caveats clearly. |
| Pangenome-aware comparison is confusing | Standard and pangenome-aware runs use different graph inputs and model assumptions | Record GBZ/pangenome inputs, mapping strategy, model preset, and regions. | Interpret pangenome-aware metrics separately and route command/runtime setup elsewhere. |

## Notebook-to-Script Translation

| Symptom | Likely cause | Checks | Recovery |
| --- | --- | --- | --- |
| Notebook code depends on Colab, shell magics, or remote downloads | Interactive setup assumptions | Identify `!`, `%`, display-only cells, and cloud paths. | Translate to `show_examples` or a small bounded script; ask before network downloads. |
| Script reads too many examples into memory | Exploratory notebook iteration was copied without bounds | Inspect loops and dataset transformations. | Stream examples, stop after a small limit, and avoid materializing full TFRecords. |
| Images lack channel labels | Missing `example_info_json` or labels | Check for example metadata. | Pass `--example_info_json` or validated `--column_labels`. |
| Script fails outside full DeepVariant runtime | TensorFlow/Nucleus/compiled genomics dependencies are missing | Check import errors and runtime environment. | Prefer containerized `show_examples` or ask the user for an approved full DeepVariant environment. |

## Safe Recovery Defaults

When unsure, propose a non-executing preview and a small bounded smoke command:

```bash
python scripts/report_command_builder.py show-examples \
  --examples /host/output/intermediate_results_dir/make_examples.tfrecord-00000-of-00001.gz \
  --output-prefix /host/output/pileup/smoke \
  --num-records 5 \
  --max-examples-to-scan 10000
```

Ask the user before running any container, Bazel binary, hap.py benchmark, network download, GPU job, or command that can create many files.
