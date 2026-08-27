# Data Formats

Use these schemas to validate inputs before running specialist OmicVerse APIs. The bundled `scripts/check_specialist_inputs.py` performs safe checks for the most common cases and never downloads data or invokes external binaries.

## GWAS and Post-GWAS Tables

### Summary Statistics

Recommended canonical columns:

| Column | Meaning | Required for |
| --- | --- | --- |
| `SNP` | Variant identifier such as rsID or `chr:pos:ref:alt` | Most workflows |
| `CHR` | Chromosome | Regional plots, clumping, locus scans |
| `BP` | Base-pair position | Regional plots, clumping, locus scans |
| `A1` | Effect allele | Harmonization, coloc, MR |
| `A2` | Other allele | Harmonization, coloc, MR |
| `BETA` | Effect size | GWAS, eQTL, coloc, MR |
| `SE` | Standard error | coloc, MR, fine-map summaries |
| `OR` | Odds ratio | Binary traits when beta is absent; convert to `log(OR)` for effect-scale workflows |
| `Z` | Z-score | Fine-mapping and some summary workflows |
| `P` | p-value | QC, plots, coloc when effects unavailable |
| `N` | Sample size | coloc, LDSC, MR interpretation |
| `EAF` | Effect allele frequency or MAF | allele checks, palindromic SNP resolution, coloc |
| `INFO` | Imputation quality | summary-stat QC |

`read_sumstats(..., rename=True)` recognizes common lowercase and tool-specific aliases for these fields. If a downstream function expects lowercase names (`beta`, `se`, `maf`, `variant`), rename explicitly and document the mapping.

### Genotype AnnData for GWAS QC

`gwas_qc` expects:

- Shape: samples × SNPs.
- `adata.X`: numeric dosage matrix with values `0`, `1`, `2`, and `NaN` for missing calls.
- `adata.obs_names`: sample identifiers.
- `adata.var_names`: SNP identifiers.
- Optional `adata.var`: `CHR`, `BP`, `A1`, `A2` for downstream locus/allele work.

Outputs include `var['call_rate']`, `var['maf']`, `var['hwe_p']`, `obs['sample_call_rate']`, and `uns['gwas_qc']`.

### eQTL and Coloc Tables

For `eqtl_map`, matrices must share sample order or explicit sample identifiers. Provide genotype, expression, covariates, SNP positions, and gene positions consistently.

For `coloc_scan`, expected default columns are:

- GWAS: `variant`, `BETA`, `SE`, `EAF` plus sample size from `n_gwas`.
- eQTL: `variant`, `gene`, `beta`, `se`, `maf` plus sample size from `n_eqtl`.
- Shared variant count per gene should meet `min_shared`, default `20`.

### MR Harmonization Tables

`harmonize(exposure, outcome)` expects both frames to include:

- `SNP`
- `beta`
- `se`
- `effect_allele`
- `other_allele`
- Optional but strongly recommended: `eaf`

Check for strand-ambiguous palindromic pairs (`A/T`, `T/A`, `C/G`, `G/C`), mismatched effect alleles, duplicated SNPs, and missing standard errors before MR.

## AIRR and V(D)J Data

### 10x V(D)J Contigs

`read_10x_vdj(path)` accepts `filtered_contig_annotations.csv` or `airr_rearrangement.tsv`-style input. Useful source columns include:

- 10x: `barcode`, `chain`, `v_gene`, `d_gene`, `j_gene`, `c_gene`, `cdr3`, `cdr3_nt`, `umis`, `reads`, `productive`.
- AIRR: `cell_id` or `sequence_id`, `locus`, `v_call`, `d_call`, `j_call`, `c_call`, `junction`, `junction_aa`, `duplicate_count`, `productive`.

If `cell_id` is missing in AIRR TSV, OmicVerse can infer it from `sequence_id` prefixes containing `_contig`.

### OmicVerse AIRR AnnData Schema

AIRR receptor fields are stored in `adata.obs`, not in `.obsm`, using chain slots `VJ_1`, `VJ_2`, `VDJ_1`, and `VDJ_2`. Key columns include:

