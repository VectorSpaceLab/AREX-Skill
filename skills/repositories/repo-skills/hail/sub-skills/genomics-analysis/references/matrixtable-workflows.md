# Dense MatrixTable Workflows

Use these patterns for dense genotype data where rows are variants/sites, columns are samples, and entries are observed values for each sample at each site.

## Axis Checklist

Before writing transformations, identify each field's axis:

| Axis | Typical fields | Methods | Joins/indexing |
| --- | --- | --- | --- |
| Row | `locus`, `alleles`, `rsid`, `qual`, `filters`, `info`, `variant_qc`, `vep` | `annotate_rows`, `filter_rows`, `select_rows`, `rows()` | keyed by `mt.row_key`, commonly `locus`, `alleles` |
| Column | `s`, sample metadata, phenotype, sex, ancestry PCs, `sample_qc` | `annotate_cols`, `filter_cols`, `select_cols`, `cols()` | keyed by `mt.col_key`, commonly `s` |
| Entry | `GT`, `AD`, `DP`, `GQ`, `PL`, `PGT`, `PID`, `GP`, `dosage` | `annotate_entries`, `filter_entries`, `select_entries` | indexed by both row and column |
| Global | source metadata, VEP CSQ header, run parameters | `annotate_globals`, `select_globals`, `index_globals()` | shared across the dataset |

Use `mt.describe()` and targeted `mt.<field>.describe()` to verify axis and type. A column phenotype cannot be used as a row field without aggregation or join logic, and an entry expression cannot be used where Hail expects a row-only or column-only expression.

## Import, Inspect, Cache

The verified signatures include:

- `hl.import_vcf(path, force=False, force_bgz=False, header_file=None, min_partitions=None, drop_samples=False, call_fields=['PGT'], reference_genome='default', contig_recoding=None, array_elements_required=True, skip_invalid_loci=False, entry_float_type=..., filter=None, find_replace=None, n_partitions=None, block_size=None, ...)`
- `hl.import_plink(bed, bim, fam, min_partitions=None, delimiter='\\s+', missing='NA', quant_pheno=False, a2_reference=True, reference_genome='default', contig_recoding=None, skip_invalid_loci=False, n_partitions=None, block_size=None)`
- `hl.import_bgen(path, entry_fields, sample_file=None, n_partitions=None, block_size=None, index_file_map=None, variants=None, _row_fields=['varid', 'rsid'])`

### VCF to Native `.mt`

```python
import hail as hl

hl.init()
mt = hl.import_vcf(
    vcf_path,
    reference_genome="GRCh38",
    force_bgz=True,          # only when a .gz file is actually block-gzipped
    array_elements_required=False,
    contig_recoding={"1": "chr1", "2": "chr2"},  # extend only for naming fixes
)
mt.describe()
mt = mt.checkpoint(native_mt_path, overwrite=True)
```

Key decisions:

- Set `reference_genome` deliberately: a built-in such as `"GRCh37"` or `"GRCh38"`, a custom `ReferenceGenome`, or `None` for workflows that cannot validate contigs at import time.
- Use `contig_recoding` for naming convention differences, not for liftover between assemblies.
- Use `skip_invalid_loci=True` only when losing invalid records is acceptable and recorded in analysis notes.
- Use `array_elements_required=False` when VCF arrays may contain missing elements such as `1,.,5`.
- Use `drop_samples=True` only for sites-only import.

### PLINK to Native `.mt`

```python
mt = hl.import_plink(
    bed="cohort.bed",
    bim="cohort.bim",
    fam="cohort.fam",
    reference_genome="GRCh37",
    missing="-9",
    quant_pheno=True,
)
mt = mt.checkpoint("cohort_plink.mt", overwrite=True)
```

PLINK import creates row fields such as `locus`, `alleles`, `rsid`, and `cm_position`, column fields such as `s`, family IDs, sex, and phenotype fields, and entry field `GT`. Use `missing="-9"` for quantitative phenotypes when PLINK's default missing phenotype marker should be treated as missing.

### BGEN to Native `.mt`

