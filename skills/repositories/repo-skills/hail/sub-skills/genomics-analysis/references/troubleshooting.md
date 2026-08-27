# Genomics Analysis Troubleshooting

This guide focuses on dense MatrixTable and genetics workflow failures. Route backend initialization, cluster, Java/Spark, cloud credentials, and general installation problems to `../setup-and-backends/SKILL.md`. Route sparse GVCF/VDS issues to `../variant-datasets/SKILL.md`.

## Quick Diagnosis Table

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Import says contig is not in reference | VCF/PLINK/BGEN contigs do not match `reference_genome` | Use correct `reference_genome`, add `contig_recoding`, or set `skip_invalid_loci=True` only if dropping rows is acceptable |
| Many rows skipped or loci invalid | Wrong assembly, invalid positions, or over-broad `skip_invalid_loci` | Verify source build, inspect contig naming and max positions, avoid recoding assembly mismatches |
| `.vcf.gz` import is very slow | Standard gzip or serial forced import | Use `.vcf.bgz` block gzip; use `force_bgz=True` only for true bgzip files |
| BGEN import fails before reading entries | Missing or stale `.idx2` index | Run `hl.index_bgen` once with matching reference and use the same index mapping |
| `variant_qc` or `sample_qc` errors on `GT` | Missing `GT` or `GT` is not `call` | Import/request `GT`, use `call_fields` for true call fields, or write dosage-specific aggregations |
| HWE p-values missing after QC | Multiallelic rows | Run `hl.split_multi_hts` or filter to `hl.len(mt.alleles) == 2` before relying on HWE |
| `split_multi_hts` errors on out-of-order keys | Dataset has multiple records at a locus with multiallelic/biallelic mixture | Split multiallelic and biallelic subsets separately, or use `permit_shuffle=True` deliberately |
| Exported split VCF has odd INFO `Number` fields | INFO arrays were not allele-selected after split | Rewrite allele-specific INFO fields with `info.FIELD[a_index - 1]` before export |
| Association test complains about indices | Row/column/entry expression used on wrong axis | Check `expr.describe()` and make `y`/covariates column-indexed, `x` entry-indexed |
| Logistic regression has many non-converged rows | Separation, rare variants, collinear covariates | Try `test="firth"`, filter rare variants, inspect covariates, or use burden/SKAT methods |
| `hl.vep` or `hl.nirvana` fails before annotation | Missing external config/executable/cache/reference or bad schema | Provide a valid config, set matching assembly/cache, or route setup to environment guidance |
| Pipeline hangs or runs out of memory after `entries()`/`collect()` | Large distributed data materialized locally or expanded to coordinates | Use Hail joins/aggregations, `rows()`, `cols()`, checkpoints, and distributed exports |

## Reference and Contig Mismatch

### Check the problem

```python
mt.describe()
mt.locus.describe()
mt.aggregate_rows(hl.agg.counter(mt.locus.contig))
```

If import fails before creating `mt`, inspect a header or import a tiny safe subset. For VCF, compare contig names and assembly in the header to the intended `reference_genome`.

### Use `contig_recoding` only for labels

Good use: source VCF has `1`, `2`, ..., `X` but the target reference expects `chr1`, `chr2`, ..., `chrX`.

```python
recode = {str(i): f"chr{i}" for i in range(1, 23)} | {"X": "chrX", "Y": "chrY", "MT": "chrM"}
mt = hl.import_vcf(path, reference_genome="GRCh38", contig_recoding=recode)
```

Bad use: source is truly GRCh37 coordinates and target is GRCh38. Contig recoding cannot change positions or alleles; use liftover with appropriate chain files and allele validation, or obtain correctly aligned data.

### `skip_invalid_loci`

Use `skip_invalid_loci=True` only when invalid rows are known bad records and can be dropped. Record the choice because it changes the analysis population. Do not use it to mask a broad assembly mismatch.

## Compression, Indexing, and Partitioning

### VCF bgzip issues

- Prefer `.vcf.bgz` for block-gzipped files.
- If the file ends in `.vcf.gz` but is actually bgzip, use `force_bgz=True` or rename it.
- If it is standard gzip, `force=True` can import but is slow and not recommended for substantial datasets.
- For multiple VCFs, headers and sample order must match. Use `header_file=` when shards lack headers or need a consistent header.

### BGEN index issues

- Run `hl.index_bgen` once per BGEN file and keep the generated `.idx2` beside the BGEN or pass `index_file_map`.
- Index and import with the same reference genome and contig recoding assumptions.
- BGEN import supports bi-allelic unphased diploid variants; incompatible BGEN data needs preprocessing outside Hail.

