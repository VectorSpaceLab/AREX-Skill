# API Reference

Import convention:

```python
import omicverse as ov
```

## `ov.genetics`

| Function | Purpose | Key parameters | Returns / writes |
| --- | --- | --- | --- |
| `read_sumstats(path, sep=None, rename=True, nrows=None, **kwargs)` | Read summary statistics and canonicalize column names | `sep`, `rename`, `nrows` | `pandas.DataFrame`; `.attrs['sumstats_columns']` maps canonical names to source names |
| `read_plink(prefix)` | Read PLINK `.bed/.bim/.fam` trio | `prefix` without extension | Genotype object/data for samples × SNPs |
| `read_vcf(path, max_variants=None)` | Read VCF genotype records | `max_variants` for bounded load | Variant/genotype data |
| `gwas_qc(adata, call_rate=0.95, maf=0.01, hwe=1e-6, sample_call_rate=0.95, copy=True)` | Filter genotype AnnData | `AnnData.X` dosages 0/1/2, `NaN` missing | Filtered AnnData with SNP/sample QC columns and `uns['gwas_qc']` |
| `gwas_association(genotype, phenotype, covariates=None, model='linear')` | Per-SNP association scan | `model='linear'` or `'logistic'` | DataFrame with `snp`, `beta`, `se`, `stat`, `pvalue`, `n` |
| `genomic_inflation(results, p_col='pvalue')` | Inflation factor from GWAS p-values | p-value column | Lambda/summary statistics |
| `eqtl_map(genotype, expression, covariates=None, snp_pos=None, gene_pos=None, model='linear', cis_dist=1000000.0, pv_threshold=1e-5, pv_threshold_cis=0.0, ...)` | Matrix eQTL mapping | genotype/expression matrices or file paths; optional positions | eQTL results from backend |
| `finemap(X=None, y=None, method='susie_rss', z=None, R=None, n=None, bhat=None, shat=None, L=10, coverage=0.95, min_abs_corr=0.5, max_iter=100, **kwargs)` | SuSiE fine-mapping | individual-level `X/y` or summary `z/R/n` | Fine-mapping fit |
| `get_credible_sets(fit, X=None, R=None, coverage=0.95, min_abs_corr=0.5, **kwargs)` | Extract credible sets | SuSiE fit and LD info | Credible-set table/object |
| `get_pip(fit, prune_by_cs=False, **kwargs)` | Extract posterior inclusion probabilities | SuSiE fit | PIP vector |
| `make_coloc_dataset(stats, snps, n, maf, beta='beta', se='se', trait_type='quant', sdY=1.0)` | Build coloc dataset dict | aligned variants, sample size, MAF | Dict for `colocalize` |
| `colocalize(dataset1, dataset2, method='abf', MAF=None, p1=1e-4, p2=1e-4, p12=1e-5, **kwargs)` | Colocalization | shared variants; optional prior settings | Coloc backend result |
| `coloc_scan(gwas, eqtl, n_gwas, n_eqtl, gene_col='gene', variant_col='variant', ..., min_shared=20)` | Scan GWAS against eQTL genes | shared variant identifiers and effect columns | Ranked coloc scan results |
| `harmonize(exposure, outcome, tolerance=0.08, action=2)` | Align exposure/outcome alleles for MR | `SNP`, `beta`, `se`, `effect_allele`, `other_allele`; optional `eaf` | Harmonized DataFrame |
| `mendelian_randomization(mr_input_or_dataframes=None, method='ivw', bx=None, bxse=None, by=None, byse=None, snps=None, n=None, **kwargs)` | Two-sample MR | `ivw`, `egger`, `median`, `mode`, `maxlik`, `divw`, `conmix`, `lasso`, `cml`, `all` | MR result or comparison DataFrame |
| `disease_relevance_score(adata, gene_set, gene_weight=None, cov=None, n_ctrl=1000, random_seed=0, copy=False, return_raw=False, ...)` | scDRS disease relevance | AnnData and gene set | AnnData annotations or result table |

Optional backend extras: install `omicverse[genetics]` for `pymatrixeqtl`, `pysusie`, `pycoloc`, `pytwosamplemr`, `pyscdrs`, `pyldsc`, and `pytwas`. The core GWAS reader/QC/association functions are backend-light.

## `ov.airr`

