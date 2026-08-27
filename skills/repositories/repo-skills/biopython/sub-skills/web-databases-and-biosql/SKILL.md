---
name: web-databases-and-biosql
description: "Use Biopython web/database retrieval, offline public-database
  parsers, and optional BioSQL safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Biopython web databases and BioSQL

Use this sub-skill when a task involves Biopython's public biological database clients, database-specific parsers, or BioSQL integration:

- NCBI Entrez E-utilities through `Bio.Entrez`.
- PubMed/MEDLINE, GenBank flat files, Swiss-Prot/UniProt, ExPASy, and KEGG records.
- Online BLAST submission only for `Bio.Blast.qblast` etiquette and network cautions.
- Optional BioSQL relational storage through the `BioSQL` package.

## First routing decision

1. **Online retrieval requested**: confirm network permission, user identity metadata, expected request count, retry/rate policy, and whether data may be sent to the remote service. Do not run online retrieval as a default smoke check.
2. **Already-downloaded records**: prefer offline parsing with `Bio.Entrez.read`/`parse`, `Bio.Medline`, `Bio.SwissProt`, `Bio.ExPASy.*`, `Bio.KEGG.*`, or `Bio.GenBank` as appropriate.
3. **General sequence file I/O**: route to the file I/O sub-skill for ordinary `SeqIO`/`AlignIO` parsing, indexing, and conversion.
4. **BLAST result object analysis**: route to the alignment/search sub-skill. This sub-skill only covers online `qblast` safety and saving returned handles.
5. **BioSQL**: treat database servers, schema loading, and third-party DB drivers as optional. Do not require full server setup unless the user explicitly asks for BioSQL persistence.

## References

- `references/web-database-workflows.md` for Entrez, Medline, GenBank, SwissProt, UniProt, ExPASy, KEGG, and qblast workflows.
- `references/biosql-reference.md` for BioSQL driver choices, connection patterns, and optional setup boundaries.
- `references/troubleshooting.md` for rate limits, parser modes, validation errors, network failures, and database-driver problems.

## Offline check

Run `python scripts/offline_database_parsers_smoke.py` from this sub-skill directory, or run it by path from any working directory. It performs only in-memory parser/import checks and prints `PASS` on success.
