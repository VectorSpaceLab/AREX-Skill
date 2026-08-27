# G2P reference

`gget.g2p` wraps the public Genomics 2 Proteins REST API and uses public
UniProt REST lookups when one side of the gene/UniProt pair is omitted. It
needs network access, but no credential. The live signature is:

```python
gget.g2p(
    gene: str | None = None, uniprot_id: str | None = None,
    resource: str = "features", isoform: str | None = None,
    residues: int | list[int] | tuple[int, ...] | range | set[int] | None = None,
    save: bool = False, out: str | None = None, verbose: bool = True,
) -> pandas.DataFrame | None
```

At least one of `gene` or `uniprot_id` is required. Passing both is best for
reproducibility because it makes the intended pair explicit and allows the
G2P endpoint to reject a mismatched pair rather than silently choosing another
protein.

## Resource selection

| `resource` | What it returns | Required identifiers |
|---|---|---|
| `features` | Per-residue table, about 140 columns: pLDDT, DSSP/ASA, UniProt sites, PTMs, pockets, interactions, bonds, PFES, MaveDB scores, and related annotations | gene or UniProt; the pair is resolved if one is absent |
| `map` | Gene → transcript → protein isoform → structure identifier map | gene or UniProt |
| `alignment` | Residue-level alignment between two UniProt isoforms | explicit canonical `uniprot_id` and alternative `isoform` |

A successful result always prepends `gene_name` and `uniprot_id` columns and
stores the same values in `df.attrs`. This invariant holds for gene-only,
UniProt-only, and paired calls. For `map`, gget adds `PDB Ids List` immediately
after the comma-joined `PDB Ids` column; each populated entry is a list of
strings. The stable BRCA1 map test expects these columns:

```text
gene_name, uniprot_id, UniProtKB, UniProt Isoform,
Ensembl Gene Id, Ensembl Protein Id, Ensembl Transcript Id,
RefSeq mRNA Id, PDB Ids, PDB Ids List
```

The exact feature columns are wide and can evolve. Assert stable columns such
as `residueId`, `AA`, and `AlphaFold confidence (pLDDT)` rather than hard-coding
the entire table.

## Identifier resolution and isoforms

- **Gene only:** gget queries UniProt with `gene_exact:<gene> AND
  organism_id:9606 AND reviewed:true`, asks for up to five accessions, and
  chooses the first reviewed human Swiss-Prot result. This is approximate for
  synonyms/paralogues and does not cover non-human, unreviewed, or specific
  isoform intent. The candidate count is logged when more than one matches.
- **UniProt only:** gget queries the UniProt entry JSON and extracts the primary
  gene symbol. The lookup is cached in-process (up to 256 keys).
- **Alignment:** pass the canonical isoform explicitly, for example
  `uniprot_id="P01130-1", isoform="P01130-2"`. Gene-only resolution returns a
  base accession and cannot disambiguate isoforms, so it is rejected.
- A mismatched but syntactically valid gene/accession pair can make G2P return
  a JSON failure body over HTTP 200; gget recognizes this and returns `None`.

```python
import gget

# Explicit pair: recommended for an analysis record.
features = gget.g2p("BRCA1", uniprot_id="P38398", resource="features")

# Either side can be resolved for a quick human canonical lookup.
map_df = gget.g2p(uniprot_id="P38398", resource="map")
map_df = gget.g2p("BRCA1", resource="map")

# Explicit isoforms are mandatory for alignment.
alignment = gget.g2p(
    uniprot_id="P01130-1", resource="alignment", isoform="P01130-2"
)
```

## Residue filtering and files

`residues` is a client-side filter applied after the full `features` or
`alignment` TSV is fetched. It accepts an int, list/tuple/set of ints, or a
Python `range`; booleans and strings are rejected. It does not apply to `map`.
If the response lacks `residueId`, gget warns and leaves the result unfiltered.
If requested positions are absent, it returns the available matches and logs
the missing positions.

```python
selected = gget.g2p(
    "BRCA1", uniprot_id="P38398", resource="features",
    residues=[185, 1775, 1812],
)
segment = gget.g2p(
    "LDLR", uniprot_id="P01130-1", resource="alignment",
    isoform="P01130-2", residues=range(100, 200),
)
```

`out="path/file.csv"` takes precedence over `save=True`. `save=True` uses the
current directory and the generated name
`gget_g2p_<gene>_<uniprot_id>_<resource>.csv`. The function writes CSV with the
canonical pair in the first columns, so the identifiers survive serialization.
Check the file and its header before passing it to another tool. This Python
function does not expose a JSON-return flag; the CLI has `--csv` output mode.

## Public API limits and routing

The feature table may include predicted structure annotations, but this skill
does not download raw PDB files or run AlphaFold. For a `PDB Ids List`, route
actual structure retrieval to sequence-tools. The public G2P API does not
expose the portal web UI's gnomAD, ClinVar, or HGMD overlays. If a user needs
those variant layers, record the limitation and direct them to the G2P portal
rather than fabricating columns from the feature table.

The G2P TSV helper retries connection errors, timeouts, and HTTP 5xx responses
three times after delays of 1, 2, and 4 seconds. It treats an empty body, a
JSON-shaped failure body, non-5xx HTTP errors, or an exhausted retry as a
failed query and returns `None` (with a diagnostic log). UniProt resolution
failures generally lead to a `ValueError` explaining how to pass the other
identifier.

## Validation and recovery

1. Validate the pair before an expensive feature request. For a known stable
   case, `BRCA1/P38398` should produce more than 100 feature rows and include
   `residueId`; `BRCA1/P01130` should return `None` rather than a one-column
   pseudo-table.
2. For alignment, confirm both isoforms are accession strings with the intended
   `-1`/`-2` suffixes. Passing a gene-only request is a validation error.
3. For resolution ambiguity, inspect the log and switch to an explicit
   accession; do not treat the first human reviewed Swiss-Prot hit as universal.
4. For a `None` result, retry a small `map` request with the explicit pair,
   inspect network/HTTP diagnostics, and then check G2P's portal availability.
   A successful HTTP response with no rows is still not evidence that the gene
   lacks annotations.
5. For a wide feature table, record the column list, resource, pair, residue
   filter, retrieval date, and output path. Do not merge rows from different
   isoforms without an explicit alignment step.
