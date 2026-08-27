# DeepVariant Benchmarking and Metrics Interpretation

This reference helps agents interpret DeepVariant accuracy/runtime summaries and prepare safe benchmark handoffs. It does not replace user-approved hap.py execution, truth-set selection, or full benchmark protocol design.

## Benchmark Inputs and Outputs

| Artifact | Typical source | What it answers | Safety note |
| --- | --- | --- | --- |
| DeepVariant VCF/gVCF | Completed calling run | Calls to evaluate or summarize | Reading local outputs is safe; running the caller routes elsewhere. |
| Truth VCF and confident regions BED | User-provided truth set or GIAB-style benchmark inputs | Which loci count for accuracy | Must match sample, reference build, contig names, and evaluated regions. |
| hap.py `summary.csv` or `*.summary.csv` | User-run benchmark | Recall, precision, F1, TP/FP/FN by type/filter | Executing hap.py may require Docker, large data, and long runtime. |
| hap.py output VCFs | User-run benchmark | Locus-level FP/FN/TP categories | Useful input to `show_examples --vcf` after bounded filtering. |
| Runtime logs and TSVs | Wrapper run with logging | Stage timing and make_examples bottlenecks | Existing logs are safe to inspect; new run planning routes elsewhere. |
| Training `.metrics` files | Training/eval loop | Checkpoint-level TP/FN/FP and F1 trends | Training execution routes to the training sub-skill. |

## Release Metrics Context

DeepVariant 1.10 release metrics were generated on high-CPU cloud machines, not a generic laptop or default VM. Treat release numbers as context, not guarantees.

Record these conditions before comparing user metrics with release tables:

- DeepVariant version and image tag.
- Model type, including pangenome-aware versus standard models.
- Sample, truth set, confident regions, benchmark regions, and reference build.
- Read technology, assay, coverage, preprocessing, and region targeting.
- Machine type, CPU count, memory, storage speed, GPU use, container overhead, and shard count.
- Whether optional reporting, phasing, small-model, custom-model, or pangenome flags were enabled.

Do not compare WGS, WES, PacBio, ONT, RNA-seq, hybrid, MAS-Seq, pangenome-aware WGS, and pangenome-aware WES metrics as if they share identical expected accuracy or runtime. Each model type uses different assumptions and coverage in release summaries.

## hap.py Summary Interpretation

hap.py summaries commonly report separate rows for `SNP` and `INDEL`, often with a filter/subset column such as `PASS`. Important columns include:

| Column | Meaning | Interpretation |
| --- | --- | --- |
| `TRUTH.TOTAL` | Truth variants in the evaluated subset | Denominator for recall; changes with confident regions and filters. |
| `TRUTH.TP` | Truth variants matched by the query | True-positive support for recall. |
| `TRUTH.FN` | Truth variants missed by the query | Investigate with false-negative VCF slices and `show_examples` when examples exist. |
| `QUERY.TOTAL` | Query variants evaluated | Denominator context for precision. |
| `QUERY.FP` | Query variants not matched to truth | Investigate with false-positive VCF slices and `show_examples`. |
| `Recall` | `TRUTH.TP / TRUTH.TOTAL` | Sensitive to truth/confident-region compatibility. |
| `Precision` | Matched query calls over evaluated query calls | Sensitive to filters, normalization, and representation. |
| `F1_Score` | Harmonic mean of precision and recall | Useful headline metric, but it can hide SNP/INDEL or region-specific issues. |

Use PASS-only rows for headline DeepVariant call accuracy when the benchmark output distinguishes PASS from filtered calls. If a user compares all-filter rows with PASS-only rows, explain that filtered, non-PASS, and RefCall records can change counts and should not be mixed without a clear reason.

## False Positive and False Negative Review

A safe visual-review handoff usually follows this sequence:

1. Confirm the user already has a completed DeepVariant run and preserved `make_examples` intermediates.
2. Obtain hap.py output VCF slices for FP or FN loci, or help the user prepare bounded slices in an approved benchmark workspace.
3. Use `show_examples --vcf` with the FP/FN VCF slice plus `--num_records`, `--regions`, or `--max_examples_to_scan`.
4. Write outputs to a dedicated empty prefix so PNGs and curation TSVs do not mix with prior reviews.
5. Record whether examples came from calling mode or training mode, because training examples may include truth labels in image filenames.

Preview:

