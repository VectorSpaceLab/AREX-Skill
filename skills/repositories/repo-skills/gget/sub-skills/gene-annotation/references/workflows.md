# Gene annotation workflows

These recipes use only the public gget interfaces. They are network-bound and
should be run with a bounded ID count and an output directory that is safe to
write. All examples keep `verbose=False` after the first successful probe so
that returned values remain easy to inspect.

## 1. Resolve a symbol to a species-specific canonical protein

```python
import json
import gget

hits = gget.search(
    ["ace2", "angiotensin converting enzyme 2"],
    species="homo_sapiens",
    id_type="gene",
    andor="or",
    limit=10,
    verbose=False,
)
if hits is None or hits.empty:
    raise LookupError("No species-specific Ensembl hit")

# Select by an explicit criterion; do not assume the first row is correct.
rows = hits[hits["gene_name"].str.upper().eq("ACE2")]
if rows.empty:
    raise LookupError("ACE2 was not returned")
ens_id = rows.iloc[0]["ensembl_id"]

meta = gget.info(
    ens_id,
    ncbi=False,
    pdb=False,
    json=True,
    verbose=False,
)
if not meta:
    raise LookupError(f"No metadata for {ens_id}")
reported_id, record = next(iter(meta.items()))
canonical = record.get("canonical_transcript")
if not canonical:
    raise LookupError(f"No canonical transcript reported for {reported_id}")

fasta_lines = gget.seq(reported_id, translate=True, verbose=False)
if not fasta_lines:
    raise LookupError("No UniProt sequence for canonical transcript")
if not fasta_lines[0].startswith(">") or len(fasta_lines) % 2:
    raise ValueError("Unexpected FASTA-line output")
json.dump(
    {"gene": reported_id, "canonical_transcript": canonical, "fasta": fasta_lines},
    open("ace2_canonical_protein.json", "w"),
    indent=2,
)
```

The result is JSON-compatible because the FASTA list contains strings. The
metadata object is useful for retaining the exact current Ensembl ID and
canonical transcript, but `seq` will still query current UniProt data and may
return a different current cross-reference than an older release.

CLI equivalent (JSON metadata and FASTA output):

```bash
gget search -s human -t gene -l 20 ace2 "angiotensin converting enzyme 2" > hits.json
gget info ENSG00000130234 --ncbi --pdb --out ace2_info.json
gget seq --translate ENSG00000130234 --out ace2_protein.fa
```

The numeric ID in the CLI example is illustrative; use the ID selected from
`hits.json`, not a copied ID from a different species.

## 2. Search for transcripts, then retrieve nucleotide isoforms

```python
import gget

hits = gget.search(
    "sprr2a", "homo_sapiens", id_type="transcript", limit=5, verbose=False
)
if hits is None or hits.empty:
    raise LookupError("No transcript hit")
transcript_id = hits.iloc[0]["ensembl_id"]

# Metadata works for a transcript and identifies its parent gene/object type.
meta = gget.info(transcript_id, ncbi=False, uniprot=False, verbose=False)
if meta is None:
    raise LookupError("Transcript metadata was not found")

# A transcript request is one record even if isoforms=True; the flag is for genes.
fasta_lines = gget.seq(transcript_id, isoforms=True, translate=False, verbose=False)
assert fasta_lines and fasta_lines[0].startswith(">")
```

To enumerate all transcript sequences, pass the parent **gene** ID to
`gget.seq(gene_id, isoforms=True)`. In nucleotide mode each returned pair is
an Ensembl transcript header and its sequence. In protein mode the same gene
request asks UniProt for each transcript; transcripts without protein matches
are omitted.

## 3. Handle a versioned transcript without a UniProt match

A versioned ID is not a historical-release selector. `info` and `seq` strip a
dot-version from IDs beginning with `ENS` and use the latest record. Diagnose a
missing protein without silently changing species or transcript:

```python
import gget

versioned = "ENST00000000000.99"  # replace with the requested ID
meta = gget.info(versioned, ncbi=False, uniprot=True, verbose=True)
if meta is None:
    raise LookupError("Ensembl did not recognize the normalized transcript")

# Inspect metadata and the current Ensembl-reported version.
key, record = next(iter(meta.items()))
print(key, record.get("uniprot_id"), record.get("object_type"))
protein = gget.seq(versioned, translate=True, verbose=True)
if not protein:
    # Preserve the exact failure; retrieve nucleotide sequence only as a
    # clearly labeled fallback, not as an amino-acid substitution.
    nucleotide = gget.seq(versioned, translate=False, verbose=True)
```

Interpret an empty protein result as “no UniProt sequence returned for the
current transcript mapping,” not as proof that the transcript has no coding
sequence. Check `object_type`, `biotype`, `canonical_transcript`, and the
reported UniProt field. If an exact historical version is required, obtain and
record the matching release reference files with `gget.ref` and use a separate
release-aware sequence workflow; `gget.seq` itself has no release parameter.

## 4. Discover release-aware reference files

```python
import gget

refs = gget.ref(
    "mus_musculus",
    which=["gtf", "dna", "pep"],
    release=110,
    verbose=False,
)
for label, item in refs["mus_musculus"].items():
    if not item["ftp"]:
        raise RuntimeError(f"No FTP for {label}")
    print(label, item["ensembl_release"], item["ftp"], item["bytes"])
```

Use `ftp=True` when a downstream command expects URL arguments:

```python
urls = gget.ref("homo_sapiens", which=["dna", "gtf"], ftp=True)
assert len(urls) == 2
```

To discover valid species before a large request:

```python
vertebrates = gget.ref(None, list_species=True, release=110, verbose=False)
invertebrates = gget.ref(None, list_iv_species=True, verbose=False)
```

The list operations are remote directory scans. They require no species
positional value, but they can be slow and should not be repeated in a loop.
The CLI `--download` mode uses curl and `--out_dir`; the Python API returns
links and metadata rather than downloading files.

## 5. Output validation and reproducibility record

For every network result, record:

- input symbols/IDs exactly as submitted and the normalized/reported ID;
- species shortcut or full name, explicit core database, and `release` where
  applicable;
- `id_type`, `andor`, `limit`, `translate`, `isoforms`, provider flags, and
  output mode;
- the returned `ensembl_release` for `ref`, DataFrame/JSON keys for metadata,
  and FASTA headers for sequences;
- whether a provider was unavailable, rate-limited, or returned no match.

For DataFrame output, check `result.columns`, `result.shape`, and nulls before
indexing. For JSON output, check whether the value is a list (`search`) or a
dictionary keyed by ID (`info`/`ref`). For FASTA output, require alternating
header/sequence lines, nonempty sequences, and a header that names the actual
query or transcript. Do not compare sequences in this skill; route that work
to **sequence-tools**.
