# VDS API Reference

This is a compact reference for `hail.vds` APIs most relevant to sparse `VariantDataset` workflows. Signatures reflect the inspected installed Hail package where available.

## Core Object

| API | Signature / fields | Notes |
| --- | --- | --- |
| `hl.vds.VariantDataset` | `VariantDataset(reference_data, variant_data)` | Constructs a VDS from two component `MatrixTable`s. `reference_data` is keyed by `locus`; `variant_data` is keyed by `locus, alleles`; both components must have compatible sample columns. |
| `vds.reference_data` | `MatrixTable` | Sparse reference blocks with `END` or `LEN`. No row `alleles` key. |
| `vds.variant_data` | `MatrixTable` | Sparse variant/non-reference data keyed by `locus, alleles`; entries commonly contain `LA`, `LGT`, `LAD`, `LPL`, and `LPGT`. |
| `vds.write(path, **kwargs)` | Writes VDS directory | Accepts `MatrixTable.write` keyword options such as `overwrite=True`; writes component matrices below the VDS path. |
| `vds.checkpoint(path, **kwargs)` | Returns reread `VariantDataset` | Useful after expensive transformations. |
| `vds.n_samples()` | Returns `int` | Counts columns in `reference_data`. |
| `vds.reference_genome` | Property | Reference genome from the component locus type. |
| `vds.validate(check_data=True)` | Raises on invalid representation | With `check_data=True`, eagerly checks component column agreement and reference block validity. |
| `hl.vds.VariantDataset.from_merged_representation` | `from_merged_representation(mt, *, ref_block_indicator_field="END", ref_block_fields=(), infer_ref_block_fields=True, is_split=False)` | Builds a VDS from one sparse merged `MatrixTable`. Requires `END` or `LEN`, `LGT` or `GT`, and `LA` unless already split. Reference-block entries must be hom-ref. |
| `hl.vds.VariantDataset.union_rows` | `union_rows(*vdses)` | Combines VDSes with same samples and disjoint row regions; max reference block metadata is preserved only when all inputs provide it. |

## Reading and Metadata

| API | Signature | Notes |
| --- | --- | --- |
| `hl.vds.read_vds` | `read_vds(path, *, intervals=None, n_partitions=None, _assert_reference_type=None, _assert_variant_type=None, _warn_no_ref_block_max_length=True, _drop_end=False)` | Public usage is normally `hl.vds.read_vds(path, intervals=..., n_partitions=...)`. Reads both component matrices and returns `VariantDataset`. |
| `hl.vds.store_ref_block_max_length` | `store_ref_block_max_length(vds_path)` | Patches existing VDS metadata with max reference block length, enabling faster interval filtering without rewriting all component data. |
| `hl.vds.read_dense_mt` | `read_dense_mt(path)` | Reads a VDS path directly as a dense `MatrixTable`; requires `ref_block_max_length` metadata. Use sparingly. |

## Filtering and Reshaping

| API | Signature | Notes |
| --- | --- | --- |
| `hl.vds.filter_samples` | `filter_samples(vds, samples, *, keep=True, remove_dead_alleles=False)` | `samples` is a table keyed by one string field or an array/list of sample strings. Filters both components. `remove_dead_alleles=True` recomputes `LA` and row `alleles` after removing samples. |
| `hl.vds.filter_variants` | `filter_variants(vds, variants_table, *, keep=True)` | Filters only `variant_data` rows by a keyed variants table; preserves reference data. |
| `hl.vds.filter_intervals` | `filter_intervals(vds, intervals, *, split_reference_blocks=False, keep=True)` | `intervals` is a table keyed by one `interval<locus>` field or an array expression of intervals. Split mode trims reference blocks and supports `keep=True` only. |
| `hl.vds.filter_chromosomes` | `filter_chromosomes(vds, *, keep=None, remove=None, keep_autosomes=False)` | Pass exactly one selector. Uses reference genome contig metadata and interval filtering. |
| `hl.vds.split_multi` | `split_multi(vds, *, filter_changed_loci=False)` | Splits multiallelic `variant_data` with sparse semantics; may convert reference-data `LGT` to `GT`. |
| `hl.vds.truncate_reference_blocks` | `truncate_reference_blocks(ds, *, max_ref_block_base_pairs=None, ref_block_winsorize_fraction=None)` | Caps long reference blocks on a VDS or reference `MatrixTable` and stores max reference block length metadata. |
| `hl.vds.merge_reference_blocks` | `merge_reference_blocks(ds, equivalence_function, merge_functions=None)` | Merges adjacent equivalent reference blocks; useful after transformations that fragment blocks. |
| `hl.vds.segment_reference_blocks` | `segment_reference_blocks(ref, intervals)` | Lower-level helper for interval coverage and split interval filtering; intervals must be start-inclusive and not span contigs. |
| `hl.vds.write_variant_datasets` | `write_variant_datasets(vdss, paths, *, overwrite=False, stage_locally=False, codec_spec=None)` | Writes many VDSes efficiently; advanced/internal batch-oriented helper. |

## QC and Coverage

