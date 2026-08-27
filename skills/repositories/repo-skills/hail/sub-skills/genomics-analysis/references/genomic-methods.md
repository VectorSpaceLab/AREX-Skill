# Genomic Methods Guidance

This reference maps common dense-genomics tasks to Hail APIs and the schema assumptions they require.

## Method Selection Table

| Task | Primary Hail API | Input expectations | Output |
| --- | --- | --- | --- |
| Import VCF | `hl.import_vcf` | VCF files with compatible headers/sample order; optional `reference_genome`, `contig_recoding` | `MatrixTable` keyed by `locus`, `alleles`; columns keyed by `s` |
| Import PLINK | `hl.import_plink` | Binary SNP-major `bed`/`bim`/`fam`; unique FAM individual IDs | `MatrixTable` with `GT` entries and FAM-derived column fields |
| Index/import BGEN | `hl.index_bgen`, `hl.import_bgen` | BGEN v1.2-style bi-allelic unphased diploid variants, `.idx2` index | `MatrixTable` with selected `GT`, `GP`, or `dosage` entries |
| Import intervals | `hl.import_locus_intervals`, `hl.import_bed` | Reference genome matching target loci | interval-keyed `Table` for row filtering |
| Native cache | `mt.write`, `hl.read_matrix_table`, `mt.checkpoint` | Any valid `MatrixTable` | Hail-native `.mt` dataset |
| Variant QC | `hl.variant_qc` | `GT: call`, row key/fields represent `locus`, `alleles` | row struct, default `variant_qc` |
| Sample QC | `hl.sample_qc` | `GT: call`, row key/fields represent `locus`, `alleles` | column struct, default `sample_qc` |
| Split multiallelics | `hl.split_multi_hts` | Hail HTS entry schema such as `GT`, `AD`, `DP`, `GQ`, `PL` | split biallelic rows with `a_index`, `was_split` |
| PCA on calls | `hl.hwe_normalized_pca` | diploid, biallelic `CallExpression` | eigenvalues, column scores table, row loadings table |
| PCA on numeric entries | `hl.pca` | numeric entry expression such as normalized dosage | eigenvalues, scores table, loadings table |
| LD pruning | `hl.ld_prune` | diploid, biallelic call expression | row-keyed table of retained variants |
| Quantitative association | `hl.linear_regression_rows` | column-indexed `y`/covariates, entry-indexed numeric `x` | row-keyed results table |
| Case-control association | `hl.logistic_regression_rows` | Boolean or 0/1 `y`, column covariates, entry `x` | row-keyed results table |
| Gene/set association | `hl.skat` | grouped variant sets, entry genotypes/dosage, phenotypes/covariates | set-level association table |
| Relatedness pruning | `hl.pc_relate`, `hl.king`, `hl.identity_by_descent`, `hl.maximal_independent_set` | call/dosage data with enough variants | related-pair table and filtered samples |
| VEP annotation | `hl.vep` | variant row keys and VEP config/executable/cache | row annotation field plus optional global CSQ header |
| Nirvana annotation | `hl.nirvana` | variant row keys and Nirvana config/cache/reference | row annotation field |
| Family methods | `hl.Pedigree.read`, trio/family methods | FAM-like pedigree with matching sample IDs | pedigree object or family-based tables |

## Quality Control

### `hl.variant_qc`

`variant_qc(mt, name='variant_qc')` adds a row-indexed struct with allele metrics, call counts, call rate, genotype counts, transition/transversion statistics, HWE metrics for biallelic rows, and optional DP/GQ stats when those entry fields are integer typed.

```python
mt = hl.variant_qc(mt)
mt = mt.filter_rows(
    (mt.variant_qc.call_rate >= 0.98) &
    (mt.variant_qc.AF[1] > 0.01) &
    (mt.variant_qc.p_value_hwe > 1e-6)
)
```

Run variant QC after import and after major entry/sample filters. Imported VCF INFO counts are not recomputed automatically.

### `hl.sample_qc`

`sample_qc(mt, name='sample_qc')` adds a column-indexed struct with call rate, genotype counts, singleton counts, transition/transversion ratio, heterozygote/homozygote ratio, insertion/deletion ratio, optional DP/GQ stats, and call counts.

```python
mt = hl.sample_qc(mt)
mt = mt.filter_cols(
    (mt.sample_qc.call_rate >= 0.98) &
    (mt.sample_qc.r_ti_tv > 1.5)
)
```

QC functions require `GT` to be a `call` entry field. If only dosages are present, use dosage-specific aggregations or import `GT` when available.

## Multiallelic Splitting

Use `hl.split_multi_hts` before biallelic-only statistics. It handles high-throughput sequencing entry fields:

- `GT` and `PGT`: downcoded per alternate allele.
- `AD`: alternate depth for selected allele; reference depth sums other categories.
- `DP`: copied.
- `PL`: minimized over multiallelic genotypes that downcode to each biallelic genotype.
- `GQ`: recomputed from `PL` when available; otherwise copied.

New row fields include `a_index` and `was_split`. Row `info` arrays are not universally rewritten to per-allele scalar semantics; use `a_index - 1` to select allele-specific values before export or analysis.

## PCA

Use HWE-normalized PCA for common genetic PCA on calls:

