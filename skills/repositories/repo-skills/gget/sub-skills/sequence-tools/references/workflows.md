# Sequence-tools workflows

These recipes are designed to be copied after substituting the user's own inputs. They keep remote work separate from local work and make type/orientation decisions explicit.

## 1. Inspect and normalize a small sequence input

For a literal, first determine whether it is nucleotide or protein. Do not rely on automatic detection when the sequence contains only DNA letters but is biologically a peptide. For a FASTA, ensure every header has a following sequence and check record count/length before invoking a tool.

```python
from pathlib import Path

path = Path("queries.fa")
text = path.read_text(encoding="utf-8")
if not text.startswith(">"):
    raise ValueError("FASTA must start with '>'")
records = [block for block in text.split(">") if block.strip()]
print("records:", len(records))
for block in records:
    header, *lines = block.splitlines()
    seq = "".join(lines).replace(" ", "").upper()
    print(header, len(seq), sorted(set(seq)))
```

The gget BLAST/BLAT wrappers accept `.fa`/`.txt` paths but submit only record one. If all records matter, loop intentionally and respect the remote service's rate limits; do not assume passing a multi-record FASTA submits a batch.

## 2. Remote protein search then structure retrieval

Use this when a peptide has no known structure ID but similar deposited structures may exist.

```python
import gget

protein = "MKWMFKEDHSLEHRCVESAKIRAKY"
hits = gget.blast(protein, program="blastp", database="pdbaa", limit=10, expect=10.0)
if hits is not None and not hits.empty:
    print(hits[["Description", "Accession"]].head())
    # Select and manually verify an accession/PDB ID from the result.
    structure = gget.pdb("4ACQ", resource="mmcif", save=True)
```

The BLAST result is remote evidence, not an automatic authorization to fetch every hit. Validate the selected four-character PDB ID and use `resource="mmcif"` for large structures. If you need Ensembl-to-sequence resolution first, route to `gene-annotation` rather than passing an Ensembl ID to BLAST.

## 3. Locate a sequence on a genome with BLAT

```python
import gget

locations = gget.blat(
    "ATGCTGAATTTATGCTGAATTTATGCTGAATTTATGCTGAATTT",
    seqtype="DNA",
    assembly="mouse",  # maps to mm39
)
if locations is None:
    print("No match or UCSC rejected the request")
else:
    print(locations.sort_values("%_matched", ascending=False).head())
```

For a protein, set `seqtype="protein"`; for translated searches use the literal encoded choice (`translated%20RNA` or `translated%20DNA`). Inspect `genome` because an invalid assembly can result in UCSC's default genome. Keep a sequence under 8,000 residues/characters or record that gget truncated it. A very short input can legitimately yield no match.

## 4. Persist a local MUSCLE alignment

A two-record local FASTA is a deterministic novice workflow and does not require a remote service:

```python
import gget

gget.muscle("queries.fa", super5=False, out="results/aligned.afa", verbose=True)
```

After completion, verify `results/aligned.afa` exists, begins with FASTA headers, and contains equal-length aligned sequences. Use `super5=True` for a few hundred sequences or when the input is too large for PPP's time/memory budget:

```python
gget.muscle("many_proteins.fa", super5=True, out="results/many.super5.afa")
```

Do not compare PPP and Super5 output character-for-character as if one were a correctness oracle; they are different MUSCLE v5 workflows. With no `out`, the wrapper prints a colored alignment and removes its temporary `.afa`, so use `out` whenever a later tool needs the alignment.

CLI equivalent:

```bash
gget muscle queries.fa --out results/aligned.afa
gget muscle many_proteins.fa --super5 --out results/many.super5.afa
```

If the local executable is missing or permission denied, stop and follow `references/troubleshooting.md`; do not retry indefinitely or substitute an unverified binary.

## 5. DIAMOND query/reference orientation

For protein-vs-protein local alignment:

```python
import gget

result = gget.diamond(
    query="queries.fa",             # sequences being searched
    reference="reference_proteins.fa",  # target database source
    sensitivity="very-sensitive",
    threads=2,
    out="diamond-run",
)
print(result[["query_accession", "subject_accession", "identity_percentage", "bit_score"]])
```

For translated DNA query against protein reference:

```python
result = gget.diamond(
    query="coding_dna.fa",
    reference="reference_proteins.fa",
    translated=True,
    threads=4,
)
```

Expected interpretation is always query→subject/reference. A reference sequence appearing as `query_accession` means the inputs were reversed or the CLI parser consumed a positional token incorrectly; it is not evidence that DIAMOND discovered a new reference. Prefer named Python arguments. On CLI, use:

```bash
gget diamond query.fa -ref reference_proteins.fa -s very-sensitive -t 2 -o diamond-run
```

Keep the positional query before `-ref`. Use `--translated` only for nucleotide query versus amino-acid reference. The output folder may contain TSV/CSV/JSON and a generated database basename; preserve it for inspection, but remember that the wrapper recreates a database each call and its current alignment command passes the reference-file path as `--db` after `makedb` creates the requested basename. See the database-lifecycle note in troubleshooting.

## 6. ELM motifs from a sequence or UniProt accession

One-time setup (requires `curl`, network, and write access):

```bash
gget setup elm
```

Then run both ortholog and regex workflows:

```python
import gget

ortholog_df, regex_df = gget.elm(
    "LIAQSIGQASFV",
    sensitivity="very-sensitive",
    threads=2,
)
print(ortholog_df.shape, regex_df.shape)
```

For a UniProt accession, set `uniprot=True` explicitly:

```python
ortholog_df, regex_df = gget.elm("Q02410", uniprot=True, expand=True)
```

`ortholog_df` reports experimentally validated ELM instances in local ortholog matches; `regex_df` reports direct motif-regex matches in the input sequence. Empty results are informative. `expand=True` is useful for provenance review but increases the regex-table columns and payload. Do not put a custom setup output directory in the expectation that `gget.elm` will read it; setup's default package location is the one the wrapper checks.

## 7. PDB metadata and modern structure format

```python
import gget

entry = gget.pdb("4ACQ", resource="entry")
assembly = gget.pdb("1RH7", resource="assembly", identifier=1)
chain = gget.pdb("4G22", resource="polymer_entity_instance", identifier="A")
mmcif = gget.pdb("4ACQ", resource="mmcif", save=True)
```

Use an `identifier` for assembly/entity/chain resources. Metadata is a decoded JSON object; structures are raw text. With `resource="pdb"`, gget tries legacy PDB endpoints and transparently returns mmCIF if no legacy file is available. If a caller requires a `.pdb` grammar, request a structure known to have legacy PDB or handle the returned `.cif` fallback explicitly.

## 8. AlphaFold only after a runtime preflight

Do not launch a full prediction as a smoke test. First verify an AlphaFold installation, OpenMM if relaxation is requested, `pdbfixer`, model parameters, the Jackhmmer executable, writable temporary storage, and network access to the MSA database. Then use a small protein:

```python
import gget

gget.alphafold(
    "MAAHKGAEHHHKAAEHHEQAAKHHHAAAEHHEQAAHHADTAYAHHKHAEEHAAQAAKHD",
    out="prediction",
    relax=False,
    plot=False,                 # suitable for headless execution
    jackhmmer_savedir="scratch",
)
```

For a complex, pass a list of amino-acid sequences; gget automatically selects the multimer model. `multimer_for_monomer=True` deliberately uses multimer for one chain, and `multimer_recycles=20` trades runtime/memory for additional recycling. A successful run should leave `prediction/selected_prediction.pdb` and `prediction/predicted_aligned_error.json`. Treat pLDDT/PAE as model confidence outputs, not experimental validation. For new production predictions, prefer a maintained AlphaFold service/tool and retain gget only when its simplified, no-template workflow is specifically wanted.

## 9. Chained local/remote comparison

A reproducible structure-comparison route is:

1. Obtain an amino-acid FASTA with `gene-annotation` if the source is an Ensembl transcript.
2. Run `blast(..., database="pdbaa")` to identify candidate PDB-related hits.
3. Manually select and validate candidate IDs, then fetch `pdb(..., resource="mmcif")`.
4. Optionally run `alphafold` only after the expensive runtime preflight.
5. Compare structures in a dedicated viewer or analysis package; gget does not align or validate 3D structures.

This sequence preserves the distinction between ID lookup, remote homology evidence, experimental structure retrieval, and prediction.
