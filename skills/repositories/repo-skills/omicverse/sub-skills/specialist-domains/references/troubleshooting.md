# Troubleshooting Specialist Domains

## External Binary and Auto-Install Failures

OmicVerse alignment wrappers can search for binaries on `PATH`, in the active Python environment, and optionally attempt installation when `auto_install=True`. Treat `auto_install=True` as a side effect.

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `'<tool>' not found on PATH or in the active environment bin` | Missing CLI such as `STAR`, `fastp`, `featureCounts`, `prefetch`, `fasterq-dump`, `kb`, `simpleaf`, `mafft`, `FastTree`, or `vsearch` | Ask whether installation is allowed; otherwise pass explicit binary path (`star_path`, `fastp_path`, `featurecounts_path`, `prefetch_path`, `fasterq_path`, `simpleaf_bin`) and set `auto_install=False` where available |
| Tool installs unexpectedly | Wrapper defaulted to `auto_install=True` | Re-run with `auto_install=False`; document that installation requires user approval |
| STAR builds an index unexpectedly | `STAR(..., auto_index=True)` and `genome_dir` lacked an index | Use `auto_index=False` for existing indexes; if building is intended, require `genome_fasta_files`, `gtf`, output storage, and resource approval |
| SRA download or validation stalls | Network, SRA toolkit config, or accession issue | Bound accession list, use explicit `output_dir`, confirm network approval, inspect SRA toolkit availability before running |
| `simpleaf`/`alevin-fry` cannot find home paths | Missing `ALEVIN_FRY_HOME`/simpleaf install | Pass `simpleaf_bin` and `alevin_fry_home`; use `dry_run=True` before execution |
| `featureCounts` output missing gene symbols | GTF lacks selected `gene_name_field` or mapping failed | Use `gene_mapping=True`, `gene_name_field='gene_name'`, or provide `gene_map`; inspect simplified count files |

Do not run alignment wrappers merely to test availability. Prefer `--help` for binaries or the bundled input validator for local file/schema checks.

## Downloads and Network Calls

Network-backed functions include SRA `prefetch`, 16S reference fetchers (`fetch_sintax_ref`, `fetch_silva`, `fetch_rdp`), molecular structure fetches (`fetch_structure`, `predict_structure`), and ChEMBL known-drug lookup (`known_drugs`). Ask before network use and always set explicit cache/output directories.

Common signals:

- Connection timeout or reset: retry only if the user approves; keep partial files isolated.
- Empty or stale reference DB: verify `db_dir` and source name; `fetch_silva` may emit deprecation guidance for newer SILVA references.
- Molecular target not found: distinguish gene symbol, UniProt accession, and PDB ID; use `source='pdb'` for four-character PDB IDs.

## Optional Extras

| Area | Extra / packages | Failure signal | Action |
| --- | --- | --- | --- |
| Genetics | `omicverse[genetics]`: `pymatrixeqtl`, `pysusie`, `pycoloc`, `pytwosamplemr`, `pyscdrs`, `pyldsc`, `pytwas`, `statsmodels` | ImportError when calling backend functions | Core `read_sumstats`, `gwas_qc`, and `gwas_association` may still work; install extra only if needed |
| AIRR | `omicverse[airr]`: `pyimmunarch`, `pyalakazam`, `pyshazam`, `pyscoper`, `pytigger`, `pydowser`, `pygliph` | Bulk/B-cell/TCR specificity backend import error | Single-cell AIRR reader/QC/clonotype functions can work without bulk extras |
| Molecular core | `omicverse[mol]` on Python >=3.10: `py3Dmol`, `biotite`, `chembl_webresource_client`, `requests` | ImportError mentioning `omicverse[mol]` | Use Python >=3.10 and install core molecular extra for views, parsing, and ChEMBL |
| Docking | `omicverse[mol-dock]`: `rdkit`, `vina`, `meeko`, `gemmi`; pocket detection via `fpocket-rs` | ImportError from `dock`, `redock_validate`, or `pockets` | Install docking/pocket backends only when docking is required and allowed |
| DADA2 | `pydada2` | ImportError from DADA2 functions | Use `backend='vsearch'` if external VSEARCH pipeline is available, or install pydada2 |

