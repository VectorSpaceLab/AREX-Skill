# Troubleshooting

Use this matrix when OmicVerse table-centric workflows fail before or during statistical analysis.

## Input Schema Failures

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `ValueError: duplicate sample IDs` or duplicated columns | Matrix header contains repeated samples after trimming whitespace | Rename columns before loading; preserve a mapping table if duplicates are biological replicates. |
| Duplicate gene/metabolite/protein/taxon IDs | Feature index is not unique | Aggregate intentionally, disambiguate with suffixes, or call workflow-specific duplicate helpers such as `pyDEG.drop_duplicates_index()` for bulk. |
| Numeric conversion error from readers | Abundance columns include text labels or metadata | Move metadata columns to a separate metadata file or pass `sample_col`/`group_col` so only feature columns become numeric. |
| Metadata sample count differs from matrix columns | Matrix and metadata IDs are not aligned | Normalize whitespace/case, check sample naming, and use the bundled checker to list missing/extra IDs. |
| Missing `group`, `batch`, `time`, `subject`, `is_qc`, or `is_blank` | Required design/QC column absent | Add the column to metadata or change the API argument to the correct existing column name. |
| Log transform creates NaN/inf | Negative values or inappropriate pseudocount for raw-scale transform | Confirm whether data are already log-scale; for proteomics Olink NPX use `log2=False`; for metabolomics ensure nonnegative intensities before log. |

## Bulk RNA-seq

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `group1` or `group2` samples not found | DE lists do not match DataFrame columns exactly | Compare sets of sample IDs and preserve matrix columns as strings. |
| `pydeseq2` import error | DESeq2 backend not installed | Install the narrow `pydeseq2` dependency if required, or use `method="edger"` / `method="limma"` when compatible. |
| Count method fails on continuous/log data | Data include negative or pre-normalized values | Use a continuous/log-scale method or `timecourse_deg(..., data_type="continuous")`. |
| Time-course DE finds no temporal genes | Time metadata not indexed to sample columns or too few time points | Reindex `time` to matrix columns; use at least 3 distinct time points for clustering and meaningful spline/factor tests. |
| `temporal_clusters` raises missing `pymfuzz` | Optional time-course clustering backend absent | Install `pymfuzz` or `omicverse[timecourse]`, or stop at `timecourse_deg` results. |
| `Temporal clustering needs >=3 distinct time points` | Insufficient time design | Do not cluster; use two-time-point DE or collect more time points. |

## Bulk ORA/GSEA and `ov.es`

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `signatures[...] must be list / tuple / set / dict` | Wrong signature object shape | Use `{signature: [genes]}` or `{signature: {gene: weight}}`. |
| `pass either signatures or net, not both` | Both dict and long network were supplied | Choose one format; use `ov.es.signatures_to_net` to convert dicts when a long network is needed. |
| `must pass signatures or net` | No gene-set source | Provide a dict or long DataFrame with `source`, `target`, `weight`. |
| Empty or tiny score matrices | Gene IDs do not overlap signatures | Check gene symbol case/version suffixes and map Ensembl IDs to symbols if needed. |
| GPU engine error | Torch/CUDA unavailable or incompatible | Use `engine="cpu"` or `engine="auto"`; do not require GPU for verification. |
| GSEA/ORA output p-values look plausible but labels disagree | Confusion over log base | OmicVerse enrichment `logp` means `-log10(p)`; do not compare to natural-log values. |
| Remote gene-set library unavailable | Network-backed source was assumed | Pass local `pathways_dict` or ask for network authorization before fetching. |

## Metabolomics

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `group_col=... is not a column` | Wrong factor name in MetaboAnalyst/generic CSV | Print the CSV headers and pass the exact group column to `read_metaboanalyst` or `read_wide`. |
| `could not convert string to float` | Metadata or labels included among metabolite columns | Set `sample_col` and `group_col`; remove non-feature columns from the matrix. |
| `Groups need ≥2 samples each` | Group labels are sparse or misspelled | Inspect `adata.obs[group_col].value_counts()` and choose explicit `group_a` / `group_b`. |
| `has fewer than 2 unique values` | Design column contains one level | Fix metadata or choose a different factor. |
| CV filter needs `3 QC samples` | Too few pooled QC samples for robust CV | Use `across="all"` only when scientifically acceptable, or skip QC-pool CV. |
| Drift correction warns samples outside QC range | QC injections do not bracket the run | Treat corrected values cautiously; consider excluding unbracketed samples or rerunning with better QC coverage. |
| Blank filter says no blank samples | Blank mask column wrong or all false | Confirm `blank_mask` and blank sample labels. |
| PLS-DA Q² negative or unstable | Wrong preprocessing order or too many components | Use PQN → log → Pareto first; reduce components; verify groups are balanced. |
| `None of the hit metabolite names resolve to KEGG` | Feature names cannot map to compound IDs | Provide `mass_db`, KEGG IDs, or a curated name mapping before `msea_ora` / `msea_gsea`. |
| KEGG/HMDB/ChEBI/LION fetch failure | Network/cache unavailable | Pass local `pathways` or `mass_db`; ask before enabling remote fetchers. |
| Lipid parser error | `pygoslin` not installed or lipid names unsupported | Install `omicverse[lipidomics]` or use generic metabolomics paths without lipid-specific parsing. |
| Lipidomics functions raise `pylipidr` missing | Optional lipidr bridge absent | Install `omicverse[lipidomics]` for `read_skyline`, `normalize_pqn`, `de_lipids`, `lsea`, and `lipid_mva`. |