```python
hl.index_bgen("cohort.bgen", reference_genome="GRCh38")
mt = hl.import_bgen(
    "cohort.bgen",
    entry_fields=["dosage", "GP"],
    sample_file="cohort.sample",
)
mt = mt.checkpoint("cohort_bgen.mt", overwrite=True)
```

BGEN import requires `.idx2` indexes created by `hl.index_bgen`, and index/reference choices must match import choices. BGEN support is for bi-allelic, unphased, diploid variants; request only the needed entry fields (`GT`, `GP`, `dosage`) for performance.

## Sample Annotation and Phenotypes

Annotate samples by keying a `Table` to the column key:

```python
pheno = hl.import_table(pheno_tsv, impute=True, key="s")
mt = mt.annotate_cols(pheno=pheno[mt.s])
mt = mt.filter_cols(hl.is_defined(mt.pheno))
```

For covariates and association tests, keep phenotypes and covariates column-indexed:

```python
mt = mt.annotate_cols(
    is_case=hl.bool(mt.pheno.case_control),
    age=hl.float64(mt.pheno.age),
    is_female=hl.float64(mt.pheno.is_female),
    pc1=hl.float64(mt.pheno.PC1),
    pc2=hl.float64(mt.pheno.PC2),
)
```

If sample IDs differ between sources, normalize in a table before joining. Do not collect large sample maps to Python dictionaries for distributed annotation.

## Row Annotation and Intervals

Annotate variants by row key:

```python
ann = hl.import_table(annotation_tsv, impute=True)
ann = ann.annotate(**hl.parse_variant(ann.variant, reference_genome="GRCh38"))
ann = ann.key_by("locus", "alleles")
mt = mt.annotate_rows(annotation=ann[mt.row_key])
```

Filter to intervals:

```python
intervals = hl.import_locus_intervals(intervals_path, reference_genome="GRCh38")
mt = mt.filter_rows(hl.is_defined(intervals[mt.locus]))
```

For a small Python list of intervals, use `hl.filter_intervals(mt, [hl.parse_locus_interval(...)])`. For large interval files, prefer an interval-keyed table join.

## Entry Filtering and Hard-Call Cleanup

Entry filters remove or mask per-sample genotype entries, not variants or samples:

```python
mt = mt.filter_entries((mt.GQ >= 20) & (mt.DP >= 10))
mt = mt.annotate_entries(GT=hl.or_missing((mt.GQ >= 20) & (mt.DP >= 10), mt.GT))
```

After filtering entries, run QC again if exporting or using QC-derived INFO fields. Imported VCF `info.AC`, `info.AF`, and `info.AN` are not automatically updated by sample or entry filters.

## QC Workflow

```python
mt = hl.variant_qc(mt)
mt = hl.sample_qc(mt)

mt = mt.filter_cols(
    (mt.sample_qc.call_rate >= 0.98) &
    (mt.sample_qc.r_ti_tv > 1.5)
)
mt = mt.filter_rows(
    (mt.variant_qc.call_rate >= 0.98) &
    (mt.variant_qc.AF[1] > 0.01)
)
mt = mt.checkpoint("post_qc.mt", overwrite=True)
```

`variant_qc(mt, name='variant_qc')` and `sample_qc(mt, name='sample_qc')` require a `GT` entry field of type `call`. They add row or column structs with call rates, counts, transition/transversion metrics, and optional DP/GQ stats when `DP`/`GQ` are integer entry fields. For multiallelic variants, HWE fields are missing; split or filter to biallelic variants before relying on HWE metrics.

## Split Multiallelics

```python
biallelic = mt.filter_rows(hl.len(mt.alleles) == 2).annotate_rows(a_index=1, was_split=False)
multi = mt.filter_rows(hl.len(mt.alleles) > 2)
split = hl.split_multi_hts(multi, keep_star=False, left_aligned=False)
mt = split.union_rows(biallelic)
mt = mt.checkpoint("split.mt", overwrite=True)
```

`split_multi_hts(ds, keep_star=False, left_aligned=False, vep_root='vep', permit_shuffle=False)` is designed for high-throughput sequencing-style entry fields (`GT`, `AD`, `DP`, `GQ`, `PL`, `PGT`, `PID`). It downcodes calls, adjusts `AD`/`PL`, recomputes `GQ` when possible, adds `a_index` and `was_split`, and can split VEP consequence arrays under `vep_root`. It does not automatically rewrite every `info` array; rewrite allele-specific INFO fields explicitly before export.