1. Filter/split to biallelic diploid variants.
2. Run `variant_qc` and filter to common variants.
3. LD prune.
4. Run HWE-normalized PCA on pruned calls.
5. Join scores back to columns.

`hl.pca(entry_expr, k=10, compute_loadings=False)` accepts a numeric entry expression such as dosage or a normalized numeric matrix. It is not a substitute for genetics-specific HWE normalization unless that is intended.

## Relatedness and Sample Pruning

Common workflow:

```python
rel = hl.pc_relate(mt.GT, min_individual_maf=0.01, k=10, statistics="kin")
pairs = rel.filter(rel.kin > 0.125)
to_remove = hl.maximal_independent_set(pairs.i, pairs.j, keep=False)
mt = mt.filter_cols(hl.is_defined(to_remove[mt.col_key]), keep=False)
```

Use relatedness methods on a QCed, preferably LD-pruned/common-variant subset. Apply the resulting sample removals to the original post-QC dataset, not only the subset used to infer relatedness.

## Association Tests

### Linear Regression

`linear_regression_rows(y, x, covariates, block_size=16, pass_through=(), weights=None)` tests each row's entry-indexed `x` against one or more column-indexed quantitative phenotypes.

Rules:

- Include intercept explicitly in `covariates` if desired: `covariates=[1, ...]`.
- `x` is usually `mt.GT.n_alt_alleles()` or a dosage entry.
- `y` may be a single expression, a list of expressions, or grouped lists; missingness behavior differs for grouped lists.
- Use `pass_through` for row annotations such as `rsid`, gene, or consequence fields.

### Logistic Regression

`logistic_regression_rows(test, y, x, covariates, pass_through=(), max_iterations=None, tolerance=None)` supports `test="wald"`, `"lrt"`, `"score"`, or `"firth"`.

Rules:

- `y` must be Boolean or numeric with present values 0/1.
- Missing response/covariates define a common set of samples; missing `x` values are mean-imputed for each row.
- Use `"firth"` for rare variants or quasi-complete separation where Wald/LRT convergence is suspicious.
- Inspect convergence, explosion, and iteration fields when available in the result schema.

### SKAT and Burden-Style Workflows

Use `hl.skat` for set-level rare variant association when the task groups variants by gene, region, or annotation. Ensure variant sets are well-defined row annotations or group keys, entry genotype/dosage expression is numeric, covariates are column-indexed, and filtering/splitting/annotation steps happen before grouping.

## VEP and Nirvana Boundaries

`vep(dataset, config=None, block_size=1000, name='vep', csq=False, tolerate_parse_error=False)` can annotate a `MatrixTable` or `Table` with variant-like row keys. It requires an external VEP runtime or service configuration.

Use VEP when the environment provides:

- A VEP executable/command and cache matching the assembly.
- A JSON config or supported service/cloud configuration.
- A schema for parsed JSON output, or `csq=True` when CSQ strings are preferred.

Hail-specific behavior:

- Adds row field `name` and process metadata.
- With `csq=True`, adds global field `name + "_csq_header"`.
- Distinct row variants are annotated and then joined back.
- `split_multi_hts` can split variable-length VEP consequence arrays by `a_index` when `vep_root` points to the VEP field.

Nirvana-style annotation is similar as a workflow boundary. Hail can host row annotations and parse results, but the annotator executable/cache/reference assets are outside dense MatrixTable semantics.

## ReferenceGenome, Locus, Call, and Pedigree

### `ReferenceGenome`

Built-ins include `GRCh37`, `GRCh38`, `GRCm38`, and `CanFam3`; names are case-sensitive. Use `hl.get_reference("GRCh38")` for built-ins. Custom references can define contigs, lengths, X/Y/MT contigs, PAR intervals, sequence files, and liftover chains.

Use reference operations for contig length validation, parsing `locus` and interval strings, liftover setup and validation, and aligning import options with data assembly.

### `Locus`

A Python `hl.Locus` value represents `contig`, 1-based `position`, and a reference genome. Most pipelines manipulate `LocusExpression` values such as `mt.locus`, `hl.locus`, or `hl.parse_locus` rather than collecting Python `Locus` objects. Parse variant strings with `hl.parse_variant`, which returns `locus` and `alleles` fields suitable for keys.

### `Call`

A Python `hl.Call` value represents genotype alleles and phase. Most pipelines manipulate `CallExpression` values (`mt.GT`). Useful expression methods include `is_hom_ref()`, `is_het()`, `is_hom_var()`, and `n_alt_alleles()`.

### `Pedigree`

Use `hl.Pedigree.read(fam_path)` for PLINK FAM-like pedigree data when family methods need trios. A `Pedigree` stores trios and can filter to known samples. Reading/writing a `Pedigree` does not preserve phenotype information; use `hl.import_fam` or `hl.import_plink` when phenotypes must remain data fields.

## Export and Result Tables

Association and relatedness functions usually return `Table` outputs. Export these with `ht.export(...)` after selecting fields:

```python
results = results.select("rsid", "beta", "standard_error", "p_value")
results.export("gwas.tsv.bgz")
```

For a final VCF, ensure the MatrixTable schema matches VCF semantics and rewrite stale `info` fields after filtering. Use `hl.export_vcf` for VCF and `mt.write` for native reusable Hail datasets.
