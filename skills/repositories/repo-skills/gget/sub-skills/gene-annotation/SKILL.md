---
name: gene-annotation
description: "Use gget to discover Ensembl reference FTPs, search gene or
  transcript annotations, inspect Ensembl/WormBase/FlyBase IDs, and retrieve
  nucleotide or UniProt amino-acid FASTA sequences."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# Gene annotation

Use this skill for identifier-centered annotation work: choose a species/release,
find an ID from free text, inspect its metadata, and retrieve nucleotide or
protein sequence. The four public operations are `gget.ref`, `gget.search`,
`gget.info`, and `gget.seq`. They query remote Ensembl, Ensembl Genomes,
Ensembl REST, NCBI, UniProt, or PDBe services; a network-enabled run is
required.

## Choose the operation

- **Reference files/FTP discovery:** `gget.ref` returns release-aware links and
  metadata for GTF, DNA, cDNA, CDS, ncRNA, and peptide files. It does not
  download in Python unless the caller downloads the returned URL.
- **Free-text discovery:** `gget.search` searches Ensembl gene or transcript
  names, descriptions, synonyms, and related annotation fields. It needs a
  species or explicit Ensembl core database.
- **ID metadata:** `gget.info` expands Ensembl, WormBase, or FlyBase IDs and
  can add NCBI, UniProt, and optional PDB information.
- **Sequence:** `gget.seq` returns FASTA records as a Python list. Nucleotide
  requests use Ensembl; `translate=True` uses UniProt protein records.

Route sequence comparison/alignment to **sequence-tools**, expression queries
to **expression-omics**, and target or cancer queries to **disease-structure**.
Do not infer a protein match from a symbol alone: resolve the species-specific
ID, then inspect its metadata before choosing canonical or isoform behavior.

## Fast path: search -> info -> sequence

1. Search the intended species with a narrow term and a small `limit`.
2. Select an `ensembl_id` and verify `gene_name`, description, `biotype`, and
   `url`; when transcripts matter, search with `id_type="transcript"`.
3. Call `gget.info(id, ncbi=False, pdb=False)` first. Read `object_type`, the
   current `ensembl_id`, and `canonical_transcript`; for a gene, inspect
   `all_transcripts` when isoforms are needed.
4. Call `gget.seq(current_id, translate=False)` for nucleotide or
   `gget.seq(current_id, translate=True)` for the canonical protein. Add
   `isoforms=True` only for a gene when all transcript records are wanted.
5. Validate the returned FASTA headers and sequence alphabet/length before
   downstream analysis. Save explicitly or serialize the returned list; see
   [workflows](references/workflows.md).

A compact Python chain is:

```python
import gget
hits = gget.search("ace2", species="homo_sapiens", limit=5, verbose=False)
ens_id = hits.iloc[0]["ensembl_id"]
meta = gget.info(ens_id, ncbi=False, pdb=False, json=True, verbose=False)
protein_fasta = gget.seq(ens_id, translate=True, verbose=False)
```

The chain is current-database work: `search`, `info`, and `seq` do not share an
explicit release parameter. Record the returned Ensembl version and service
responses if reproducibility matters.

## Output and safety rules

- Python `json=True` is supported by `search` and `info`; it changes the return
  from a pandas `DataFrame` to JSON-compatible list/dictionary data. `ref` has
  dictionary output by default; `seq` always returns FASTA lines as a list.
- `wrap_text=True` is a display convenience for long DataFrame text. It does
  not create a new stable schema and is not a JSON formatting option.
- Python `save=True` writes fixed filenames in the current working directory:
  `gget_ref_results.json` or `.txt`, `gget_search_results.csv` or `.json`,
  `gget_info_results.csv` or `.json`, and `gget_seq_results.fa`. The return
  value is still useful; use the CLI `--out` option for a chosen path.
- IDs beginning with `ENS` have version suffixes removed before `info` and
  `seq` lookups; metadata reports the latest version returned by Ensembl.
  WormBase and FlyBase identifiers are handled separately and must not be
  normalized as Ensembl IDs.
- Keep requests bounded. `info` documents a practical limit of 1,000 IDs per
  request; split larger lists. Avoid repeatedly polling public APIs, and keep
  `verbose=True` while diagnosing partial or missing records.

## CLI quick reference

```text
gget ref [species] [-w all|gtf,cdna,dna,cds,ncrna,pep] [-r RELEASE]
         [--ftp] [--list_species|--list_iv_species] [--download]
         [--out_dir DIR] [--out FILE] [--quiet]
gget search WORD... --species SPECIES [-r RELEASE] [-t gene|transcript]
            [-ao or|and] [-l LIMIT] [--csv] [--out FILE] [--quiet]
gget info ID... [--ncbi] [--uniprot] [--pdb] [--csv] [--out FILE] [--quiet]
gget seq ID... [--translate] [--isoforms] [--out FILE] [--quiet]
```

CLI output is JSON by default for `ref`, `search`, and `info`; `--csv` switches
`search` or `info` to CSV. `seq` emits FASTA. `--ncbi` and `--uniprot` are
negative flags in the CLI (they turn those providers off), unlike Python's
positive boolean arguments. Use `-h` for the installed CLI help; deprecated
CLI aliases are documented in [api](references/api.md), but should not be used.

## Constraints and handoff

Reference and search resolution depend on live Ensembl listings/MySQL. Metadata
can combine several live providers, and protein retrieval depends on UniProt
cross-references; a valid Ensembl ID can therefore have no protein record.
Release selection for `ref` and `search` does not freeze REST/UniProt metadata.
Do not silently substitute another species, release, transcript, or UniProt
record when an exact match is absent. Use the recovery steps in
[troubleshooting](references/troubleshooting.md), and preserve the selected ID,
release/database, flags, and output mode in the downstream handoff.