| Function | Purpose | Key parameters | Returns / writes |
| --- | --- | --- | --- |
| `airr_obs_columns()` | List OmicVerse per-cell AIRR columns | none | Ordered column-name list |
| `read_10x_vdj(path)` | Read 10x Cell Ranger V(D)J output | `filtered_contig_annotations.csv` or `airr_rearrangement.tsv` | AnnData with AIRR fields in `obs` and raw contigs in `uns['airr_contigs']` |
| `read_airr(path)` | Read AIRR rearrangement TSV(s) | path or paths | AnnData AIRR schema |
| `read_tracer(data, column_map=None)` | Read per-contig table with optional column map | DataFrame/path | AnnData AIRR schema |
| `from_airr_array(adata, airr_key='airr')` | Convert scirpy-style `obsm['airr']` | source AnnData | OmicVerse AIRR schema |
| `simulate_airr(n_cells=300, n_clones=40, receptor='TCR', seed=0)` | Synthetic AIRR AnnData | receptor and size | AnnData for testing/tutorials |
| `chain_qc(adata, inplace=True)` | Classify receptor chain configuration | AIRR `obs` slots | Adds chain QC columns or returns DataFrame |
| `define_clonotypes(adata, sequence='aa', key_added='clone_id')` | Exact-identity clonotypes | `sequence='aa'` or nucleotide flavor | Adds `obs[key_added]` |
| `define_clonotype_clusters(...)` | Distance-based clonotype clusters | sequence/distance settings | Adds cluster labels |
| `clonal_expansion(adata, target_col='clone_id', clip_at=4, key_added='clonal_expansion')` | Clone-size categories | integer or ascending bin list | Ordered categorical `obs[key_added]` |
| `alpha_diversity(adata, groupby=None, target_col='clone_id', metric='shannon')` | Diversity by group | `shannon`, and supported metrics | DataFrame/Series |
| `repertoire_overlap(adata, groupby, target_col='clone_id', metric='jaccard')` | Pairwise overlap | `groupby`, metric | Matrix/DataFrame |
| `vdj_usage(adata, gene='v', chain='VDJ_1', groupby=None, normalize=True)` | V/D/J usage | chain slot and group | Usage table |
| `tcrdist`, `tcr_neighbors`, `tcr_cluster` | TCR distance and clustering | CDR3/V gene fields | Distance matrix/clusters |
| `annotate_antigen`, `specificity_groups` | TCR antigen/specificity analysis | clean CDR3 and reference DB | Annotation/group tables |
| `conga_score`, `conga_clusters`, `tcr_clumping`, `hotspot_features` | Joint TCR + GEX analysis | TCR AIRR data plus expression/neighborhoods | Scores/clusters/features |

Optional `omicverse[airr]` backends add bulk repertoire and B-cell analysis: `repertoire_diversity`, `repertoire_overlap_bulk`, `gene_usage_bulk`, `clonality`, `public_clonotypes`, `track_clonotypes`, `clonal_clustering`, `mutation_analysis`, `lineage_trees`, `infer_genotype`, and related functions.

## `ov.alignment`

