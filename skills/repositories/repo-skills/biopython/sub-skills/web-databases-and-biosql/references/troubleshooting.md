# Troubleshooting web database and BioSQL workflows

## Quick diagnosis table

| Symptom | Likely cause | Correct response |
|---|---|---|
| Warning that Entrez email is not specified | `Entrez.email` was not set and no per-call `email` was provided | Set a real contact address for approved live requests; do not use fake email to silence the warning |
| `StreamModeError` saying XML must be opened in binary mode | Entrez XML was opened as text | Open XML with `"rb"` or pass the filename/path directly to `Entrez.read`/`parse` |
| `NotXMLError` or `CorruptedXMLError` | The handle is not XML, is truncated, or is an HTML/error page | Inspect/save the raw response; parse MEDLINE/GenBank/text with the correct non-XML parser |
| Unknown XML tag or validation failure | Entrez DTD/XSD changed or a record contains tags not represented locally | Prefer updating local DTD/XSD cache; use `validate=False` only if skipping unknown tags is acceptable |
| Runtime error from XML error elements | Entrez returned an error payload | Fix query parameters or set `ignore_errors=True` only if the caller will inspect returned errors |
| HTTP 400/404 from KEGG or ExPASy | Invalid identifier, database, option, or no such accession | Validate input and report provider status; do not blindly retry client-side errors |
| HTTP 429/5xx or transient `URLError` | Rate limiting or temporary service/network failure | Respect provider limits, retry with backoff, and preserve any already downloaded data |
| Empty second read from a BLAST/Entrez handle | The stream was consumed once | Save bytes/text once, then parse from the saved data or reopen the saved file |
| `ValueError: More than one record found` | Used `read` on multi-record Swiss-Prot/GenBank-style input | Use `parse` and iterate |
| `ValueError: No ... record found` | Empty or wrong-format input for a format-specific parser | Confirm the input format and route to the correct parser |
| `ImportError: No module named MySQLdb/psycopg2/mysql.connector` | Optional BioSQL database driver is not installed | Install/choose the approved driver or use SQLite for local-only prototypes |
| BioSQL connection succeeds but schema operations fail | Missing/wrong BioSQL schema, permissions, or DB-specific SQL issue | Verify schema version, user privileges, driver, and target database type before loading records |

## Entrez issues

### Identity and rate policy

Always set `Entrez.email` before approved live calls. Set `Entrez.tool` for larger applications. Set `Entrez.api_key` only when the user supplies a valid key. Without an API key, Biopython enforces about three Entrez requests per second; with an API key, about ten per second.

`Entrez.max_tries` and `Entrez.sleep_between_tries` control retry behavior for transient failures. Do not solve repeated 4xx client errors by increasing retries.

### XML parser mode

`Entrez.read` and `Entrez.parse` require XML with a DTD or XML Schema. The parser validates by default. If a task only needs a few fields from XML whose schema is not available, first consider Python's standard XML tools; use `validate=False` only when the user accepts loss of unknown tags.

When parsing saved XML:

```python
from Bio import Entrez

record = Entrez.read("saved-entrez-result.xml")  # path is opened/closed safely
# or
with open("saved-entrez-result.xml", "rb") as handle:
    record = Entrez.read(handle)
```

For large multi-record XML, use `Entrez.parse` and process records as a stream.

### Text versus XML formats

Some Entrez calls return XML by default, but `efetch` can return text formats depending on `rettype`/`retmode`:

- PubMed MEDLINE: `rettype="medline", retmode="text"` then `Bio.Medline.parse`.
- GenBank flat file: `rettype="gb", retmode="text"` then usually `SeqIO.parse(..., "genbank")`.
- FASTA text: `rettype="fasta", retmode="text"` then `SeqIO.parse(..., "fasta")`.

If the parser reports non-XML content, check whether the request asked for text and route accordingly.

## MEDLINE, GenBank, Swiss-Prot, and ExPASy issues

- Use `read` only when exactly one record is expected; use `parse` for zero, one, or many records.
- Swiss-Prot text can be parsed by `Bio.SwissProt` for rich format-specific records, or by `SeqIO` with the `"swiss"` format when the user wants `SeqRecord` objects.
- `ExPASy.get_sprot_raw` and `ExPASy.get_prosite_raw` are online functions. They raise `ValueError` for common nonexistent raw IDs. `get_prosite_entry` and `get_prodoc_entry` return HTML, not raw parser text.
- For Prosite/Prodoc/Enzyme flat files, use the corresponding `Bio.ExPASy` parser modules and keep downloaded source text available for reproducibility.

## UniProt search issues

`UniProt.search` is online and returns a lazy iterator over JSON results. It can fetch more pages during iteration or slicing. For broad queries:

- Ask for a maximum result count.
- Use `fields=[...]` to limit payload size.
- Use slicing (`results[:N]`) rather than `list(results)` unless the user explicitly wants everything.
- Treat `batch_size=0` as count-oriented; do not expect it to populate full result records.

## KEGG issues

- KEGG parser coverage is incomplete. Specific parser/writer support is available for compound, enzyme, and map records; other flat files may need the generic parser or manual section handling.
- The REST wrapper throttles calls to roughly three per second, but the caller still owns query scope and batching.
- `kegg_get` accepts at most 10 entries per call; `kegg_list` accepts at most 100 entries when a list is supplied.
- Invalid option combinations may raise `ValueError` before network access; provider-side invalid queries may return HTTP 400/404.
- Treat pathway image/KGML retrieval as network/file-download work, not a parser smoke test.

## Online BLAST (`qblast`) issues

`Bio.Blast.qblast` submits sequences to NCBI. It is not an offline parser.

Before using it:

- Confirm network approval and data-sharing permission.
- Set `Bio.Blast.email` to a real contact address.
- Keep expected search count low; for many searches, prefer local BLAST or schedule per NCBI guidance.
- Choose `format_type` based on downstream parser compatibility.
- Save the returned data before parsing; a stream can be read only once.

If results differ from the web interface, compare all BLAST parameters. Defaults in `qblast` and the web form are not guaranteed to match.

## BioSQL issues

- Importing `BioSQL` does not prove that a specific database server or driver works.
- `sqlite3` is available in most Python installations and needs no external server, but it does not test MySQL/PostgreSQL behavior.
- `MySQLdb`, `mysql.connector`, `psycopg2`, and `pgdb` are optional third-party drivers; install and verify only in an approved environment.
- Schema loading is database-type-specific. Do not load a schema into a non-empty or production database without explicit approval.
- Use transaction boundaries: commit after successful loads, rollback on failure, and close connections in `finally` blocks.
- Keep retrieval failures separate from database write failures so partially downloaded data is not mistaken for loaded records.

## Offline smoke script

The bundled smoke script intentionally avoids:

- network calls;
- database-server connections;
- credential use;
- external command-line tools;
- original repository checkout files.

If it fails, first inspect the installed Biopython version and importability of `Bio`, `BioSQL`, `Bio.Entrez`, `Bio.Medline`, `Bio.SwissProt`, `Bio.KEGG`, `Bio.ExPASy`, `Bio.UniProt`, and `Bio.Blast`.