## PCA and LD Pruning

```python
mt = mt.filter_rows(hl.len(mt.alleles) == 2)
mt = hl.variant_qc(mt)
mt_common = mt.filter_rows(mt.variant_qc.AF[1] > 0.05)

pruned = hl.ld_prune(mt_common.GT, r2=0.2, bp_window_size=500000)
mt_pruned = mt_common.filter_rows(hl.is_defined(pruned[mt_common.row_key]))

eigenvalues, scores, loadings = hl.hwe_normalized_pca(
    mt_pruned.GT,
    k=10,
    compute_loadings=True,
)
mt = mt.annotate_cols(scores=scores[mt.s].scores)
```

`ld_prune(call_expr, r2=0.2, bp_window_size=1000000, memory_per_core=256, keep_higher_maf=True, block_size=None)` and HWE-normalized PCA expect diploid, biallelic call data. `pca(entry_expr, k=10, compute_loadings=False)` accepts numeric entries such as dosage; use it only when numeric PCA is intended.

## Association Tests

Linear regression for quantitative phenotypes:

```python
gwas = hl.linear_regression_rows(
    y=mt.pheno.height,
    x=mt.GT.n_alt_alleles(),
    covariates=[1, mt.pheno.age, mt.pheno.is_female, mt.scores[0], mt.scores[1]],
    pass_through=[mt.rsid],
)
```

Logistic regression for binary phenotypes:

```python
gwas = hl.logistic_regression_rows(
    test="wald",
    y=mt.pheno.is_case,
    x=mt.GT.n_alt_alleles(),
    covariates=[1, mt.pheno.age, mt.pheno.is_female, mt.scores[0], mt.scores[1]],
    pass_through=[mt.rsid],
)
```

Rules:

- Include the intercept (`1`) explicitly.
- `y` and covariates must be column-indexed; `x` must be entry-indexed.
- For logistic regression, `y` must be Boolean or numeric 0/1; choose `"firth"` or a burden/SKAT workflow for rare variants with separation.
- Missing phenotype/covariate values exclude columns. Missing genotype `x` may be mean-imputed depending on the method.

## VEP-Style Annotation

```python
mt = hl.vep(mt, config=vep_config_path, name="vep", csq=False)
mt = mt.checkpoint("vep_annotated.mt", overwrite=True)
```

`vep(dataset, config=None, block_size=1000, name='vep', csq=False, tolerate_parse_error=False)` accepts a `MatrixTable` or `Table` with variant-like row keys and requires an external VEP runtime/config/cache. It adds a row field named by `name`; with `csq=True`, it also adds a global CSQ header. Treat VEP and Nirvana-style annotation as external annotation boundaries: Hail orchestrates and joins annotations, but the executable, cache, plugins, JSON schema, and reference assembly must be managed by the runtime environment.

## Export VCF

```python
mt = hl.variant_qc(mt)
mt = mt.annotate_rows(info=mt.info.annotate(
    AC=mt.variant_qc.AC[1:],
    AF=mt.variant_qc.AF[1:],
    AN=mt.variant_qc.AN,
))
metadata = hl.get_vcf_metadata(original_vcf_path)
hl.export_vcf(mt, "cohort.filtered.vcf.bgz", metadata=metadata, tabix=True)
```

`export_vcf(dataset, output, append_to_header=None, parallel=None, metadata=None, tabix=False)` uses row fields `rsid`, `qual`, `filters`, and `info`, plus entry fields as FORMAT. Other row, column, and global fields are ignored. Use `.vcf.bgz`, not standard `.gz`, for block-compressed output.

## Performance and Safety

- Prefer native `.mt` checkpoints after import, split, major joins, VEP annotation, and expensive QC.
- Use `persist` or `cache` only when the same intermediate is reused in the same session and enough memory/disk exists.
- Prefer Hail joins over Python-side `collect()` for row/sample annotations.
- Avoid `mt.entries()` for whole cohorts; it materializes a table with one row per variant-sample pair.
- Use `mt.rows()` and `mt.cols()` for row-only or sample-only exports.