## Proteomics

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `No columns match sample_pattern` in `read_maxquant` | Intensity column prefix differs | Pass a regex matching the source file, such as `sample_pattern=r"Intensity (.+)"`. |
| Too many proteins dropped by `qc_filter` | `min_peptides` or `min_valid` too strict, or metadata column missing | Inspect missingness and peptide-count distributions; lower thresholds or choose the correct `peptides_col`. |
| `method='equalize_medians' requires pydeqms` | Optional DEqMS backend absent | Install `pydeqms` or use `normalize(method="median")`. |
| `method='deqms' requires pydeqms` | DEqMS backend absent | Install `omicverse[protein]` or switch to `method="limma"`, `"welch_t"`, or `"wilcoxon"`. |
| DEqMS variance fit fails for every fit method | Peptide-count column degenerate or too few distinct counts | Use `method="limma"` for count-free moderated t or provide a better count variable. |
| `method='proda'` import error | `pyproda` absent | Install `omicverse[protein]` or use a non-proDA method. |
| `model_selector` / QRILC import error | `pyimputelcmd` absent | Install `pyimputelcmd` or use simpler imputation such as `half_min` when scientifically acceptable. |
| Olink NPX becomes NaN after normalization | NPX is already log-scale and may contain negative values | Call `ov.protein.normalize(adata, method="log2", log2=False)` or skip log2 transform. |
| Two-group method rejects three groups | Pairwise method used with >2 groups | Use `method="anova"` or `"kruskal"`, or subset/contrast groups explicitly. |

## Microbiome

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `scikit-bio` import error | Diversity/ANCOM-BC backend missing | Install `scikit-bio` for `Alpha`, `Beta`, `Ordinate.pcoa`, and `DA.ancombc`, or use non-skbio routes where possible. |
| Auto rarefaction depth is 0 | At least one sample has zero total counts | Filter empty samples or pass a positive explicit `rarefy_depth`. |
| UniFrac or Faith PD asks for a tree | Missing `adata.uns['tree']` or taxa mismatch | Store a Newick tree at `uns['tree']` and ensure tree tips match `adata.var_names`. |
| `rank ... not in adata.var columns` | Requested taxonomy rank absent | Add taxonomy columns or run at ASV/OTU level with `rank=None`. |
| `group_key not in adata.obs` | Wrong group metadata name | Inspect `adata.obs.columns` and pass the correct column. |
| DESeq2 DA import error | `pydeseq2` absent | Install `pydeseq2` or use `DA.wilcoxon` / `DA.ancombc`. |
| ANCOM-BC unsupported shape | Installed scikit-bio changed return format | Pin a supported scikit-bio version or inspect and adapt result parsing before relying on it. |
| `paired_spearman` rejects `obs_names` | Microbe and metabolite samples are misaligned | Intersect/reindex both AnnData objects to identical `obs_names` in the same order. |
| MMvec is slow or fails on Torch | Torch missing or hardware/backend mismatch | Use `paired_spearman` or `paired_cca` unless the user explicitly needs MMvec embeddings. |

## Network and Cache Caveats

- Metabolomics KEGG/HMDB/ChEBI/LION fetchers can require network access and may write caches. Ask before using them in restricted environments.
- Dataset/tutorial fetchers may download sizable public files. Prefer local fixtures or user-provided tables for verification.
- Do not run native examples, notebooks, or remote fetchers by default in a skill-consuming task; use local schema checks and small synthetic data first.

## Quick Triage Commands

```bash
python sub-skills/multiomics-statistics/scripts/check_multiomics_table.py matrix.tsv --metadata metadata.tsv --sample-id-column sample --required-metadata-cols group
```

```python
print(adata.shape)
print(adata.obs.columns.tolist())
print(adata.var.columns.tolist())
print(adata.obs_names[:5].tolist(), adata.var_names[:5].tolist())
```

```python
# Signature overlap check
signature_genes = set().union(*[set(v.keys() if isinstance(v, dict) else v) for v in signatures.values()])
overlap = signature_genes & set(map(str, adata.var_names))
print(len(overlap), "overlapping signature genes")
```
