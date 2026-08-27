# VDS Troubleshooting

Use this guide when sparse VDS behavior surprises a workflow or when GVCF combining fails. Route ordinary dense `MatrixTable` problems to `../genomics-analysis/SKILL.md` unless the root cause is VDS representation conversion.

## Dense vs Sparse Misuse

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Code expects `vds.row`, `vds.entry`, `vds.GT`, or `vds.cols()` like a `MatrixTable`. | `VariantDataset` is a wrapper around `reference_data` and `variant_data`. | Choose `vds.variant_data`, `vds.reference_data`, `hl.vds.to_dense_mt(vds)`, or `hl.vds.to_merged_sparse_mt(vds)` deliberately. |
| Variant-only analysis is extremely slow or out of memory. | The workflow densified with `to_dense_mt` before filtering. | Filter samples/intervals/variants first, or use `vds.variant_data` directly. Densify only for dense-only methods. |
| Coverage metrics miss some bases at non-reference calls. | `interval_coverage` computes from reference blocks; variant rows can interrupt blocks. | Document the slight underestimate, or build a custom workflow that also adds variant-entry depth when exact total coverage is required. |
| Dense sample QC differs from VDS sample QC. | Dense workflow may not convert `LGT`/`LA` correctly or may count reference-block base thresholds differently. | Use `hl.vds.sample_qc(vds)` as the VDS-native path; if comparing dense output, first annotate `GT=hl.vds.lgt_to_gt(mt.LGT, mt.LA)`. |

## Local Allele Field Confusion

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `LGT` allele indexes do not match row `alleles` positions. | `LGT` indexes positions inside `LA`, not global allele indexes. | Convert with `hl.vds.lgt_to_gt(vmt.LGT, vmt.LA)` before global allele logic. |
| `LAD` or `LPL` arrays look too short for multiallelic rows. | Arrays are local to observed alleles, by design. | Use `hl.vds.local_to_global` only when a downstream format/API requires global arrays. |
| `local_to_global` throws local allele out-of-bounds. | `n_alleles` does not match `hl.len(vmt.alleles)`, or `LA` was corrupted by manual edits. | Pass `hl.len(vmt.alleles)` and avoid hand-editing `LA`; after sample filtering, use `remove_dead_alleles=True` if alleles should be compacted. |
| Globalizing `LPL` makes a job explode in size. | `number="G"` arrays scale with genotype count at the total allele count. | Avoid global `PL` unless required for export/compatibility; filter high-allele sites or cap alleles first. |
| Reference rows have no `LA` field. | Reference blocks are represented in `reference_data`; local alleles are a variant-data concept. | Do not force `LA` onto reference data. `to_merged_sparse_mt` can synthesize trivial local allele information for reference-block rows. |

## Reference Block `END` and `LEN` Issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `vds.validate` says reference data needs `END` or `LEN`. | Manually constructed or transformed reference data dropped both block extent fields. | Preserve one of `END` or `LEN`; reconstruct `LEN=END-locus.position+1` or `END=LEN+locus.position-1` if possible. |
| Negative or missing `LEN` validation errors. | Bad source reference blocks, wrong `END`, or interval segmentation created invalid extents. | Check entries where `END < locus.position` or `LEN < 0`; regenerate from valid GVCFs or fix segmentation logic. |
| Interval filtering warns about missing max reference block length and runs slowly. | VDS lacks `ref_block_max_length` global metadata. | Run `hl.vds.store_ref_block_max_length(vds_path)` for in-place metadata patch, or create a rewritten VDS with `hl.vds.truncate_reference_blocks`. |
| `read_dense_mt` errors that `ref_block_max_length` is missing. | Direct dense read needs max block metadata to query reference blocks efficiently. | Patch with `store_ref_block_max_length` or rewrite with `truncate_reference_blocks` before dense read. |
| Filtered intervals include reference blocks starting before the interval. | A reference block that overlaps the interval starts earlier than the requested interval. | This is expected in default interval filtering. Use `split_reference_blocks=True` when output blocks must be trimmed to the interval. |

## Component Mismatch and Manual VDS Construction

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `VariantDataset(reference_data, variant_data)` fails immediately. | Component row keys, column keys, or reference genomes do not satisfy VDS requirements. | Ensure `reference_data` is keyed by `locus`, `variant_data` by `locus, alleles`, and both components use matching sample columns and reference genome. |
| `validate(check_data=True)` fails on column agreement. | One component was independently filtered or reordered by columns. | Apply sample filters through `hl.vds.filter_samples`, or filter both components identically and preserve column key/order. |
| `variant_data` rows are empty after sample filtering. | Removed samples carried all entries for some variants. | This is expected; Hail drops empty variant rows. Use `remove_dead_alleles=True` if retained rows also need compacted `alleles` and `LA`. |
| `to_merged_sparse_mt` cannot fill reference-only alleles. | Reference genome has no sequence attached and rows lack `ref_allele`. | Pass `ref_allele_function=lambda row: hl.missing("str")` for workflows that can tolerate missing reference allele, or attach reference sequence before conversion. |

