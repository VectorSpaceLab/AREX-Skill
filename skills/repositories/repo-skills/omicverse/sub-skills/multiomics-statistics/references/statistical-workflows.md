# Statistical Workflows

This reference turns table-centric OmicVerse tasks into reproducible local workflows. Use [`data-formats.md`](data-formats.md) first when sample IDs, matrix orientation, or design metadata are uncertain.

## Bulk RNA-seq Differential Expression

Use `ov.bulk.pyDEG` for genes-by-samples matrices. Inputs are typically raw counts for count-aware methods or already normalized/log-scaled values for continuous methods.

```python
import omicverse as ov

# counts: pandas.DataFrame with genes as index and sample IDs as columns
dds = ov.bulk.pyDEG(counts)
dds.drop_duplicates_index()
result = dds.deg_analysis(
    group1=["case_1", "case_2", "case_3"],
    group2=["ctrl_1", "ctrl_2", "ctrl_3"],
    method="edger",       # common local choices: "edger", "limma"; pydeseq2 routes need pydeseq2
    alpha=0.05,
)
```

Validation checkpoints:

- Matrix index is unique gene IDs or symbols; columns are unique sample IDs.
- `group1` and `group2` names exactly match matrix columns.
- Count-based methods should receive nonnegative count-like data; log-scale or negative values should use methods designed for continuous data.
- Standard `pyDEG` outputs include `pvalue`, `qvalue`, `log2FC`, `abs(log2FC)`, `BaseMean`, `-log(pvalue)`, `-log(qvalue)`, and `sig`.

## Bulk ORA and GSEA

Use the offline dict-backed ORA/GSEA paths when possible; avoid assuming remote gene-set catalogs are available.

```python
pathways = {
    "IFN_RESPONSE": ["ISG15", "IFI6", "MX1"],
    "INFLAMMATION": ["IL6", "TNF", "CXCL8"],
}
ora = ov.bulk.geneset_enrichment(
    gene_list=significant_genes,
    pathways_dict=pathways,
    pvalue_threshold=0.05,
    pvalue_type="auto",
    background=all_tested_genes,
)

gsea = ov.bulk.geneset_enrichment_GSEA(
    gene_rnk=ranked_genes,      # DataFrame/Series with gene and score/rank
    pathways_dict=pathways,
    backend="numpy",
    permutation_num=1000,
    seed=112,
)
```

Expected signals:

- ORA result tables contain `P-value`, `Adjusted P-value`, `Odds Ratio`, `Combined Score`, `Genes`, plus OmicVerse post-processing such as `logp` and `fraction`.
- `logp` is `-log10(P-value or adjusted P-value)`, not natural log.
- The NumPy GSEA backend is deterministic for a fixed `seed` and returns GSEA-style fields such as `es`, `nes`, `pval`, `fdr`, and hit traces.

## Enrichment and Signature Scoring with `ov.es`

Use `ov.es` when the task is scoring signatures in an AnnData or expression DataFrame rather than testing a ranked list.

```python
signatures = {
    "HALLMARK_IFN": ["ISG15", "IFI6", "MX1"],
    "NFKB_REGULON": {"TNF": 1.0, "IL6": 1.0, "IL10": -1.0},
}

ov.es.aucell(adata, signatures=signatures, tmin=3, engine="auto")
ov.es.ucell(adata, signatures=signatures, max_rank=1500, key_added="score_ucell")
ov.es.ora(adata, signatures=signatures, tmin=3, engine="auto")

scores = ov.es.decouple(
    adata,
    signatures=signatures,
    methods=["aucell", "ora", "ulm"],
    cons=False,
)
consensus = ov.es.consensus(scores)
```

Checklist:

- Gene identifiers in `adata.var_names` or DataFrame columns must match signature targets.
- Dict signatures may be `{signature: [genes]}` or `{signature: {gene: weight}}`; signed/weighted regulons need the second form.
- Long network DataFrames must contain `source`, `target`, and `weight` columns.
- Per-method scores are written to `adata.obsm['score_<method>']`; methods with p-values also write `adata.obsm['padj_<method>']`.
- `engine="gpu"` needs a compatible Torch/CUDA stack; `engine="cpu"` is safer for portable verification.

## Metabolomics

Generic targeted or untargeted tables are read into samples-by-metabolites AnnData.

```python
adata = ov.metabol.read_wide(
    "peak_table.tsv",
    sep="\t",
    sample_col="sample",
    group_col="group",
)
# or MetaboAnalyst-style CSV where group_col is required
adata = ov.metabol.read_metaboanalyst("metabo.csv", group_col="Muscle loss")

adata = ov.metabol.normalize(adata, method="pqn")
adata = ov.metabol.transform(adata, method="log")
deg = ov.metabol.differential(
    adata,
    group_col="group",
    group_a="case",
    group_b="control",
    method="welch_t",
    log_transformed=True,
)
pls = ov.metabol.plsda(adata, group_col="group", n_components=2)
```

