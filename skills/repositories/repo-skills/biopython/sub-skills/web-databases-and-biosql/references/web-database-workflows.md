# Web-database and parser workflows

This reference covers Biopython modules that either talk to public biological database services or parse database-specific record formats after data has already been obtained. Online calls are never a required verification step.

## Network-safety checklist

Before using an online service from Biopython, establish:

- **Permission**: the user approved network access and the biological data may be sent to the service.
- **Identity**: set an appropriate email/tool field when supported so providers can contact the user.
- **Request budget**: know expected request count, batch size, sleep/retry policy, and whether the service permits bulk use.
- **Offline fallback**: prefer parsing saved XML/text files when the task is analysis rather than retrieval.
- **Handle discipline**: use context managers or close returned handles; cache raw responses when debugging parsers to avoid repeating remote calls.

## NCBI Entrez (`Bio.Entrez`)

Set module-level defaults before network calls:

```python
from Bio import Entrez

Entrez.email = "user@example.org"       # use a real contact address for live work
Entrez.tool = "my-biopython-workflow"   # defaults to "biopython" if not changed
Entrez.api_key = None                    # set to an NCBI API key only when available
```

Operational facts:

- Entrez functions return handles. XML results are returned in binary mode; plain text results are usually text handles.
- Biopython automatically enforces NCBI's request rate: about 3 requests/second without an API key, about 10 requests/second with one.
- `Entrez.max_tries` defaults to `3`; `Entrez.sleep_between_tries` defaults to `15` seconds for transient retry handling.
- For long query strings or about 200+ IDs, request construction uses HTTP POST instead of GET.
- If `email` is unset, request construction warns; do not silence the warning by using fake contact information.

Common functions:

| Function | Use | Typical parser |
|---|---|---|
| `einfo(**kwargs)` | list databases, fields, links, counts | `Entrez.read` |
| `esearch(db, term, **kwargs)` | search and return IDs, count, query translation, optional history | `Entrez.read` |
| `epost(db, **kwargs)` | post many IDs to Entrez history | `Entrez.read` |
| `efetch(db, **kwargs)` | retrieve records by IDs or history | `Entrez.read`, `Entrez.parse`, `Medline.parse`, `SeqIO`, or raw text |
| `esummary(**kwargs)` | retrieve document summaries | `Entrez.read` or `Entrez.parse` |
| `elink(**kwargs)` | link records between databases | `Entrez.read` or `Entrez.parse` |
| `egquery(**kwargs)` | global query counts | `Entrez.read` |
| `espell(**kwargs)` | spelling suggestions | `Entrez.read` |
| `ecitmatch(**kwargs)` | PubMed IDs for citation strings | raw text handle |

### `Entrez.read` versus `Entrez.parse`

Use the installed signatures as the ground truth:

```python
Entrez.read(source, validate=True, escape=False, ignore_errors=False)
Entrez.parse(source, validate=True, escape=False, ignore_errors=False)
```

Choose deliberately:

- `read` loads a complete XML result into one Python object. It is right for small single-result documents such as most `einfo` and `esearch` results.
- `parse` is a generator for XML documents that can be represented as multiple records. It is better for large `efetch`, `esummary`, or `elink` XML results.
- XML files must be opened in binary mode (`"rb"`) or passed as a filename/path. Text streams raise a stream-mode error.
- `validate=True` validates against local DTD/XSD definitions and raises if the XML contains unknown tags. Set `validate=False` only when you intentionally accept skipping unknown tags.
- `escape=True` HTML-escapes invalid HTML characters in returned strings.
- `ignore_errors=True` stores XML error elements instead of raising immediately; use only when the caller can inspect and report those errors.

### History-aware Entrez batching

For large result sets, avoid fetching many IDs in one URL. Use history:

```python
from Bio import Entrez

Entrez.email = "user@example.org"
search = Entrez.read(Entrez.esearch(db="pubmed", term="biopython", usehistory="y", retmax=0))
count = int(search["Count"])
webenv = search["WebEnv"]
query_key = search["QueryKey"]

for start in range(0, count, 200):
    with Entrez.efetch(
        db="pubmed",
        rettype="medline",
        retmode="text",
        retstart=start,
        retmax=200,
        webenv=webenv,
        query_key=query_key,
    ) as handle:
        chunk = handle.read()
        # Parse or persist this chunk before fetching the next batch.
```

Use `epost` when the input is already a long list of UIDs. For `elink`, pass multiple IDs as a list when one-to-one source-to-target link mapping matters; a comma-delimited string can merge destinations.

## PubMed/MEDLINE (`Bio.Medline`)

Use MEDLINE parsing when PubMed records are in MEDLINE flat-file format, typically from `efetch(db="pubmed", rettype="medline", retmode="text")`.

```python
from io import StringIO
from Bio import Medline

text = """PMID- 1
TI  - A tiny title.
AU  - Doe J
AB  - A tiny abstract.

"""
record = Medline.read(StringIO(text))      # exactly one record
records = list(Medline.parse(StringIO(text)))  # iterator for one or many records
```

Notes:

- MEDLINE record keys are abbreviations such as `PMID`, `TI`, `AU`, `AB`, `JT`, and `DP`.
- Repeated fields such as authors become lists.
- For PubMed XML, use `Entrez.read`/`parse`; for MEDLINE text, use `Bio.Medline`.

## GenBank records

For most work on GenBank/GenPept sequence records, use the file-I/O skill with `Bio.SeqIO` and format `"genbank"`/`"gb"`. This preserves the normal `SeqRecord`/`SeqFeature` interface.

Use `Bio.GenBank.read(handle)` or `Bio.GenBank.parse(handle)` only when the task needs GenBank-specific record objects that are closer to the raw flat-file fields than `SeqRecord` is.

Retrieval pattern:

```python
from Bio import Entrez, SeqIO

Entrez.email = "user@example.org"
with Entrez.efetch(db="nuccore", id="ACCESSION.VERSION", rettype="gb", retmode="text") as handle:
    records = list(SeqIO.parse(handle, "genbank"))
```

Keep GenBank bulk downloads polite: use history or FTP-style bulk data sources for very large public datasets, then parse offline.

## Swiss-Prot, UniProt, and ExPASy

### Swiss-Prot flat files (`Bio.SwissProt`)

Use `Bio.SwissProt.read(source)` for exactly one Swiss-Prot flat-file record and `Bio.SwissProt.parse(source)` for many records. The parser accepts text handles, binary handles, or paths; binary Swiss-Prot streams are decoded as ASCII.

```python
from io import StringIO
from Bio import SwissProt

text = """ID   TINY_TEST Reviewed; 4 AA.
AC   P00000;
DT   01-JAN-2000, integrated into UniProtKB/Swiss-Prot.
DT   01-JAN-2000, sequence version 1.
DT   01-JAN-2000, entry version 1.
DE   RecName: Full=Tiny test protein;
OS   Synthetic construct.
OC   other sequences.
OX   NCBI_TaxID=32630;
SQ   SEQUENCE   4 AA;  477 MW;  ABCDEF1234567890 CRC64;
     MAAA
//
"""
record = SwissProt.read(StringIO(text))
assert record.entry_name == "TINY_TEST"
```

If the user wants `SeqRecord` objects rather than format-specific Swiss-Prot records, route to the file-I/O skill and use `SeqIO` formats such as `"swiss"` or `"uniprot-xml"`.

### ExPASy retrieval and parsers

`Bio.ExPASy` provides network functions returning text handles:

- `ExPASy.get_sprot_raw(accession)` returns a raw Swiss-Prot entry suitable for `SwissProt.read`.
- `ExPASy.get_prosite_raw(id)` returns a raw PROSITE/PRODOC record suitable for `Bio.ExPASy.Prosite` or `Bio.ExPASy.Prodoc` parsers.
- `ExPASy.get_prosite_entry(id)` and `get_prodoc_entry(id)` return HTML pages, not raw parser input.

Invalid raw identifiers raise `ValueError` for the common raw-entry functions; treat HTML-returning functions as display/download helpers rather than parser inputs.

Additional parser modules include `Bio.ExPASy.Prosite`, `Bio.ExPASy.Prodoc`, `Bio.ExPASy.Enzyme`, and `Bio.ExPASy.ScanProsite`.

### UniProt search (`Bio.UniProt`)

`Bio.UniProt.search(query, fields=None, batch_size=500)` is an online JSON search iterator. It fetches pages from UniProt as needed.

Use bounded access patterns:

```python
from Bio import UniProt

results = UniProt.search("(organism_id:2697049) AND (reviewed:true)", fields=["accession", "protein_name"])
first_ten = results[:10]
```

Do not call `list(UniProt.search(...))` on broad queries unless the user explicitly requested all results and approved the network/time budget. Use `batch_size=0` only for count-oriented workflows where no full result page is needed.

## KEGG (`Bio.KEGG`)

Biopython includes KEGG REST helpers and parsers. The KEGG parser coverage is intentionally limited: specific parser/writer support exists for compound, enzyme, and map records, with a generic parser for other KEGG-like flat files.

REST helpers:

| Function | Use |
|---|---|
| `REST.kegg_info(database)` | database/organism statistics |
| `REST.kegg_list(database, org=None)` | list entries, optionally organism-restricted for pathway/module |
| `REST.kegg_find(database, query, option=None)` | search entries |
| `REST.kegg_get(dbentries, option=None)` | retrieve entries or sequence/image/KGML/JSON variants |
| `REST.kegg_conv(target_db, source_db, option=None)` | convert identifiers |
| `REST.kegg_link(target_db, source_db, option=None)` | link related entries |

Important limits and failures:

- The REST wrapper throttles calls to no more than about three per second.
- `kegg_list` accepts at most 100 entries when a list is supplied.
- `kegg_get` accepts at most 10 entries per call; image/KGML-style options are more restrictive.
- Local validation catches some invalid options, but HTTP 400/404 responses must be handled by the caller.

Offline parser example:

```python
from io import StringIO
from Bio.KEGG import Enzyme

text = """ENTRY       EC 5.4.2.2                 Enzyme
NAME        Phosphoglucomutase
CLASS       Isomerases;
            Intramolecular transferases;
            Phosphotransferases (phosphomutases)
SYSNAME     alpha-D-glucose 1,6-phosphomutase
///
"""
record = Enzyme.read(StringIO(text))
assert record.entry == "5.4.2.2"
```

## Online BLAST (`Bio.Blast.qblast`) cautions

Use this sub-skill only for safe online submission policy. For parsing, filtering, and object-model work on BLAST outputs, route to the alignment/search sub-skill.

Installed signature fact:

```python
Blast.qblast(program, database, sequence, ..., format_type="XML", ...)
```

Safety facts:

- `qblast` contacts NCBI BLAST over the network; do not call it without explicit approval.
- Set `Bio.Blast.email` to a real contact address. `Bio.Blast.tool` defaults to `"biopython"`.
- NCBI asks automated clients not to contact the server more often than once every 10 seconds and not to poll one RID more often than once per minute; Biopython's `qblast` handles those timing rules internally.
- For more than about 50 searches, schedule runs outside peak weekday hours or use local BLAST instead.
- Never send confidential, embargoed, or non-shareable sequences to a public BLAST service.
- Save the returned bytes once before parsing; reading a returned stream consumes it.
- `format_type` can request `"XML"`, `"XML2"`, `"JSON2"`, `"Tabular"`, `"HTML"`, or `"Text"`; choose a parser-compatible format deliberately.