- Global: `has_ir`, `receptor_type`.
- Per-chain slot fields: `{slot}_v_gene`, `{slot}_d_gene`, `{slot}_j_gene`, `{slot}_c_gene`, `{slot}_junction`, `{slot}_junction_aa`, `{slot}_locus`, `{slot}_duplicate_count`, `{slot}_productive`.
- Locus classes: VJ arm uses `TRA`, `TRG`, `IGK`, `IGL`; VDJ arm uses `TRB`, `TRD`, `IGH`.

Common derived columns:

- `chain_pairing` from `chain_qc`.
- `clone_id` from `define_clonotypes`.
- `clonal_expansion` from `clonal_expansion`.

`clonal_expansion` requires the `target_col` to exist; missing `clone_id` raises an error.

## FASTQ and Alignment Inputs

### FASTQ Pair Naming

Accepted paired-end naming should make R1/R2 unambiguous. Standard examples:

- `S1_S10_L001_R1_001.fastq` and `S1_S10_L001_R2_001.fastq`
- `S1_R1.fastq.gz` and `S1_R2.fastq.gz`
- `sample_L001_1.fq.gz` and `sample_L001_2.fq.gz` only when the `_1`/`_2` marker is genuinely the read marker, not part of the sample name

The amplicon sample discovery logic treats an R1-only sample as `(sample, fq1, None)` and rejects empty directories. Unsafe sample names containing path traversal or separators are invalid for pipeline sample tuples.

### SRA Accessions

SRA workflows use accession strings such as `SRR...`, `ERR...`, or `DRR...`. Download/convert functions need explicit output directories and external SRA toolkit binaries when `auto_install=False`.

### STAR and featureCounts Inputs

- STAR samples are tuples `(sample, read1, read2)` or `(sample, read1)` depending on paired/single-end data.
- `genome_dir` must contain an existing STAR index when `auto_index=False`.
- If `auto_index=True`, provide `genome_fasta_files`, `gtf`, and sufficient resources.
- `featureCount` takes BAM items such as `(sample, bam)` or `(sample, bam, paired)` and requires a GTF.
- `featureCount(..., merge_matrix=True)` can produce a merged count matrix; `simple=True` produces simplified per-sample outputs.

### kb-python and simpleaf Inputs

- Reference build needs FASTA and GTF or prebuilt compatible files.
- `count` requires `technology` (for example a 10x chemistry), `index_path`, `t2g_path`, and FASTQ paths.
- `simpleaf_count` separates `reads1` and `reads2`; both can be a string or list and should have the same length for paired data.
- `simpleaf_index` and `simpleaf_count` expose `dry_run=True` for command preview.

## Amplicon and DADA2 Outputs

`build_amplicon_anndata` expects:

- `otutab_tsv`: rows are ASVs/OTUs, columns are samples. A header such as `#OTU ID` is normalized to ASV index.
- `asv_fasta`: FASTA headers may contain `;size=...`; output strips size annotations.
- `sintax_tsv`: optional taxonomy calls with ranks such as domain, phylum, class, order, family, genus, species.
- `sample_metadata`: optional DataFrame indexed by sample IDs.

Output AnnData:

- Shape: samples × ASVs.
- `X`: sparse integer counts.
- `var['sequence']`: ASV sequence.
- Taxonomy columns: `domain`, `phylum`, `class`, `order`, `family`, `genus`, `species`, `taxonomy`, `sintax_confidence`.
- `obs`: merged sample metadata when supplied.

DADA2-derived helper output uses ASV IDs `ASV1`, `ASV2`, ... and the same taxonomy column layout.

## Molecular Target Inputs

### Target Identifiers

- Gene symbol: `EGFR`, `TP53`, `IL6`. Usually requires UniProt/organism resolution and network access.
- UniProt accession: examples include `P00533`, `P01308`, `Q9Y2X7`. Good for AlphaFold DB models.
- PDB ID: four-character IDs such as `1CRN` or `1M17`; use `source='pdb'` when requesting experimental structures.
- Amino-acid sequence: use `predict_structure(sequence, engine='esmfold')` only when network/API use is approved.
- Ligand: SMILES string, ligand file, or RDKit molecule-like object for docking.

### Structure Confidence and Docking Inputs

Before docking:

- Check `MolStructure.source`, sequence length, residue count, pLDDT/PAE if available, and whether a relevant binding region is known.
- Prefer `pocket=<pocket_id>` from `pockets(...)` or an explicit `box=(center, size)`.
- Keep `exhaustiveness` and `n_poses` small for smoke tests; increase only when the user requests production docking.
