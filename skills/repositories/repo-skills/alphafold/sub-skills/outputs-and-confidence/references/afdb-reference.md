# AlphaFold DB Reference

This reference distills the AlphaFold Protein Structure Database formats and access warnings needed for output-processing tasks.

## Dataset Scope and License

- The public AlphaFold UniProt release contains approximately 214 million predictions.
- Data is available under CC-BY-4.0 terms and can be used for academic and commercial purposes with appropriate attribution.
- The dataset is theoretical modeling output, provided as-is, and is not a substitute for professional medical, diagnostic, or treatment advice.

## Per-Entry File Naming

AlphaFold DB entry filenames begin with an identifier of the form:

```text
AF-<UniProt accession>-F<fragment number>
```

Each entry provides three primary files:

| File suffix | Meaning | How to use |
| --- | --- | --- |
| `model_v4.cif` | Atomic coordinates and metadata for the predicted structure | Parse as ModelCIF/PDBx/mmCIF; pLDDT is also represented in the coordinate file metadata/B-factor-like fields. |
| `confidence_v4.json` | Per-residue pLDDT confidence | Same conceptual fields as `confidence_<model>.json`: residue numbers, pLDDT scores, and categories. |
| `predicted_aligned_error_v4.json` | Pairwise PAE confidence | Use for domain/domain or residue/residue placement confidence; lower values mean more confident relative placement. |

Predictions grouped by NCBI taxonomy ID are distributed as proteome shard tar files named like:

```text
proteomes/proteome-tax_id-<TAX_ID>-<SHARD_ID>_v4.tar
```

## Extra Dataset Files

| File | Contents |
| --- | --- |
| `accession_ids.csv` | UniProt accession, first residue index, last residue index, AlphaFold DB identifier, and latest version. |
| `sequences.fasta` | FASTA records for all proteins in the current database version; headers start with `>AFDB` followed by AlphaFold DB identifier and protein name. |

## Access Patterns

- Use the AlphaFold DB website for simple lookup by protein name, gene name, or UniProt accession.
- Use premade species or Swiss-Prot downloads when a curated subset is enough.
- Use manifests for custom subsets when you already know the files needed.
- Use GCS proteome tar shards for large proteome-level transfer.
- Use BigQuery metadata only when a query-based subset is necessary and the user understands cost controls.

## Cost and Scale Warnings

- The full database is very large, roughly tens of terabytes and hundreds of millions of files after extraction.
- Full download/manipulation requires substantial storage, filesystem capacity, bandwidth, and processing resources.
- GCS public dataset access can still require a Google Cloud account and project setup.
- BigQuery has a free tier, but repeated or broad metadata queries can exceed free limits and incur charges on paid billing accounts.
- Storage Transfer Service and transfers to or from other cloud services may incur costs.
- Do not trigger AFDB downloads, GCS transfers, BigQuery queries, or cloud setup automatically during skill validation; produce plans and warnings unless the user explicitly requests execution.

## Mapping AFDB Files to Local Outputs

| AFDB file | Closest local `run_alphafold` artifact | Difference |
| --- | --- | --- |
| `model_v4.cif` | `ranked_0.cif` or per-model `.cif` | AFDB is a curated database prediction file with database metadata; local files are per-run outputs. |
| `confidence_v4.json` | `confidence_<model>.json` | Both describe pLDDT; local filenames include model names. |
| `predicted_aligned_error_v4.json` | `pae_<model>.json` | Local PAE is present only when the model output includes predicted aligned error. |

## Practical Review Checklist

1. Confirm whether the task is about AFDB dataset files or a local `run_alphafold` output folder.
2. For AFDB downloads, prefer the smallest subset route that satisfies the task.
3. Warn explicitly before any workflow that touches GCS, BigQuery, cloud billing, or full-database transfer.
4. For confidence interpretation, use pLDDT for local structure reliability and PAE for relative placement.
5. Preserve attribution/license notes when advising downstream reuse of AFDB predictions.