## Entry and Call Field Confusion

### `GT` versus dosage

Many genetics methods require `GT: call`:

- `hl.variant_qc`
- `hl.sample_qc`
- `hl.hwe_normalized_pca`
- `hl.ld_prune`
- methods that call `mt.GT.n_alt_alleles()`

BGEN dosage workflows may only import `dosage`. In that case:

- Use `hl.pca(mt.dosage, ...)` for numeric PCA-like workflows if appropriate.
- Use association `x=mt.dosage` when dosage is the intended predictor.
- Do not call `variant_qc`/`sample_qc` unless a valid hard-call `GT` is present.

### FORMAT call fields

`hl.import_vcf` loads `GT` as `call` automatically and can load additional FORMAT fields as calls with `call_fields=[...]`. If a FORMAT field is not a genotype call, do not add it to `call_fields`.

## Multiallelic Split Mistakes

### Common mistakes

- Running biallelic-only methods on unsplit multiallelic rows.
- Filtering `info.AC` after split without indexing by `a_index`.
- Assuming split rows preserve original row order without a shuffle when duplicate loci exist.
- Splitting a dataset with custom entry fields and assuming custom fields are adjusted automatically.

### Safer pattern

```python
bi = mt.filter_rows(hl.len(mt.alleles) == 2).annotate_rows(a_index=1, was_split=False)
multi = mt.filter_rows(hl.len(mt.alleles) > 2)
split = hl.split_multi_hts(multi)
mt = split.union_rows(bi)

if "AC" in mt.info:
    mt = mt.annotate_rows(info=mt.info.annotate(AC=mt.info.AC[mt.a_index - 1]))
```

If the dataset has mixed biallelic and multiallelic records at the same locus and `split_multi_hts` reports out-of-order keys, use the subset-and-union pattern above or permit a shuffle deliberately.

## VEP and External Annotation Failures

`hl.vep` and `hl.nirvana` are not pure Hail expression logic. They need external runtimes, caches, schemas/configs, and matching assemblies.

Diagnose:

- Is `config` provided, or is the environment configured to find one?
- Does the config assembly match the MatrixTable reference (`GRCh37` vs `GRCh38`)?
- Does the command in the config exist on every worker or in the service environment?
- Does `csq=True` match the desired VEP output format, or should JSON schema parsing be used?
- Are VEP consequence arrays being split correctly after `split_multi_hts` via the right `vep_root`?

For VEP, `tolerate_parse_error=True` returns missing annotations for bad rows, which can hide annotation failures. Use it only when expected and audited.

## Association Covariate Shape Errors

### Axis requirements

- `y`: column-indexed expression or list of column-indexed expressions.
- `x`: entry-indexed numeric expression.
- `covariates`: list of column-indexed expressions or constants.
- `pass_through`: row fields or row-indexed expressions.

Debug with:

```python
mt.pheno.height.describe()
mt.GT.n_alt_alleles().describe()
mt.pheno.age.describe()
```

### Intercept and missingness

Hail does not add an intercept automatically. Use `covariates=[1, ...]` when the model should include one. Missing phenotype or covariate values drop samples from the analysis; if multiple phenotypes have different missingness patterns, consider separate runs or grouped `y` lists for linear regression.

### Logistic convergence

For rare variant case-control tests:

- Inspect convergence and explosion fields when available in the output schema.
- Try `test="firth"` for separation-prone rows.
- Filter variants by minor allele count/frequency when appropriate.
- Check for duplicate or collinear covariates, including PCs and sex/ancestry indicators.

## Expensive `collect`, `entries`, and Checkpoint Issues

### Avoid local materialization

Bad patterns for large cohorts:

```python
keys = mt.rows().key_by().select().collect()
entry_table = mt.entries()
local = mt.aggregate_rows(hl.agg.collect(mt.locus))
```

Safer patterns:

```python
annotation = annotation_ht.key_by("locus", "alleles")
mt = mt.annotate_rows(ann=annotation[mt.row_key])

sample_table = sample_ht.key_by("s")
mt = mt.annotate_cols(pheno=sample_table[mt.s])

mt.rows().select("variant_qc").export("variant_qc.tsv.bgz")
```

### Checkpointing

Use `checkpoint` after operations that would otherwise be recomputed repeatedly:

- VCF/PLINK/BGEN import to native `.mt`.
- Large annotation joins.
- Entry filters before QC.
- Multiallelic splitting.
- VEP/Nirvana annotation.
- LD-pruned or post-QC subsets reused by multiple downstream analyses.

If checkpoint/write fails, separate data-path permissions or backend storage issues from MatrixTable logic and route environment/storage setup as needed.
