# Specialist Workflows

This reference covers non-core OmicVerse domains that often need stricter input validation and explicit side-effect control than ordinary AnnData workflows.

## Genetics and Post-GWAS

Use `omicverse.genetics` for summary statistics, genotype matrices, post-GWAS interpretation, and single-cell disease-relevance scoring.

### Typical Flow

1. Load summary statistics with `ov.genetics.read_sumstats(path, sep=None, rename=True, nrows=None)`. With `rename=True`, aliases are mapped to canonical columns such as `SNP`, `CHR`, `BP`, `A1`, `A2`, `BETA`, `SE`, `OR`, `Z`, `P`, `N`, `EAF`, and `INFO`.
2. For genotype-level analysis, load or construct samples × SNPs data. `gwas_qc(adata, call_rate=0.95, maf=0.01, hwe=1e-6, sample_call_rate=0.95)` expects `AnnData.X` as 0/1/2 dosages with `NaN` for missing calls and returns filtered AnnData with `var['call_rate']`, `var['maf']`, `var['hwe_p']`, `obs['sample_call_rate']`, and `uns['gwas_qc']`.
3. Run `gwas_association(genotype, phenotype, covariates=None, model='linear')` for quantitative traits or `model='logistic'` for binary traits. Outputs include `snp`, `beta`, `se`, `stat`, `pvalue`, and `n`.
4. Use backend-gated post-GWAS functions only after confirming `omicverse[genetics]` dependencies: `eqtl_map`, `finemap`, `colocalize`, `mendelian_randomization`, `disease_relevance_score`, LDSC, and TWAS.
5. For coloc or MR, harmonize variants and alleles before interpretation. Prefer shared `SNP`/variant identifiers, explicit `A1`/`A2` or `effect_allele`/`other_allele`, aligned effect signs, and documented sample sizes.

### Coloc and MR Pattern

- Build coloc input with `make_coloc_dataset(stats, snps=..., n=..., maf=..., beta='beta', se='se', trait_type='quant', sdY=1.0)` or use `coloc_scan(gwas, eqtl, n_gwas=..., n_eqtl=..., min_shared=20)` when scanning many genes.
- Call `colocalize(dataset1, dataset2, method='abf', MAF=None, p1=1e-4, p2=1e-4, p12=1e-5)` after verifying the same variants are represented in both traits.
- Prepare MR with `harmonize(exposure, outcome, tolerance=0.08, action=2)`. Required harmonization columns are `SNP`, `beta`, `se`, `effect_allele`, `other_allele`, with `eaf` recommended for palindromic alleles.
- Run `mendelian_randomization(..., method='ivw')`; supported estimator selectors include `ivw`, `egger`, `median`, `mode`, `maxlik`, `divw`, `conmix`, `lasso`, `cml`, and `all`. `method='cml'` requires `n`.

## AIRR Immune Repertoire

Use `omicverse.airr` for single-cell V(D)J/TCR/BCR workflows and optional bulk repertoire/B-cell backends.

### Single-Cell AIRR Flow

1. Read data with `read_10x_vdj(path)` for `filtered_contig_annotations.csv` or `airr_rearrangement.tsv`, `read_airr(path)` for AIRR rearrangement TSV, `read_tracer(data, column_map=None)`, or `from_airr_array(adata, airr_key='airr')` for scirpy-style data.
2. Confirm `adata.obs` contains AIRR chain slots. OmicVerse stores receptor data in columns such as `VJ_1_v_gene`, `VJ_1_j_gene`, `VJ_1_junction_aa`, `VJ_1_locus`, `VDJ_1_v_gene`, `VDJ_1_d_gene`, `VDJ_1_junction_aa`, `VDJ_1_locus`, plus `has_ir` and `receptor_type`.
3. Run `chain_qc(adata, inplace=True)` to classify receptor chain configuration.
4. Run `define_clonotypes(adata, sequence='aa', key_added='clone_id')` before clone-size metrics.
5. Run `clonal_expansion(adata, target_col='clone_id', clip_at=4, key_added='clonal_expansion')`. Integer `clip_at=4` yields categories `1 (single)`, `2`, `3`, and `>= 4`; custom ascending bins such as `[1, 5, 10, 50, 100]` produce ordered range labels.
6. Use `alpha_diversity`, `repertoire_overlap(groupby=...)`, `vdj_usage`, and plotting helpers for summaries.

### AIRR Bulk and TCR/BCR Backends

- `omicverse[airr]` adds optional R-parity packages for bulk repertoire diversity/overlap/gene usage, Immcantation B-cell workflows, GLIPH-style specificity, and B-cell phylogenetics.
- Bulk functions accept AIRR-format `pandas.DataFrame` data or backend-specific containers rather than forcing AnnData.
- TCR specificity functions such as `tcrdist`, `tcr_neighbors`, `tcr_cluster`, `giana_cluster`, `clustcr_cluster`, `specificity_groups`, and `annotate_antigen` depend on CDR3 and V/J gene columns being clean and comparable.

## Raw Sequencing, Alignment, and Amplicon Pipelines

Use `omicverse.alignment` for wrappers around SRA toolkit, fastp, STAR, featureCounts, kb-python, simpleaf/alevin-fry, cutadapt, vsearch, pydada2, MAFFT, and FastTree.

### Side-Effect Policy

Many wrappers execute external commands, write output trees, and default to `auto_install=True` for missing tools. Before running them:

- Ask the user whether downloads, installs, and external binaries are allowed.
- Prefer explicit binary overrides such as `prefetch_path`, `vdb_validate_path`, `fasterq_path`, `fastp_path`, `star_path`, `featurecounts_path`, or `simpleaf_bin`.
- For wrappers that expose `dry_run` (`simpleaf_index`, `simpleaf_count`), use it first to inspect the command.
- Use isolated output directories and set `overwrite=False` unless replacement is intended.

### SRA-to-Counts Pattern

1. Download SRA with `prefetch(sra_ids, output_dir='prefetch', validate=True, auto_install=False, prefetch_path=..., vdb_validate_path=...)` only after network approval.
2. Convert to FASTQ with `fqdump(sra_ids, output_dir='fastq', gzip=False, library_layout='auto', auto_install=False, fasterq_path=...)`.
3. QC FASTQs with `fastp(samples, output_dir='fastp', fastp_path=..., auto_install=False)`.
4. Align with `STAR(samples, genome_dir, output_dir='star', gtf=..., auto_index=False, star_path=..., auto_install=False)` unless the user explicitly wants index creation. If `auto_index=True`, `genome_fasta_files` and `gtf` may be used to generate a STAR index.
5. Count BAMs with `featureCount(bam_items, gtf, output_dir='counts', featurecounts_path=..., auto_install=False, merge_matrix=True)`.
6. `bulk_rnaseq_pipeline(...)` chains these steps; use it only when the user has approved every side effect and provided references/output policy.

### kb-python and simpleaf Pattern

- Build reference with `ref(index_path, t2g_path, fasta_paths=None, gtf_paths=None, workflow='standard', threads=8, overwrite=False, ...)`.
- Count reads with `count(index_path, t2g_path, technology, fastq_paths, output_path='.', workflow='standard', h5ad=False, report=False, ...)`.
- Build splici index with `simpleaf_index(output, fasta=None, gtf=None, rlen=91, ref_type='spliced+intronic', simpleaf_bin=None, alevin_fry_home=None, dry_run=False, ...)`.
- Quantify with `simpleaf_count(index, reads1, reads2, t2g_map, output='.', chemistry='10xv3', anndata_out=False, dry_run=False, ...)`.
- `simpleaf_pipeline(fasta, gtf, reads1, reads2, index_output='af_index', quant_output='af_quant_out', ...)` chains index and count.

### 16S and Phylogeny Pattern

- `amplicon_16s_pipeline(fastq_dir=None, samples=None, workdir=None, db_fasta=None, primer_fwd=None, primer_rev=None, backend='vsearch', ...)` discovers or accepts sample tuples `(sample, R1, R2_or_None)` and returns an AnnData-like ASV workflow result. `primer_rev` without `primer_fwd` is invalid, unsafe sample names are rejected, and `backend='dada2'` is accepted.
- `dada2_pipeline(samples, workdir, db_fasta=None, trunc_len=(240, 160), max_ee=(2.0, 2.0), ...)` requires non-empty samples and an explicit workdir.
- `build_amplicon_anndata(otutab_tsv, asv_fasta, sintax_tsv=None, sample_metadata=None, sample_order=None)` produces sample × ASV AnnData with sparse integer counts, `var['sequence']`, taxonomy columns, and merged sample metadata.
- `fetch_sintax_ref`, `fetch_silva`, and `fetch_rdp` download taxonomy references; never call them without network approval and an explicit database directory.
- `mafft`, `fasttree`, and `build_phylogeny` wrap external CLIs. Validate mode/model parameters and binary availability first.

## Molecular Structure and Drug Binding

Use `omicverse.mol` when a user wants to move from a gene/protein/drug candidate to 3D structure, druggability, known drugs, or docking.

### Safe Molecular Flow

1. Validate the target query. `fetch_structure(query, source='auto', taxon=9606, dir='./data', verbose=False)` accepts a gene symbol, UniProt accession, or PDB ID; `source='pdb'` avoids AlphaFold/UniProt ambiguity for 4-character PDB IDs.
2. Ask before network calls. `fetch_structure`, `predict_structure(sequence, engine='esmfold', timeout=300)`, and `known_drugs(target, organism='Homo sapiens', max_records=300)` use remote services.
3. Inspect structure confidence before docking. `MolStructure` exposes residue-level confidence fields when available; `plot_pae` visualizes predicted aligned error for AlphaFold models.
4. Use `pockets(structure, min_drug_score=0.0, sort_by='drug_score')` and `druggability(structure)` only when pocket backends are installed.
5. Use `dock(structure, ligand, pocket=None, box=None, exhaustiveness=8, n_poses=9, seed=0)` only after confirming Python >=3.10 and docking extras (`rdkit`, `vina`, `meeko`, `gemmi`) are available. Prefer an explicit `box` or validated `pocket` over blind docking for large proteins.
6. Use `redock_validate(structure, ref_ligand=None, exhaustiveness=8, seed=0)` to sanity-check a docking protocol when an experimental ligand is available.

### Molecular Output Expectations

- `fetch_structure` returns a `MolStructure` with source metadata, sequence/residue information, and optional pLDDT/PAE.
- `known_drugs` returns a drug/bioactivity table from ChEMBL.
- `pockets` returns a DataFrame with identifiers and scores such as `pocket_id`, `rank`, `drug_score`, and `volume`.
- `dock` returns a `DockingResult` with poses, affinities, pose blocks, and a best pose.
