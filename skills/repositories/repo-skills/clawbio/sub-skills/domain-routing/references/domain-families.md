# Domain families and composition map

This map is intentionally a routing index, not a method manual. Read the selected skill's `SKILL.md` before execution and preserve its input contract.

## Variant, genotype, and population data

| User signal and shape | Prefer | Status in the catalog snapshot | Disambiguation / next step |
| --- | --- | --- | --- |
| VCF/VCF.GZ, “annotate”, VEP, ClinVar, gnomAD, consequences | `variant-annotation` or `vcf-annotator` guidance | Agent-readable-only | Do not call `clawbio run variant-annotation` unless it becomes registered. Use `acmg` for the clinical-reporting intent when that is the actual requested output. |
| VCF/VCF.GZ or population table, diversity/FST/heterozygosity/representation | `equity` (`equity-scorer`) | Registered | Confirm the VCF is suitable for population metrics and obtain a population map when required. |
| A single rsID or variant association/PheWAS/eQTL request | `gwas` (`gwas-lookup`) | Registered | This is a variant lookup, not bulk VCF annotation. `gwas-region`, `eqtl-region`, `ld-region`, or `locuscompare-region` are narrower registered regional routes when the request names those outputs. |
| Raw 23andMe/AncestryDNA text plus drug/CYP/CPIC intent | `pharmgx` (`pharmgx-reporter`) | Registered | Preserve raw genotype format and reference-build notes. Do not route a generic VCF to PharmGx without confirming its supported genotype fields. |
| VCF plus PRS/polygenic risk intent | `just-prs` or `prs` | Registered | Choose `just-prs` for the VCF/evidence-aware request; choose `prs` when the request and input match the PGS/trait contract. Treat clinical risk language as a safety-sensitive clarification. |
| Unified personal/genomic profile from several completed results | `profile` (`profile-report`) | Registered | Use only after input artifacts and user consent are clear; it is a composition/report route, not a substitute for upstream analyses. |
| CNV/SV or ACMG classification request | `cnv-acmg` or `acmg` | Registered | Inspect whether the input is a CNV call set, a general VCF, or a report request. The names are not interchangeable. |
| WGS/WES FASTQ or tumor-normal variant calling | `sarek-pipeline` (`nfcore-sarek-wrapper`) | Registered | This is an upstream pipeline route. A resulting VCF can hand off to agent-readable variant annotation or registered clinical/reporting routes. |

## Read, alignment, and pipeline data

| User signal and shape | Prefer | Status | Disambiguation / next step |
| --- | --- | --- | --- |
| FASTQ/BAM/CRAM and generic read QC/alignment | `seq-wrangler` guidance | Agent-readable-only | Inspect paired-end structure, read type, reference, and whether the request is bulk RNA, scRNA, or DNA. Use a registered nf-core wrapper when its contract is the intended workflow. |
| Bulk RNA FASTQ plus samplesheet, reference, STAR/Salmon/RSEM/HISAT2 | `rnaseq-pipeline` (`nfcore-rnaseq-wrapper`) | Registered | Produces a count-matrix handoff when the chosen mode supports it; do not route an existing count matrix back through this wrapper. |
| Single-cell/10x FASTQ plus samplesheet, nf-core preprocessing | `scrnaseq-pipeline` (`nfcore-scrnaseq-wrapper`) | Registered | This is preprocessing from reads. Existing `.h5ad` or Matrix Market goes to `scrna` instead. |
| Existing bulk count matrix + sample metadata + DE/contrast | `rnaseq` (`rnaseq-de`) | Registered | Validate gene identifiers, sample columns, metadata `sample_id`, formula, and contrast. |
| Finished DE/marker results + volcano/MA/heatmap/dotplot | `diffviz` (`diff-visualizer`) | Registered | Do not rerun DE when the supplied file already contains result columns. |
| Multiple FastQC/aligner result files, aggregate QC | `multiqc-reporter` guidance or `sample-qc` for identity/contamination triage | Agent-readable-only / Registered respectively | Separate report aggregation from sample identity, sex mismatch, contamination, and batch-shift triage. |

## Single-cell and expression data