```bash
docker run \
  -v /host/output:/output \
  google/deepvariant:1.10.0 \
  /opt/deepvariant/bin/show_examples \
  --examples=/output/intermediate_results_dir/make_examples.tfrecord@64.gz \
  --example_info_json=/output/intermediate_results_dir/example_info.json \
  --vcf=/output/benchmark/false_positives.vcf.gz \
  --regions='chr20:10000000-10100000' \
  --output=/output/review/fp \
  --num_records=25 \
  --max_examples_to_scan=100000 \
  --image_type=channels \
  --curate
```

If no matching images are produced, check coordinate conventions, contig names, VCF normalization, malformed headerless VCF rows, examples coverage, and whether examples were generated from the same reference/read inputs as the benchmarked VCF.

## Runtime Metrics Interpretation

Use runtime metrics at two levels:

- **Stage-level runtime** from wrapper logs: identifies whether `make_examples`, `call_variants`, `postprocess_variants`, or `vcf_stats` dominates wall-clock time.
- **Region-level runtime** from `runtime_by_region_vis`: identifies pathological regions or shard imbalance within `make_examples`.

Common conclusions:

- Long `get reads` time points toward storage, CRAM/reference decoding, index locality, region locality, or high read density.
- Long `find candidates` time points toward noisy data, dense candidate regions, model-type thresholds, or complex loci.
- Long `make pileup images` time points toward high candidate/example counts, alt-aligned pileups, local assembly complexity, or dense alignments.
- Long `write outputs` time points toward many examples, slow output storage, compression overhead, or sharding layout.
- A few extreme regions with steep Pareto curves justify targeted region inspection before changing global resources.
- Uniformly slow shards usually suggest infrastructure, global flags, or resource issues rather than individual loci.

## Pangenome-Aware Metrics

Pangenome-aware DeepVariant metrics should be interpreted separately from standard DeepVariant metrics. Record GBZ/pangenome inputs, mapping strategy, pangenome reference sample naming, and whether the run used WGS-pangenome or WES-pangenome models.

When comparing pangenome-aware and standard runs:

- Keep sample, truth set, confident regions, benchmark regions, reference build, and hap.py options as similar as possible.
- Distinguish runtime increases due to graph/pangenome setup from ordinary `make_examples` bottlenecks.
- Separate WGS-pangenome and WES-pangenome expectations; they differ in target regions and coverage assumptions.
- Route pangenome command planning and GBZ/runtime troubleshooting to the pangenome-aware calling sub-skill; keep this sub-skill focused on report and metric interpretation.

## Checkpoint Metric Summaries

DeepVariant includes a small `print_f1`-style parser for training/evaluation `.metrics` JSON files. Its behavior can be distilled as:

1. Read regular files in a metrics directory.
2. Parse JSON metrics.
3. Extract checkpoint numbers from filenames matching `ckpt-<number>.metrics`.
4. Normalize metric keys by replacing `/` with `_`.
5. Compute `F1_All = 2 * TPs_All / (2 * TPs_All + FNs_All + FPs_All)`.
6. Print tab-separated `checkpoint`, `TPs_All + FNs_All`, and `F1_All`.

Use this interpretation for checkpoint-selection discussions. Route model training, evaluation runs, and metric-file production to the training sub-skill.

Parser-only smoke check idea for verification artifacts: create a temporary metrics directory with one tiny `ckpt-1.metrics` JSON containing `TPs/All`, `FNs/All`, and `FPs/All`, then confirm the computed F1 equals the expected harmonic formula. Keep that test artifact outside the runtime skill tree.

## Safe Benchmark Handoff

Before proposing hap.py execution, collect:

- Query VCF and index.
- Truth VCF and index.
- Confident regions BED and index when required.
- Reference FASTA and `.fai`, with build compatibility confirmed.
- Sample name, contig naming, regions/subsets, and hap.py stratification choices.
- hap.py container or binary availability.
- Output directory with enough space.
- User approval for Docker/network/long-running execution.

Recommended handoff phrasing:

```text
I can prepare a hap.py command preview, but executing it requires your approved benchmark environment, truth inputs, and runtime budget. The output summary can then be interpreted here, and selected FP/FN rows can be visualized with show_examples if DeepVariant intermediates were preserved.
```

Do not silently download truth sets, pull hap.py images, run cloud scripts, or infer that release-case-study commands are safe for a user's local machine.
