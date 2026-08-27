# Data Formats

OmicVerse table workflows are sensitive to orientation. Validate IDs and metadata before loading data into OmicVerse objects.

## Common Matrix Orientations

| Workflow | Preferred Matrix Orientation | Metadata Orientation | OmicVerse Object |
| --- | --- | --- | --- |
| Bulk RNA-seq `ov.bulk.pyDEG` | genes/features in rows, samples in columns | sample metadata keyed by matrix columns | pandas DataFrame; not necessarily AnnData |
| Bulk ORA/GSEA | gene list or ranked genes | optional background universe | list/Series/DataFrame |
| `ov.es` signature scoring | observations/cells/samples in rows, genes in columns for DataFrame; genes in `adata.var_names` for AnnData | optional observation metadata in `obs` | AnnData or DataFrame |
| Metabolomics `ov.metabol` | samples in rows, metabolites/features in columns | sample metadata in columns or `adata.obs` | AnnData with `X = samples × metabolites` |
| Proteomics `ov.protein` | samples in rows, proteins in columns after reader output | sample metadata in `adata.obs`, protein metadata in `adata.var` | AnnData with `X = samples × proteins` |
| Microbiome `ov.micro` | samples in rows, taxa/ASVs/OTUs in columns | sample metadata in `adata.obs`, taxonomy in `adata.var` | AnnData with count-like `X = samples × taxa` |

## Feature-by-Sample Matrix + Metadata

Many input files arrive as `features × samples` matrices plus a separate sample metadata table. Validate them with the bundled script before transposing/loading.

Example matrix:

```text
feature_id\tS1\tS2\tS3\tS4
GeneA\t10\t12\t3\t4
GeneB\t0\t5\t8\t9
```

Example metadata:

```text
sample\tgroup\tbatch\ttime
S1\tcase\tB1\t0
S2\tcase\tB1\t1
S3\tcontrol\tB2\t0
S4\tcontrol\tB2\t1
```

Check command:

```bash
python sub-skills/multiomics-statistics/scripts/check_multiomics_table.py counts.tsv --metadata metadata.tsv --sample-id-column sample --required-metadata-cols group,batch
```

What the checker verifies:

- Header and delimiter are readable for CSV or TSV.
- Feature IDs in the first matrix column are present and unique.
- Sample IDs in matrix columns are present and unique.
- Abundance cells are numeric, blank, `NA`, `NaN`, or equivalent missing tokens.
- Metadata sample IDs are present and unique.
- Matrix samples match metadata rows unless `--allow-extra-metadata` is set.
- Required metadata columns such as `group`, `batch`, `time`, or `subject` exist.

## Design Metadata Columns

| Use Case | Required / Common Columns | Notes |
| --- | --- | --- |
| Two-group bulk DE | `group` or explicit sample lists | If using `pyDEG.deg_analysis`, group lists are supplied directly, but metadata is still useful for validation. |
| Bulk time course | `time`; optional `group`, `subject`/`block` | Time Series passed to `timecourse_deg` should be indexed by sample IDs. |
| Metabolomics differential | `group` | `read_metaboanalyst(..., group_col=...)` copies the selected factor to `obs['group']`. |
| Metabolomics QC | `is_qc`, `is_blank`, `injection_order` | QC/blank/drift functions fail when these columns are missing or masks contain too few samples. |
| Metabolomics ASCA/mixed/MEBA | design factors; `groups`; `time`; `subject` | Formulas and factor levels must match `adata.obs` exactly. |
| Proteomics differential | `group` or labels array | `de(..., group="condition")` requires that column in `adata.obs`. |
| Proteomics DEqMS | `peptides` or other count variable in `adata.var` | `count_var` defaults to `peptides`; missing count column falls back to count-free behavior only in some routes. |
| Microbiome diversity | optional `group` for plotting/stratification | Alpha/Beta do not require group labels; downstream tests often do. |
| Microbiome differential abundance | `group`; optional taxonomy rank in `adata.var` | `DA(..., rank="genus")` requires `var['genus']`. |
| Microbiome UniFrac / Faith PD | `adata.uns['tree']`; taxa names matching tree tips | Newick tree must match `adata.var_names`. |
| Paired microbe-metabolite | identical `obs_names` in both AnnData objects | `paired_spearman` rejects mismatched sample IDs. |