| Shape / intent | Prefer | Status | Key distinction |
| --- | --- | --- | --- |
| Raw-count `.h5ad` or 10x Matrix Market; QC, clustering, markers, annotation, UMAP, contrasts | `scrna` (`scrna-orchestrator`) | Registered | Confirm raw counts in `X` or `layers["counts"]`; processed-only `.h5ad` is not the same input. |
| `.h5ad` plus scVI/scANVI, latent, integration, or batch correction | `scrna-embedding` | Registered | This is the embedding/integration stage. Preserve the latent key and artifact metadata. |
| `integrated.h5ad` or `obsm["X_scvi"]` plus markers/clustering/contrasts | `scrna` with the latent representation option | Registered | Explain the `scrna-embedding → scrna --use-rep X_scvi` chain instead of hiding the handoff. |
| Bulk count matrix, pseudo-bulk, DESeq2/PyDESeq2 | `rnaseq` | Registered | Do not infer “single-cell” from the word “counts”; use metadata and matrix shape. |
| FASTA + promoter/TSS | `gi-promoter` guidance | Agent-readable-only | Use generic `analyze-fasta` only when the request is sequence metrics, not promoter prediction. |
| FASTA + splice donor/acceptor/cryptic splice | `gi-splice` guidance | Agent-readable-only | Ask whether the sequence is a gene body or a short arbitrary fragment. |
| FASTA + enhancer, chromatin, expression, or gene structure | `gi-enhancer`, `gi-chromatin`, `gi-expression`, or `gi-annotation` guidance | Agent-readable-only | Match the explicit biological question and required sequence context; do not collapse all FASTA requests into one route. |

## Sequence, structure, image, and other omics families

| User signal and shape | Prefer | Status | Notes |
| --- | --- | --- | --- |
| FASTA/FASTA.GZ + GC, ORFs, protein properties, pI, GRAVY | `analyze-fasta` | Registered | First distinguish nucleotide from protein sequence using headers/content as permitted by the skill. |
| PDB/CIF or protein structure prediction/comparison | `struct-predictor` guidance | Agent-readable-only | A protein FASTA with only sequence metrics remains `analyze-fasta`; a structure question changes the route. |
| PNG/JPG/TIFF/PDF figure + digitization or table extraction | `data-extract` (`data-extractor`) | Registered | Inspect whether the input is an image, a PDF figure, or a tabular data file before selecting extraction mode. |
| Olink, SomaScan, NPX/RFU affinity-proteomics table | `affprot` (`affinity-proteomics`) | Registered | Platform-specific routing matters; do not use an RNA DE route for protein abundance. |
| MaxQuant/DIA-NN output or a proteomic aging/organ clock | `proteomics-de` or `proteomics-clock` guidance | Agent-readable-only | Read the selected skill contract; no CLI alias is implied by the catalog entry. |
| FASTA alignment + phylogeny/IQ-TREE/maximum likelihood | `phylo` (`phylogenetics-builder`) | Registered | Confirm aligned versus unaligned sequences and desired tree method. |
| Metagenomics/Kraken2/CARD/HUMAnN3 | `metagenomics` (`claw-metagenomics`) | Registered | Distinguish raw reads from an already generated taxonomy/function table. |
| Literature, PubMed, protocol, lab, or public dataset question | `lit-synthesizer`, `protocols-io`, `labstep`, or `ncbi-datasets` guidance | Mixed | These may be agent-readable-only; do not expose a direct runner command without registry evidence. |

## Common chains

State chains explicitly, including the artifact and the condition that makes the next step valid:

1. **Bulk RNA:** `rnaseq-pipeline` → merged counts TSV plus sample metadata → `rnaseq` → DE results → `diffviz`. If the wrapper runs an alignment-only mode with no count handoff, stop or ask for a quantification route.
2. **Single-cell latent workflow:** `scrnaseq-pipeline` → raw-count `.h5ad`/10x output → `scrna-embedding` → `integrated.h5ad` with `obsm["X_scvi"]` → `scrna` with `--use-rep X_scvi` → markers/contrasts.
3. **Variant calling and annotation:** `sarek-pipeline` → local VCF → annotation guidance (`variant-annotation`/`vcf-annotator`) or a registered clinical/reporting route according to the requested output. Do not send patient VCF payloads to public APIs without explicit consent; the specialist skill owns its backend policy.
4. **Pharmacogenomics profile:** `pharmgx` → drug–gene report → optional `profile` composition or `clinpgx` lookup. A photo request is a separate `drugphoto` route and should not be inferred from a text medication name.
5. **Variant association context:** `gwas` → association/eQTL results → optional `clinpgx`, `prs`, or literature guidance only when the user asks for that follow-up.
6. **Existing scRNA result visualization:** marker/DE result table → `diffviz`; do not route a result table through raw `.h5ad` preprocessing.

A chain is a plan, not permission to run every partner automatically. Ask before expensive, destructive, clinical-looking, or networked steps, and preserve each skill's output and reproducibility bundle.