Common QC and model routes:

- `ov.metabol.cv_filter(adata, qc_mask="is_qc", cv_threshold=0.30)` keeps features stable in pooled QC samples; use `across="all"` when there are no QC pools.
- `ov.metabol.drift_correct(adata, injection_order="run_order", qc_mask="is_qc")` corrects instrument drift and warns when real samples are outside the QC range.
- `ov.metabol.blank_filter(adata, blank_mask="is_blank", ratio=3.0)` removes features close to blank intensity.
- `ov.metabol.sample_qc(adata, n_components=2, alpha=0.95)` returns Hotelling T² / DModX sample outlier diagnostics.
- `ov.metabol.msea_ora(hits, background, pathways=None, mass_db=None)` and `ov.metabol.msea_gsea(deg, stat_col="stat", mass_db=None)` use KEGG compound mappings; pass local `pathways` or `mass_db` when network access is not allowed.
- `ov.metabol.biomarker_panel(adata, group_col="group", features=10, classifier="rf")` performs nested-CV biomarker-panel evaluation.
- Multi-factor/time-series routes include `ov.metabol.asca`, `ov.metabol.mixed_model`, and `ov.metabol.meba` when design metadata includes factors, random groups, time, and subject IDs.

## Proteomics

Proteomics readers also return samples-by-proteins AnnData, usually with raw intensities in `X` and protein metadata in `var`.

```python
adata = ov.protein.read_maxquant(
    "proteinGroups.txt",
    sample_pattern=r"LFQ intensity (.+)",
)
ov.protein.qc_filter(adata, min_peptides=2, min_valid=0.5)
ov.protein.normalize(adata, method="median", log2=True)
ov.protein.impute(adata, method="qrilc", seed=0)
res = ov.protein.de(
    adata,
    group="condition",
    method="deqms",
    count_var="peptides",
)
```

Reader choices:

- `read_maxquant` parses MaxQuant `proteinGroups.txt` and drops reverse, contaminant, and only-site rows by default.
- `read_diann`, `read_fragpipe`, and `read_olink_npx` handle DIA-NN, FragPipe, and Olink formats.
- `read_wide` is the fallback for plain samples-by-proteins intensity tables.

Analysis choices:

- `normalize(method="median")` is the LFQ default; `method="quantile"`, `"equalize_medians"`, and `"log2"` are alternatives.
- `impute(method="qrilc")` is appropriate for MNAR/left-censored proteomics; `half_min`, `zero`, `knn`, `mle`, `svd`, `mar`, `mar_mnar`, and `auto` are available when their backends are installed.
- `de(method="deqms")` uses peptide counts; `method="limma"`, `"wilcoxon"`, and `"welch_t"` are useful fallbacks; `"anova"` and `"kruskal"` handle multi-group omnibus tests.
- Expected DE columns include `gene`, `logFC`, `P.Value`, and `adj.P.Val`; backend-specific columns such as peptide count or proDA parameters may also appear.

## Microbiome

Microbiome workflows use samples-by-taxa AnnData with count-like `X`, sample metadata in `obs`, and optional taxonomy in `var`.

```python
alpha = ov.micro.Alpha(adata, rarefy_depth=10000).run(
    metrics=["shannon", "observed_otus"],
)
dm = ov.micro.Beta(adata).run(metric="braycurtis", rarefy=True)
coords = ov.micro.Ordinate(adata, dist_key="braycurtis").pcoa(n=3)
da = ov.micro.DA(adata).wilcoxon(
    group_key="group",
    group_a="control",
    group_b="case",
    rank="genus",
)
```

Additional routes:

- `ov.micro.rarefy(adata, depth=None, save_original=True)` stores original counts in `layers['counts_raw']` and rarefies to a common depth.
- `ov.micro.collapse_taxa(adata, rank="genus")` aggregates ASV/OTU counts to a taxonomy rank.
- `ov.micro.DA(adata).deseq2(...)` uses `pydeseq2` for count-based differential abundance.
- `ov.micro.DA(adata).ancombc(...)` uses scikit-bio ANCOM-BC for compositional differential abundance.
- `ov.micro.combine_studies` and `ov.micro.meta_da` combine multi-cohort studies and report fixed/random-effects statistics.
- Paired microbe-metabolite routes include `simulate_paired`, `paired_spearman`, `paired_cca`, and `MMvec` when the sample axes are aligned.

## Visualization Handoffs

- For volcano plots, use metabolomics/proteomics-specific plot helpers when the result schema matches (`log2fc`/`padj` for metabolomics; `logFC`/`adj.P.Val` for proteomics).
- For heatmaps and enrichment boards, preserve row labels and `-log10` transformed p-value columns.
- For ordination, store coordinates in `adata.obsm` and variance/stress in `adata.uns` before handing off to plotting utilities.
- For general OmicVerse plotting conventions, route to [`../../core-analysis/references/core-workflows.md`](../../core-analysis/references/core-workflows.md).