## Combiner Plan and Resume Problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `new_combiner` says at least one of `gvcf_paths` or `vds_paths` must be nonempty. | No inputs were supplied. | Validate input lists before constructing the combiner. |
| `new_combiner` requires a GVCF partitioning argument. | GVCF inputs need import intervals. | Provide exactly one of `intervals`, `import_interval_size`, `use_genome_default_intervals=True`, or `use_exome_default_intervals=True`. |
| Multiple partitioning arguments produce a warning. | More than one interval strategy was supplied. | Keep only the intended strategy so plan hashes and resume behavior are clear. |
| Resume uses an unexpected old plan. | `save_path` already exists and `force=False`, or generated plan hash matched. | Use `hl.vds.load_combiner(plan_path)` to resume intentionally, or pass `force=True` only when restarting from scratch. |
| Loading a moved plan warns about `path`/`save_path` mismatch. | The serialized plan's old `save_path` differs from the path used to load it. | Hail updates the plan to the new path; save again before long runs. |
| Combiner says output already exists. | Component success markers exist for the output path while the plan is unfinished. | Treat the output as completed and read it, or move/delete the output before resuming. |
| Merge step fails from too many tasks or excessive work. | `gvcf_batch_size`, `branch_factor`, or interval count creates oversized work units. | Lower `gvcf_batch_size` or `branch_factor`; use more appropriate intervals. The setter caps extreme task counts but cannot fix all cluster limits. |

## GVCF, Reference, and Schema Mismatches

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Reference genome mismatch in intervals. | Custom intervals are typed with a different reference genome than `reference_genome`. | Recreate intervals using the same reference genome as the combiner. |
| GVCF contigs like `1` fail against GRCh38 `chr1`. | Source contig names do not match Hail reference contigs. | Use `contig_recoding={"1": "chr1", ...}` or a matching reference genome. |
| `gvcf_sample_names` error. | Names supplied without `gvcf_external_header`, header supplied without names, length mismatch, or duplicates. | Supply both `gvcf_sample_names` and `gvcf_external_header` with the same length as `gvcf_paths`, and keep names unique. |
| Duplicate or empty GVCF path error. | Input list has repeated or blank paths. | Deduplicate and validate paths before creating the combiner. |
| Adding VDS inputs produces warnings about reference entry fields or call fields. | Existing VDS schema dictates fields; requested GVCF fields do not match it. | Align `gvcf_reference_entry_fields_to_keep` and `call_fields` to the existing VDS schema, or combine compatible inputs separately. |
| `gvcf_save_filters` mismatch with VDS inputs. | Existing VDS either has `gvcf_filters` when new GVCFs would drop filters, or lacks filters when new GVCFs would save them. | Recreate inputs with consistent filter preservation or choose a compatible VDS set. |
| Reference block with non-reference genotype error. | A GVCF record with `END` has non-hom-ref `GT`, violating VDS reference-block assumptions. | Validate/regenerate the GVCF or route those records as variants; the combiner intentionally rejects inconsistent reference blocks. |

## Interval Filtering Surprises

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Interval table is rejected. | Table key is not exactly one `interval<locus>` field matching the VDS reference genome. | Key by a single interval field with the same locus reference type. |
| `split_reference_blocks=True` with `keep=False` errors. | Split mode only supports keeping intervals. | Use default `keep=False` without split mode, or invert the interval set externally. |
| Segmentation errors mention start-inclusive or cross-contig intervals. | `segment_reference_blocks` requires start-inclusive intervals that do not span contigs. | Normalize/validate interval input before calling interval coverage or split interval filtering. |
| Reference blocks outside the interval still appear after default filtering. | Default mode preserves overlapping blocks rather than trimming extents. | Use `split_reference_blocks=True` to segment and trim reference blocks. |
| Narrow interval query is unexpectedly expensive. | Missing `ref_block_max_length` forces broad reference-data scan. | Patch or truncate reference blocks before repeated interval queries. |

## Dense Conversion Warnings

Densification creates entries for every sample at every variant row. Before `hl.vds.to_dense_mt(vds)` or `hl.vds.read_dense_mt(path)`, ask:

1. Can the task use `vds.variant_data` only?
2. Can coverage use `hl.vds.interval_coverage` instead of dense per-base logic?
3. Can sample QC use `hl.vds.sample_qc`?
4. Can the workflow filter samples, variants, chromosomes, or intervals first?
5. Does the downstream method require global `GT`, `AD`, or `PL`, and can only those fields be converted?

If densification is still required, checkpoint after expensive filters, convert `LGT` to `GT` explicitly when global genotypes are needed, and avoid globalizing `LPL` unless output compatibility requires it.
