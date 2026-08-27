# SearchIO and BLAST reference

This reference covers the installed `Bio.SearchIO` and `Bio.Blast` APIs used for sequence-search result workflows. It is offline-first: parsing existing result files is safe; network search submission is optional and requires explicit user approval.

## SearchIO object model

`Bio.SearchIO` normalizes output from search tools into a four-level hierarchy:

```text
QueryResult  -> one search query and its hits
  Hit        -> one database target/hit for that query
    HSP      -> one high-scoring pair or alignment region
      HSPFragment -> one contiguous aligned fragment within an HSP
```

`QueryResult` behaves like a hybrid list/dictionary: iterate for hits, index by integer for ordered hits, and access by hit key/id for dictionary-style lookup. `Hit` contains HSPs. `HSP` may contain one or more fragments. Fragment-level objects hold query/hit identifiers, coordinate/strand/frame metadata, and optional `SeqRecord`/alignment objects if the parsed format provides sequences.

Coordinate conventions are normalized:

- Start/end coordinates are Python-style: zero-based, half-open intervals.
- Fragment start is always less than fragment end, even when the source format reports reverse-strand coordinates in descending order.
- Strand values are limited to `-1`, `0`, `1`, or `None`; frame values are integers from `-3` to `3` or `None`.
- When writing back to a supported format, Biopython converts normalized coordinates back to that format's convention.

## Verified SearchIO signatures and formats

Installed public signatures:

```text
SearchIO.parse(handle, format=None, **kwargs)
SearchIO.read(handle, format=None, **kwargs)
SearchIO.write(qresults, handle, format=None, **kwargs)
SearchIO.convert(in_file, in_format, out_file, out_format, in_kwargs=None, out_kwargs=None)
SearchIO.index(filename, format=None, key_function=None, **kwargs)
SearchIO.index_db(index_filename, filenames=None, format=None, key_function=None, **kwargs)
```

Verified read/parse formats:

```text
blast-tab, blast-xml, blat-psl, exonerate-cigar, exonerate-text,
exonerate-vulgar, fasta-m10, hhsuite2-text, hhsuite3-text,
hmmer2-text, hmmer3-tab, hmmer3-text, hmmscan3-domtab,
hmmsearch3-domtab, infernal-tab, infernal-text, interproscan-xml,
phmmer3-domtab
```

Verified write formats:

```text
blast-tab, blast-xml, blat-psl, hmmer3-tab, hmmscan3-domtab,
hmmsearch3-domtab, phmmer3-domtab
```

Use format-specific keyword arguments when required. Examples include `comments=True` for commented BLAST tabular files and selecting the correct HMMER domain-table flavor (`hmmscan3-domtab`, `hmmsearch3-domtab`, or `phmmer3-domtab`) so hit/query coordinates are interpreted correctly.

## SearchIO parsing workflow

Use `read` for exactly one query result and `parse` for files with zero, one, or many query results.

```python
from Bio import SearchIO

qresult = SearchIO.read("results.xml", "blast-xml")
for hit in qresult:
    best_hsp = hit[0]
    if best_hsp.evalue < 1e-5:
        print(qresult.id, hit.id, best_hsp.evalue)
```

For multi-query files:

```python
from Bio import SearchIO

for qresult in SearchIO.parse("results.tab", "blast-tab", comments=True):
    passing_hits = []
    for hit in qresult:
        if hit.hsps and min(hsp.evalue for hsp in hit.hsps) <= 1e-10:
            passing_hits.append(hit.id)
    print(qresult.id, passing_hits)
```

Index large result files when repeated random access is needed:

```python
from Bio import SearchIO

idx = SearchIO.index("results.xml", "blast-xml")
try:
    qresult = idx["query_id"]
finally:
    idx.close()
```

Use `index_db` for a reusable on-disk index when the search result file is large and stable. Rebuild the index when input files change.

## Writing and conversion

`SearchIO.write(qresults, handle, format)` returns a four-number tuple: number of `QueryResult`, `Hit`, `HSP`, and `HSPFragment` objects written.

```python
from Bio import SearchIO

qresults = SearchIO.parse("results.xml", "blast-xml")
counts = SearchIO.write(qresults, "filtered.tab", "blast-tab")
assert len(counts) == 4
```

Writer limitations are format-specific. A writer may require attributes that a parser did not supply or that filtering removed. If writing fails, inspect the missing attribute and choose a richer source format, a different output format, or a custom export table.

`SearchIO.convert(in_file, in_format, out_file, out_format, ...)` is a shortcut for parse-then-write and inherits the same writer restrictions.

## Bio.Blast parsing and writing

Use `Bio.Blast` when the task is specifically BLAST XML record parsing/writing through the current BLAST record classes rather than the generic SearchIO model.

Installed public signatures:

```text
Blast.parse(source)
Blast.read(source)
Blast.write(records, destination, fmt='XML')
Blast.qblast(program, database, sequence, ..., format_type='XML', ...)
```

Parsing rules:

- `Blast.parse(source)` returns an iterator-like `Bio.Blast.Records` object over BLAST XML records.
- `Blast.read(source)` returns exactly one BLAST record and raises if there are zero or more than one records.
- The source can be a file path or a binary-mode stream. If opening a stream yourself, use binary mode such as `open(path, "rb")`.
- `Blast.write(records, destination, fmt="XML")` writes XML or XML2 and returns the number of records written. File-like destinations must be binary-mode writable.

Minimal pattern:

```python
from Bio import Blast

with open("blast.xml", "rb") as handle:
    record = Blast.read(handle)
print(record.query.id, len(record))
```

Use `SearchIO` instead when downstream code expects `QueryResult`/`Hit`/`HSP` filtering, coordinate normalization, or conversion among BLAST tabular/XML and other search formats.

## qblast safety policy

`Bio.Blast.qblast` submits a remote BLAST search and polls for results. Treat it as a network operation, not as a parser. Do not call it in offline verification or smoke scripts.

Before using `qblast` in a downstream task, require all of the following:

1. The user explicitly requested a live NCBI BLAST search or approved network use.
2. The program is one of `blastn`, `blastp`, `blastx`, `tblastn`, or `tblastx`.
3. The database name, sequence, expected output format, and hit limits are clear.
4. Contact metadata is configured with `Bio.Blast.email` and, if appropriate, `Bio.Blast.tool`.
5. The workflow avoids parallel burst submissions and respects slow polling. Public-service polling should not contact the server more often than once every 10 seconds overall or once per minute for a single request id.
6. For many searches, batch or schedule responsibly; avoid submitting more than 50 public searches in a busy interactive window.

`qblast` returns a binary response stream with BLAST data and also attaches request metadata such as `rid` and `rtoe`. Save the returned stream immediately if the result is important, then parse the saved data with `Bio.Blast` or `SearchIO`.

## Local BLAST and other external search tools

Biopython can parse outputs from local BLAST+, HMMER, BLAT, FASTA, Infernal, Exonerate, HH-suite, and InterProScan via `SearchIO`, but those command-line tools are not part of the base Biopython package. If the user asks to run a local search:

- check that the executable is installed and that the database/index exists;
- run tools through a safe subprocess call with explicit arguments and a bounded output path;
- parse the generated output with the matching `SearchIO` format;
- keep external-tool setup and long-running database builds out of default verification.