| API | Signature | Returns | Notes |
| --- | --- | --- | --- |
| `hl.vds.sample_qc` | `sample_qc(vds, *, gq_bins=(0,20,60), dp_bins=(0,1,10,20,30), dp_field=None)` | Sample-keyed `Table` | Combines sparse variant metrics with reference-block GQ/DP base metrics. Uses `DP`, then `MIN_DP`, unless `dp_field` is set. |
| `hl.vds.interval_coverage` | `interval_coverage(vds, intervals, gq_thresholds=(0,10,20), dp_thresholds=(0,1,10,20,30), dp_field=None)` | Interval-by-sample `MatrixTable` | Computes base coverage from reference blocks. Intervals table must be keyed by intervals. |
| `hl.vds.impute_sex_chromosome_ploidy` | `impute_sex_chromosome_ploidy(vds, calling_intervals, normalization_contig, use_variant_dataset=False)` | Sample-keyed `Table` | Uses interval coverage by default; removes PAR intervals; requires one X and one Y contig in the reference genome. |
| `hl.vds.impute_sex_chr_ploidy_from_interval_coverage` | `impute_sex_chr_ploidy_from_interval_coverage(mt, normalization_contig)` | Sample-keyed `Table` | Consumes interval coverage matrix with `interval`, `interval_size`, and `sum_dp`. |

## Representation Conversion

| API | Signature | Notes |
| --- | --- | --- |
| `hl.vds.to_dense_mt` | `to_dense_mt(vds)` | Produces a dense `MatrixTable` at variant rows. Fills reference block entries where blocks overlap variant loci. Potentially expensive. |
| `hl.vds.to_merged_sparse_mt` | `to_merged_sparse_mt(vds, *, ref_allele_function=None)` | Produces one sparse `MatrixTable` with variant and reference-block rows. Requires a way to fill reference allele for reference-only loci. |
| `hl.vds.lgt_to_gt` | `lgt_to_gt(lgt, la)` | Converts a local call to global allele indexing by looking up alleles through `LA`; hom-ref calls are preserved even if `LA` is missing. |
| `hl.vds.local_to_global` | `local_to_global(array, local_alleles, n_alleles, fill_value, number)` | Reindexes local arrays to global allele indexing for VCF-style `Number=A`, `Number=R`, or `Number=G` arrays. Can explode data size for `number="G"`. |

## Import and Export

| API | Notes |
| --- | --- |
| `hl.vds.import_vcf` | Imports SVCR/VCF-like data into VDS representation. Prefer the combiner for multiple GVCFs or restartable production combines. |
| `hl.vds.export_vcf` | Exports a VDS as VCF-like output. Converts local fields for output and drops nested `gvcf_info` unless flattened onto entries first. |

## Combiner APIs

| API | Signature / key arguments | Notes |
| --- | --- | --- |
| `hl.vds.new_combiner` | `new_combiner(*, output_path, temp_path, save_path=None, gvcf_paths=None, vds_paths=None, vds_sample_counts=None, intervals=None, import_interval_size=None, use_genome_default_intervals=False, use_exome_default_intervals=False, gvcf_external_header=None, gvcf_sample_names=None, gvcf_info_to_keep=None, gvcf_reference_entry_fields_to_keep=None, gvcf_save_filters=False, call_fields=['PGT'], branch_factor=100, target_records=24000, gvcf_batch_size=None, batch_size=None, reference_genome='default', contig_recoding=None, force=False)` | Builds or resumes a restartable `VariantDatasetCombiner`. For GVCF inputs, provide exactly one partitioning mode. `batch_size` is deprecated; use `gvcf_batch_size`. |
| `hl.vds.load_combiner` | `load_combiner(path)` | Loads a saved combiner plan. If the plan moved, Hail updates `save_path` to the loaded path. |
| `combiner.run()` | No args | Repeatedly saves plan state and executes combine steps until finished. |
| `combiner.step()` | No args | Runs one merge layer; useful for controlled/debug execution. |
| `combiner.save()` | No args | Serializes current plan state. |
| `combiner.finished` | Boolean property | True when all GVCFs and VDS inputs have been consumed. |
| `combiner.gvcf_batch_size` | Property | Setter caps too-large task counts relative to interval count. |

## Field Semantics

| Field | Location | Meaning |
| --- | --- | --- |
| `END` | `reference_data` entry | Inclusive ending position of a reference block. A block covers `locus.position` through `END`. |
| `LEN` | `reference_data` entry | Block length in base pairs; equivalent to `END - locus.position + 1`. Hail may store `LEN` on disk and add `END` on read. |
| `ref_block_max_length` | `reference_data` global | Maximum reference block length. Enables interval filters to avoid scanning all reference blocks. |
| `LA` | `variant_data` entry | Local allele indexes into row `alleles`. Local call/array fields use indexes into `LA`, not directly into `alleles`. |
| `LGT` | Variant entries and sometimes reference entries | Local genotype call. Use `hl.vds.lgt_to_gt(LGT, LA)` for global call indexing. |
| `LAD` | `variant_data` entry | Local allele depth, VCF `AD` in local allele order. Use `local_to_global(..., number="R")` only when global indexing is needed. |
| `LPL` | `variant_data` entry | Local genotype likelihood, VCF `PL` in local genotype order. Globalizing with `number="G"` can become extremely large. |
| `LPGT` | `variant_data` entry | Local phased genotype field corresponding to `PGT`. |
| `gvcf_info` | `variant_data` entry | Struct of selected GVCF `INFO` fields preserved by combiner/import. Flatten before VCF export if values must be retained. |
| `gvcf_filters` | Both components if enabled | Preserved input GVCF filter set when `gvcf_save_filters=True`; must be present consistently in mixed VDS/GVCF combines. |
| `GQ`, `DP`, `MIN_DP` | Component entries when present | Used by sample QC and interval coverage. `DP` is preferred over `MIN_DP` unless `dp_field` is set. |

## Native Verification Notes

Repository-native VDS tests cover validation, sample QC equivalence, interval coverage, local allele conversion, dense conversion, split multiallelics, reference block max length metadata, combiner plan serialization, and GVCF combining. Treat those checks as backend-dependent; mark them `skip-backend` when Hail backend startup is unavailable and `skip-expensive` for full combiner execution paths.