## Signature and Network Formats

### Dict Signatures

Unweighted:

```python
signatures = {
    "IFN_RESPONSE": ["ISG15", "IFI6", "MX1"],
    "INFLAMMATION": ["IL6", "TNF", "CXCL8"],
}
```

Weighted/signed:

```python
signatures = {
    "NFKB": {"TNF": 1.0, "IL6": 1.0, "IL10": -1.0},
}
```

Rules:

- Signature names become score columns.
- Gene names must match the expression matrix feature names exactly after any casing/ID conversion.
- Use weighted dict values for methods that use direction, such as `viper`, `mlm`, `ulm`, `zscore`, and regulon-like scoring.

### Long Network DataFrame

```text
source\ttarget\tweight
IFN_RESPONSE\tISG15\t1.0
IFN_RESPONSE\tIFI6\t1.0
NFKB\tIL10\t-1.0
```

Rules:

- Pass as `net=net_df`, not `signatures=...`.
- Do not pass both `signatures` and `net`.
- `source` is the pathway/signature/regulon name; `target` is the feature/gene; `weight` is numeric.

## AnnData Slot Expectations

### Metabolomics

- `adata.X`: numeric samples-by-metabolites matrix.
- `adata.obs['group']`: default group column for `differential`, `plsda`, and pyMetabo-style pipelines.
- `adata.var_names`: metabolite names or feature IDs; used by differential and enrichment routes.
- `adata.var['m_z']`, `adata.var['rt']`: optional LC-MS fields parsed by `read_lcms` for mummichog-style workflows.
- `adata.layers`: optional transformed/raw matrices when workflow functions stash intermediates.

### Proteomics

- `adata.X`: samples-by-proteins matrix; readers start with raw intensities, then `normalize` usually log2-transforms.
- `adata.obs`: sample metadata, especially group labels.
- `adata.var['peptides']`: peptide/PSM count for DEqMS; readers populate when source files include counts.
- `adata.var['Gene_names']`, `adata.var['Protein_IDs']`: useful for labels and downstream enrichment.
- `adata.layers['raw']`, `adata.layers['log2']`: written by `ov.protein.normalize` when `stash_raw=True` and `log2=True`.
- `adata.uns['protein_de']`: written by `ov.protein.de`.

### Microbiome

- `adata.X`: raw integer counts for rarefaction, DESeq2, and many diversity methods; relative/proportional values are acceptable only for methods that explicitly support them.
- `adata.obs`: sample group, study, covariate, or pairing metadata.
- `adata.var`: taxonomic ranks such as `domain`, `phylum`, `class`, `order`, `family`, `genus`, `species`; optional `sequence` for ASVs.
- `adata.uns['tree']`: Newick tree string for Faith PD and UniFrac metrics.
- `adata.obsp[metric]`: beta distance matrices written by `Beta.run`.
- `adata.obsm[f'{metric}_pcoa']` and `adata.obsm[f'{metric}_nmds']`: ordination coordinates.

## Missing Values and Numeric Cells

- Bulk RNA counts should be numeric and usually nonnegative integers for count-based methods.
- Metabolomics peak tables may include blanks, zeros, and missing values; apply imputation and QC before log transforms.
- Proteomics LFQ tables often encode missing values as zeros; `read_maxquant` converts zeros to NaN for intensities.
- Microbiome counts should remain count-like for rarefaction, DESeq2, and UniFrac; CLR/proportion transforms change method assumptions.
- The schema checker accepts common missing tokens (`NA`, `NaN`, `N/A`, `null`, blank) but reports them so the workflow can decide how to impute or filter.

## Network and Identifier Mapping Inputs

Metabolomics enrichment and mummichog routes may use KEGG/HMDB/ChEBI/LION mappings. Prefer local data frames when the user has them:

- `pathways`: dict or DataFrame mapping pathway names to compound IDs.
- `mass_db`: local compound database DataFrame with KEGG/HMDB/ChEBI aliases.
- `hits` and `background`: metabolite names or IDs that can be resolved against `mass_db`.

Do not promise that remote fetchers are safe or available. Ask before enabling network-backed pathway or compound database fetches.