| Function | Purpose | Side effects / controls |
| --- | --- | --- |
| `prefetch(sra_ids, output_dir='prefetch', validate=True, prefetch_path=None, vdb_validate_path=None, auto_install=True, ...)` | Download SRA accessions and validate | Network, SRA toolkit, optional auto-install; set `auto_install=False` unless approved |
| `fqdump(sra_ids, output_dir='fastq', gzip=False, library_layout='auto', fasterq_path=None, auto_install=True, ...)` | Convert SRA to FASTQ | Runs `fasterq-dump`; writes FASTQs |
| `fastp(samples, output_dir='fastp', fastp_path=None, auto_install=True, overwrite=False, ...)` | FASTQ QC/trimming | Runs `fastp`; writes trimmed reads/reports |
| `STAR(samples, genome_dir, output_dir='star', gtf=None, auto_index=True, genome_fasta_files=None, star_path=None, auto_install=True, overwrite=False, ...)` | STAR alignment and optional index generation | Runs STAR; may build index; use explicit `star_path` and `auto_index=False` for existing indexes |
| `featureCount(bam_items, gtf, output_dir='counts', simple=True, merge_matrix=True, featurecounts_path=None, auto_install=True, strict=False, auto_fix=True, ...)` | Count reads from BAMs | Runs `featureCounts`; writes counts and optional merged matrix |
| `bulk_rnaseq_pipeline(sra_ids=None, samples=None, genome_dir='star_index', gtf='genes.gtf', output_dir='pipeline_output', skip_download=False, skip_qc=False, auto_install=True, ...)` | End-to-end SRA/local FASTQ bulk RNA-seq | Chains download, conversion, QC, STAR, featureCounts |
| `ref(index_path, t2g_path, fasta_paths=None, gtf_paths=None, workflow='standard', threads=8, overwrite=False, ...)` | Build kallisto/kb reference | Runs `kb ref`; writes index and transcript-to-gene map |
| `count(index_path, t2g_path, technology, fastq_paths, output_path='.', workflow='standard', h5ad=False, report=False, ...)` | kb-python quantification | Runs `kb count`; writes matrices/reports |
| `simpleaf_index(output, fasta=None, gtf=None, rlen=91, ref_type='spliced+intronic', simpleaf_bin=None, alevin_fry_home=None, dry_run=False, ...)` | Build simpleaf splici index | Use `dry_run=True`; writes index |
| `simpleaf_count(index, reads1, reads2, t2g_map, output='.', chemistry='10xv3', anndata_out=False, dry_run=False, ...)` | simpleaf/alevin-fry quantification | Use `dry_run=True`; writes quant output and optional `.h5ad` |
| `simpleaf_pipeline(fasta, gtf, reads1, reads2, index_output='af_index', quant_output='af_quant_out', ...)` | Build index then quantify | Runs index + count; gate side effects |
| `cutadapt(...)`, `vsearch.merge_pairs`, `vsearch.filter_quality`, `vsearch.dereplicate`, `vsearch.unoise3`, `vsearch.uchime3_denovo`, `vsearch.sintax`, `vsearch.usearch_global` | 16S command wrappers | Run external CLIs and write intermediate files |
| `amplicon_16s_pipeline(fastq_dir=None, samples=None, workdir=None, db_fasta=None, backend='vsearch', ...)` | End-to-end amplicon pipeline | Requires `workdir`; can use `vsearch` or `dada2`; writes ASV/taxonomy output |
| `dada2_pipeline(samples, workdir=None, db_fasta=None, trunc_len=(240,160), max_ee=(2.0,2.0), ...)` | pydada2 end-to-end | Requires non-empty samples and workdir |
| `build_amplicon_anndata(otutab_tsv, asv_fasta, sintax_tsv=None, sample_metadata=None, sample_order=None)` | Convert ASV table to AnnData | Pure parser; reads local files only |
| `fetch_sintax_ref(source='rdp_16s_v18', db_dir=None, overwrite=False, timeout=...)`, `fetch_silva`, `fetch_rdp` | Download 16S reference databases | Network; explicit `db_dir` or configured DB dir required |
| `mafft`, `fasttree`, `build_phylogeny` | MSA and tree inference | External binaries; validate mode/model/workdir first |

## `ov.mol`

| Function | Purpose | Key parameters | Returns / notes |
| --- | --- | --- | --- |
| `fetch_structure(query, source='auto', taxon=9606, dir='./data', verbose=False)` | Fetch AlphaFold or PDB structure | gene symbol, UniProt, or PDB ID; output cache dir | `MolStructure`; network-backed |
| `predict_structure(sequence, engine='esmfold', name=None, dir='./data', timeout=300, verbose=False)` | Predict structure from amino-acid sequence | raw sequence; timeout | `MolStructure`; network/API-backed |
| `view(structure, style='cartoon', color_by='pLDDT', ...)` | Interactive 3D view | color by chain/pLDDT/array/mapping | py3Dmol view object |
| `plot_pae(structure, ax=None, cmap='Greens_r')` | PAE heatmap | AlphaFold PAE expected | Matplotlib axes |
| `known_drugs(target, organism='Homo sapiens', max_phase=None, only_mechanism=False, max_records=300)` | ChEMBL drugs/bioactivities | target gene/protein | DataFrame; network-backed |
| `pockets(structure, min_drug_score=0.0, sort_by='drug_score')` | Binding pocket detection | pocket backend required | DataFrame with pocket scores |
| `druggability(structure)` | Structure druggability verdict | pockets computed or computable | Dict verdict and pocket summary |
| `dock(structure, ligand, pocket=None, box=None, exhaustiveness=8, n_poses=9, seed=0, verbose=False)` | AutoDock Vina docking | ligand SMILES/file/mol; explicit pocket or box recommended | `DockingResult` |
| `redock_validate(structure, ref_ligand=None, exhaustiveness=8, seed=0, verbose=False)` | Redocking validation | experimental ligand or extracted ligand | Validation result |

Optional molecular extras: `omicverse[mol]` for py3Dmol/biotite/ChEMBL/requests on Python >=3.10; `omicverse[mol-dock]` for RDKit, Vina, Meeko, and Gemmi. Pocket detection uses `fpocket-rs` separately.
