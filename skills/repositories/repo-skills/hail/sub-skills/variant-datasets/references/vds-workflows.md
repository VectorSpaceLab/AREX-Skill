# VDS Workflows

This reference distills Hail `hail.vds` behavior into practical workflows for sparse sequencing data. It assumes Hail is installed and initialized appropriately for the user's compute environment.

## Component Semantics

A `VariantDataset` is a sparse sequencing representation with two component `MatrixTable`s.

| Component | Row key | Column key | Entry meaning | Use when |
| --- | --- | --- | --- | --- |
| `vds.reference_data` | `locus` | Same sample key/order as variant data | Reference blocks. A block starts at `locus` and ends at inclusive `END`, or has equivalent `LEN`. Genotypes are implicitly homozygous reference. | Coverage, reference-block metrics, VDS sample QC reference contribution, interval coverage. |
| `vds.variant_data` | `locus`, `alleles` | Same sample key/order as reference data | Sparse variant/non-reference rows. Entries typically use local allele fields (`LA`, `LGT`, `LAD`, `LPL`, `LPGT`) instead of global fields. | Variant-only filtering/QC, singleton or burden logic, split multiallelics, sparse allele-aware analysis. |

Important invariants:

- `VariantDataset(reference_data, variant_data)` validates component schema shape on construction. `vds.validate(check_data=True)` also checks column agreement, distinct reference loci, and reference block extent validity.
- `reference_data` must keep at least one of `END` or `LEN`. Hail can derive `LEN = END - locus.position + 1` or `END = locus.position + LEN - 1`.
- VDS writes component matrices under a VDS path. On disk Hail writes reference block length as `LEN`; `read_vds` normally restores `END` for in-memory workflows.
- Local allele fields mean a variant entry's genotype and arrays are indexed through `LA`, not directly through row `alleles`.

## Read, Inspect, and Checkpoint

```python
import hail as hl

hl.init()
vds = hl.vds.read_vds(input_vds)
vds.validate(check_data=True)
print(vds.n_samples())
vds.reference_data.describe()
vds.variant_data.describe()
```

Use `hl.vds.read_vds(path, intervals=intervals)` for interval-restricted reads. Use `n_partitions=` when you want Hail to compute partition intervals from reference data and read both components over matching intervals.

Write or checkpoint the wrapper when preserving VDS semantics:

```python
vds.write(output_vds, overwrite=True)
vds = vds.checkpoint(checkpoint_vds, overwrite=True)
```

If repeated interval filtering warns about missing reference block max length, patch metadata with `hl.vds.store_ref_block_max_length(vds_path)` or rewrite a transformed copy with `hl.vds.truncate_reference_blocks`.

## Choose a Representation

| Goal | Recommended representation | Reason |
| --- | --- | --- |
| Sample-level VDS QC | `hl.vds.sample_qc(vds)` | Combines sparse variant metrics and reference-block GQ/DP base-threshold metrics without densifying. |
| Interval/base coverage over calling intervals | `hl.vds.interval_coverage(vds, intervals_ht)` | Uses reference blocks directly and avoids expanding every sample at every variant row. |
| Variant-only QC, allele counts, singleton/burden logic | `vds.variant_data` | Sparse variant rows are enough; convert local calls only where global genotype semantics are required. |
| Reference block lengths, coverage windows, block metadata | `vds.reference_data` | Reference blocks are the ground-truth representation of reference coverage. |
| Dense-only MatrixTable method after heavy filtering | `hl.vds.to_dense_mt(vds)` | Fills reference-block entries at variant rows; expensive in variants times samples. |
| One sparse matrix containing variant and reference-block rows | `hl.vds.to_merged_sparse_mt(vds, ref_allele_function=...)` | Preserves sparsity while unifying both components. |
| Multi-sample GVCF ingestion or incremental VDS merge | `hl.vds.new_combiner(...).run()` | Produces restartable VDS outputs with local allele representation. |

## Filtering Recipes

### Samples

```python
vds = hl.vds.filter_samples(vds, ["sample_1", "sample_2"], keep=True)
```

For large lists, use a table keyed by one string field:

```python
samples_ht = hl.import_table(samples_tsv, key="s")
vds = hl.vds.filter_samples(
    vds,
    samples_ht,
    keep=True,
    remove_dead_alleles=True,
)
```