## Genetics Schema and Allele Issues

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Missing `SNP`, `BETA`, `SE`, `P`, or `N` | Source uses noncanonical column names | Load with `read_sumstats(..., rename=True)` or map aliases manually; record the mapping |
| Coloc has few shared variants | Variant IDs differ across GWAS/eQTL tables | Normalize IDs to the same convention; check chromosome/position/allele composite IDs |
| MR effects have opposite direction | Exposure/outcome effect alleles not harmonized | Run `harmonize`; inspect palindromic SNPs and dropped ambiguous variants |
| Palindromic SNPs are dropped or ambiguous | `A/T` or `C/G` with missing/discordant EAF | Provide `eaf`; tune harmonization `tolerance` only with domain justification |
| Fine-map or coloc backend errors on dimensions | `z`, `R`, `bhat`, `shat`, MAF, or SNP order mismatch | Assert identical variant order and matrix shapes before calling backend |
| GWAS association returns many `NaN` rows | Monomorphic SNPs, too few complete samples, or singular covariates | Check MAF/call rate, phenotype length, missingness, and covariate rank |

## AIRR Schema Issues

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `AIRR table lacks both 'cell_id' and 'sequence_id'` | AIRR TSV lacks cell identifiers | Add `cell_id`, or ensure `sequence_id` contains cell barcode prefixes |
| `clonal_expansion` raises missing column error | `define_clonotypes` was not run or custom clone column absent | Run `define_clonotypes(..., key_added='clone_id')` or pass the correct `target_col` |
| Unexpected `receptor_type='ambiguous'` | TCR and BCR loci appear in the same cell | Inspect `locus`, `v_call`, `j_call`, and chain filtering before metrics |
| Empty V/J usage | Wrong chain slot or missing locus/gene fields | Use `chain='VDJ_1'` or `VJ_1` matching the receptor; verify `{slot}_v_gene` and `{slot}_locus` |
| CDR3/TCRdist failure | Missing or invalid `junction_aa` / CDR3 strings | Clean CDR3s with `clean_cdr3` or filter using `usable_cdr3_mask` before distance workflows |
| Bulk repertoire functions fail | Optional AIRR backend missing or table is not AIRR/immunarch-like | Install `omicverse[airr]` if approved; validate columns such as `aa`, `v_call`, `j_call`, `sample_id`, `clone_id` |

## Amplicon and FASTQ Issues

| Symptom | Likely cause | Action |
| --- | --- | --- |
| No R1/R2 FASTQ pairs found | Directory empty or naming pattern unsupported | Use explicit `samples=[(sample, r1, r2)]`; validate with `check_specialist_inputs.py fastq` |
| Sample name rejected as illegal | Sample contains path separators or traversal (`../`) | Rename sample IDs to safe alphanumeric/underscore/dash/dot strings |
| `primer_rev` error | Reverse primer supplied without forward primer | Supply both `primer_fwd` and `primer_rev`, or neither |
| DADA2 pipeline requires workdir | Missing explicit output location | Provide a dedicated `workdir`; keep outputs isolated |
| `backend='emu'` not implemented | Unsupported amplicon backend | Use `backend='vsearch'` or `backend='dada2'` |
| Taxonomy columns empty | No SINTAX file or assignments below cutoff | Confirm `db_fasta`, `sintax_tsv`, cutoff, and reference source |
| MAFFT/FastTree validation errors | Invalid mode/model | Use supported MAFFT mode and nucleotide/protein model choices documented by the wrapper |

## Molecular Structure and Docking Issues

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Target resolves incorrectly | Gene symbol, UniProt accession, and PDB ID ambiguity | Use explicit `source='pdb'` for PDB IDs or provide UniProt accession for AlphaFold |
| `ImportError` mentions `omicverse[mol]` | Molecular core extra missing or Python <3.10 | Use Python >=3.10 and install `omicverse[mol]` if approved |
| Pockets fail | `fpocket-rs` missing or structure lacks valid coordinates | Install pocket backend if approved; fetch/clean a structure with coordinates |
| Docking fails during ligand preparation | RDKit/Meeko missing or ligand invalid | Install `omicverse[mol-dock]` if approved; validate SMILES/file before docking |
| Docking fails during Vina search | Vina missing, malformed receptor PDBQT, invalid box, or huge search space | Use explicit `box`, lower `exhaustiveness` for smoke tests, and check receptor preparation |
| AlphaFold confidence is low | pLDDT/PAE indicates uncertain region | Avoid over-interpreting docking; prefer experimental PDB or a known domain/pocket |

## Quick Safe Checks

Run the bundled validator help without side effects:

```bash
python sub-skills/specialist-domains/scripts/check_specialist_inputs.py --help
```

Examples:

```bash
python sub-skills/specialist-domains/scripts/check_specialist_inputs.py gwas sumstats.tsv --mode mr
python sub-skills/specialist-domains/scripts/check_specialist_inputs.py airr-vdj filtered_contig_annotations.csv
python sub-skills/specialist-domains/scripts/check_specialist_inputs.py fastq ./fastqs
python sub-skills/specialist-domains/scripts/check_specialist_inputs.py mol-target EGFR P00533 1CRN
```