Use `remove_dead_alleles=True` after substantial sample filtering when you need row `alleles` and entry `LA` compacted to alleles still observed among retained samples. Leave it false when you need to preserve original allele indexing for compatibility with external annotations.

### Variants

```python
variants_ht = hl.read_table(variants_ht_path)  # keyed by locus, alleles
vds = hl.vds.filter_variants(vds, variants_ht, keep=True)
```

`filter_variants` only filters `variant_data`; reference blocks remain intact. Use this for targeted variant rows while preserving sparse reference information.

### Intervals

```python
intervals = hl.literal([
    hl.parse_locus_interval("chr20:1000000-2000000", reference_genome="GRCh38")
])
vds_region = hl.vds.filter_intervals(vds, intervals, keep=True)
```

For table input, key the table by a single `interval<locus<same reference>>` field. Default mode filters variant rows and keeps reference blocks that may overlap the intervals. If `ref_block_max_length` metadata is missing, reference filtering can require a full pass.

Use `split_reference_blocks=True` when output reference blocks must be trimmed exactly to kept intervals:

```python
intervals_ht = hl.Table.parallelize(
    [hl.struct(interval=hl.parse_locus_interval("chr20:1000000-2000000", reference_genome="GRCh38"))],
    key="interval",
)
vds_trimmed = hl.vds.filter_intervals(vds, intervals_ht, split_reference_blocks=True)
```

Split mode supports `keep=True` only and requires start-inclusive intervals that do not span contigs.

### Chromosomes

```python
vds_auto = hl.vds.filter_chromosomes(vds, keep_autosomes=True)
vds_chr20 = hl.vds.filter_chromosomes(vds, keep="chr20")
vds_no_mt = hl.vds.filter_chromosomes(vds, remove=["chrM"])
```

Pass exactly one of `keep`, `remove`, or `keep_autosomes`.

## Sample QC and Interval Coverage

### VDS Sample QC

```python
sqc = hl.vds.sample_qc(vds, gq_bins=(0, 20, 60), dp_bins=(0, 1, 10, 20, 30))
sqc.write(sample_qc_ht, overwrite=True)
```

`sample_qc` uses `DP` for depth if present in `reference_data`, otherwise `MIN_DP`, unless `dp_field=` is supplied. It converts `LGT` to `GT` for variant metrics when needed, computes allele counts and allele types on `variant_data`, computes GQ/DP base-threshold metrics on `reference_data`, and joins per-sample results.

Typical output includes heterozygote/homozygote counts, non-reference counts, singleton counts, allele type counts, `r_ti_tv`, `r_het_hom_var`, and GQ/DP threshold summaries.

### Interval Coverage

```python
intervals_ht = hl.import_locus_intervals(intervals_bed, reference_genome="GRCh38")
coverage_mt = hl.vds.interval_coverage(
    vds,
    intervals_ht,
    gq_thresholds=(0, 10, 20),
    dp_thresholds=(0, 1, 10, 20, 30),
)
coverage_mt.write(interval_coverage_mt, overwrite=True)
```

`interval_coverage` returns an interval-by-sample `MatrixTable` keyed by interval with row field `interval_size`. Entry fields include `bases_over_gq_threshold`, `fraction_over_gq_threshold`, and, when a depth field is usable, `bases_over_dp_threshold`, `fraction_over_dp_threshold`, `sum_dp`, and `mean_dp`.

Coverage is computed from reference blocks. Non-reference calls can interrupt reference blocks, so interval coverage may slightly underestimate true base coverage for samples with many non-reference records.

## Local Allele Workflows

VDS variant entries use local allele fields to avoid superlinear array growth at multiallelic sites.

- `LA`: local allele indexes into row `alleles`; the reference allele is usually index `0`.
- `LGT`: call where allele indexes refer to positions inside `LA`, not directly to row `alleles`.
- `LAD`, `LPL`, `LPGT`: local versions of `AD`, `PL`, and `PGT`.

Convert local calls only where global genotype semantics are required:

```python
vmt = vds.variant_data
vmt = vmt.annotate_entries(GT=hl.vds.lgt_to_gt(vmt.LGT, vmt.LA))
```

Convert local arrays to global indexing only for formats or APIs that require global `AD`/`PL` semantics:

```python
vmt = vmt.annotate_entries(
    AD=hl.vds.local_to_global(vmt.LAD, vmt.LA, hl.len(vmt.alleles), 0, number="R"),
    PL=hl.vds.local_to_global(vmt.LPL, vmt.LA, hl.len(vmt.alleles), 999, number="G"),
)
```

Avoid globalizing `LPL` at highly multiallelic rows unless required. `number="G"` arrays grow with genotype count.

## Split Multiallelics

```python
split_vds = hl.vds.split_multi(vds, filter_changed_loci=False)
```

`split_multi` applies sparse multiallelic splitting to `variant_data`. If `reference_data` has `LGT`, Hail converts it to `GT` unless `GT` is already present. Use `filter_changed_loci=True` when minimal representation would move a split allele's locus and you prefer dropping those changed-locus variants over raising an error.

## Dense and Merged Sparse Conversion

### Dense MatrixTable

```python
dense_mt = hl.vds.to_dense_mt(vds)
dense_mt = dense_mt.annotate_entries(GT=hl.vds.lgt_to_gt(dense_mt.LGT, dense_mt.LA))
```

`to_dense_mt` creates entries for every sample at each variant row by filling reference-block values where blocks overlap variant loci. Filter samples, intervals, and variants before densifying.

### Merged Sparse MatrixTable

```python
merged_sparse_mt = hl.vds.to_merged_sparse_mt(
    vds,
    ref_allele_function=lambda row: hl.missing("str"),
)
```

`to_merged_sparse_mt` combines variant rows and reference-block rows into one sparse `MatrixTable`. If reference-only rows need a reference allele, Hail uses row `ref_allele`, reference genome sequence context if attached, or a caller-provided `ref_allele_function`.

### Build a VDS from Merged Sparse Data

```python
vds = hl.vds.VariantDataset.from_merged_representation(
    merged_sparse_mt,
    ref_block_indicator_field="END",
    ref_block_fields=("GQ", "DP"),
    infer_ref_block_fields=True,
    is_split=False,
)
```

The merged representation must have `END` or `LEN`, `LGT` or `GT`, and `LA` unless already split. Reference-block entries must be homozygous reference.

## GVCF Combiner Workflows

Create a restartable plan with explicit partitioning:

```python
combiner = hl.vds.new_combiner(
    output_path=output_vds,
    temp_path=temp_dir,
    save_path=plan_json,
    gvcf_paths=gvcf_paths,
    reference_genome="GRCh38",
    use_genome_default_intervals=True,
    gvcf_reference_entry_fields_to_keep=["GQ", "DP", "MIN_DP"],
    gvcf_info_to_keep=["ExcessHet"],
    gvcf_save_filters=True,
    branch_factor=100,
    gvcf_batch_size=50,
)
combiner.run()
vds = hl.vds.read_vds(output_vds)
```

For exomes, prefer `use_exome_default_intervals=True`. For custom calling intervals, pass `intervals=[...]` typed with the same reference genome as `reference_genome`. Provide exactly one GVCF partitioning mode: `intervals`, `import_interval_size`, `use_genome_default_intervals`, or `use_exome_default_intervals`.

Resume intentionally from a saved plan:

```python
combiner = hl.vds.load_combiner(plan_json)
combiner.run()
```

Use `combiner.step()` only for controlled/debug execution. Use `force=True` with `new_combiner` only when intentionally discarding a saved plan and starting over.

## Combining Existing VDS Inputs

```python
combiner = hl.vds.new_combiner(
    output_path=output_vds,
    temp_path=temp_dir,
    save_path=plan_json,
    vds_paths=[cohort_a_vds, cohort_b_vds],
    vds_sample_counts=[1200, 800],
    reference_genome="GRCh38",
)
combiner.run()
```

When mixing GVCFs and existing VDS inputs, the existing VDS schema controls compatible reference entry fields, call fields, and whether `gvcf_filters` are preserved. If schema warnings appear, align the GVCF import options to the existing VDS or combine incompatible sets separately.

## Export Notes

`hl.vds.export_vcf(vds, output)` converts local allele fields for VCF output: `LA` becomes local alternate allele form, `LGT`/`LPGT` become `GT`/`PGT` when needed, and nested `gvcf_info` is dropped unless flattened first. For dense VCF-like workflows after conversion, route downstream dense `MatrixTable` method details to `../genomics-analysis/SKILL.md`.
