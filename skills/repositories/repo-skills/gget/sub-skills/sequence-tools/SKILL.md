---
name: sequence-tools
description: "Use gget for remote BLAST/BLAT searches, local MUSCLE/DIAMOND
  alignment, ELM motif analysis, RCSB PDB retrieval, and the optional AlphaFold
  prediction workflow."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# Sequence tools

Use this route when the task is sequence similarity/location, multiple-sequence alignment, protein motif discovery, structure retrieval, or protein structure prediction. The public Python API is `gget.<tool>(...)`; the CLI is `gget <tool> ...`. Start with a literal sequence or a small FASTA path and decide whether the operation is remote or local before running it.

## Route and safety

- Route Ensembl/WormBase/FlyBase lookup or gene/transcript FASTA acquisition with `gget.seq` to `gene-annotation`.
- Route mutation generation to `specialized-workflows`; do not use alignment tools as a mutation engine.
- Route G2P portal annotations and disease/target queries to `disease-structure`. PDB retrieval and AlphaFold prediction stay here.
- `blast` and `blat` submit data to NCBI and UCSC. Expect network latency, changing databases, rate limits, and empty/no-match results.
- `muscle` and `diamond` are local subprocess workflows. The generated skill does not ship gget's platform binaries; verify executable availability and permissions before a production run.
- `elm` is local after a one-time ELM data download, but UniProt fallback and setup use the network. ELM data is licensed for non-commercial use according to the ELM license.
- AlphaFold is optional, computationally expensive, network-heavy, and no longer actively maintained by gget. Prefer ColabFold or the AlphaFold Server for new predictions.

## Choose the operation

| Goal | Tool | Main input | Main output |
|---|---|---|---|
| Remote nucleotide/protein similarity | `blast` | one sequence or first record of `.fa`/`.txt` | DataFrame, JSON records, or saved CSV/JSON |
| Genomic/protein location | `blat` | one sequence or first record of `.fa`/`.txt` | DataFrame, JSON records, or saved CSV/JSON |
| Local MSA | `muscle` | list of sequences or FASTA/text path | printed Clustal-style view or `.afa` |
| Local protein/translated search | `diamond` | query plus required reference | DataFrame, JSON records, or output folder |
| Eukaryotic linear motifs | `elm` | amino-acid sequence or UniProt accession | ortholog and regex result tables |
| Experimental structure/metadata | `pdb` | PDB entry ID plus resource | raw PDB/mmCIF text or JSON |
| Predicted protein structure | `alphafold` | amino-acid sequence(s) or FASTA | PDB and PAE JSON files in a folder |

Detailed signatures, schemas, and CLI mappings are in [`references/api-reference.md`](references/api-reference.md). Recipes are in [`references/workflows.md`](references/workflows.md). Always consult [`references/troubleshooting.md`](references/troubleshooting.md) when validation or a remote/local dependency fails.

## Input discipline

1. A Python string can be a literal sequence or a path. For BLAST/BLAT, a `.fa` or `.txt` path is parsed and **only its first sequence is submitted**. MUSCLE and DIAMOND accept a FASTA path or sequence/list input; AlphaFold accepts a FASTA/text path or sequence/list. Use ordinary FASTA headers beginning with `>` and put sequence characters on following lines.
2. `gget` uppercases remote-search sequences. Its default type detection treats a string containing only `A`, `T`, `G`, `C`, and `N` as nucleotide; otherwise it may classify valid amino-acid letters as protein. A protein made only of DNA letters is ambiguous: set BLAST `program`/`database` or BLAT `seqtype` explicitly.
3. Do not pass a gene symbol, Ensembl ID, PDB ID, or UniProt accession as a sequence. Resolve identifiers first with the appropriate route, except for `elm(..., uniprot=True)` and `pdb`.
4. Validate alphabet, length, header/sequence pairing, and intended query/reference orientation before starting a remote request or local subprocess. A malformed FASTA raises from the shared parser rather than producing a trustworthy result.

## Fast Python starts

```python
import gget

hits = gget.blast("MKWMFKEDHSLEHRCVESAKIRAKY", database="nr", limit=10)
locations = gget.blat("ATGCTGAATTTATGCTGAATTTATGCTGAATTT", assembly="human")
gget.muscle(["MSSSSWLLLSLVAVTAAQST", "MSSSSWLLLSLVEVTAAQST"], out="aligned.afa")
aln = gget.diamond("MPEPTIDE", reference="reference.fa")
ortho_df, regex_df = gget.elm("LIAQSIGQASFV")
entry = gget.pdb("4ACQ", resource="entry")
```

Python defaults are generally DataFrames for tabular tools; use `json=True` where supported. `muscle` and `alphafold` return `None` and communicate through files/stdout. `pdb` returns text for `pdb`/`mmcif` and JSON-like objects for metadata resources. Save behavior is tool-specific; do not assume every `save` or `out` argument names the same kind of path.

## Fast CLI starts

```bash
gget blast "MKWMFKEDHSLEHRCVESAKIRAKY" --database nr --limit 10
gget blat "ATGCTGAATTTATGCTGAATTTATGCTGAATTT" --assembly human
gget muscle sequences.fa --out aligned.afa
gget diamond query.fa -ref reference.fa -o diamond-results
gget setup elm
gget elm LIAQSIGQASFV -o elm-results
gget pdb 4ACQ -r mmcif -o 4ACQ.cif
# Only after installing and checking the optional runtime:
gget alphafold protein.fa -o prediction
```

On the CLI, tabular commands print CSV by default; `--csv` selects JSON output where implemented. `--quiet` suppresses progress. `gget diamond` uses a positional `query` followed by required `-ref/--reference`; keep those positional arguments before the option to avoid argparse consuming a reference-looking sequence as another query.

## Remote search/location

- BLAST: choose `blastn`/`blastp`/translated mode and a compatible database when auto-detection is not unambiguous. `limit` controls returned descriptions/hits and `expect` is the cutoff. NCBI's service rules matter: do not submit more often than once per 10 seconds or poll one RID more often than once per minute; schedule batches of more than 50 searches in the documented off-hours.
- BLAT: choose `DNA`, `protein`, `translated%20RNA`, or `translated%20DNA`; aliases map `human`→`hg38`, `mouse`→`mm39`, and `zebrafinch`→`taeGut2`. The implementation truncates input over 8,000 characters. An unrecognized assembly can be served as UCSC's default genome, so inspect the returned `genome` column.

## Local analysis and structure

- MUSCLE uses PPP by default and `super5=True` for larger inputs (the docs suggest a few hundred sequences) to reduce time/memory. Set `out="...afa"` to persist aligned FASTA; with no `out`, gget creates and removes a temporary alignment after printing a colored view.
- DIAMOND is a local protein search. Normal mode is protein query against protein reference (`blastp`); `translated=True` is nucleotide query against amino-acid reference (`blastx`). The `diamond_db` and `out` lifecycle, including a source-level database-path quirk, is documented in the API and troubleshooting references.
- ELM requires the four local files installed by `gget setup elm`. It returns `(ortholog_df, regex_df)`: the first contains experimentally validated motif information found through DIAMOND orthologs, and the second contains direct regex matches. `expand=True` adds validation protein/organism/reference columns to the regex table.
- PDB resource `pdb` first tries legacy downloads and falls back to mmCIF for unavailable large structures. Use `resource="mmcif"` explicitly when downstream software accepts it; inspect the actual returned text and saved extension.
- AlphaFold validates sequences before downloading MSA databases and running Jackhmmer/model inference. A monomer is capped at 2,500 residues, each sequence at 3,400, and total input at 3,400; the implementation warns above 3,000 and can exhaust memory/disk.

## Output semantics

- A DataFrame is convenient for filtering and column selection; choose `json=True` for JSON-compatible records, but remember that tuple-returning ELM has two separate tables.
- `save=True` on Python remote tools writes fixed filenames in the current directory, while `out` on DIAMOND/ELM/AlphaFold is a folder and `out` on MUSCLE/PDB is normally a file path.
- A `None` return can mean no match, an upstream error, or an optional runtime branch; read the log and validate inputs before treating it as biological absence.
- Structure text is not JSON: preserve the format reported by PDB and use a parser appropriate for PDB or mmCIF.
- Alignment files should be checked for headers, sequence count, and equal aligned lengths before downstream use.

## Completion checklist

- Confirm sequence type and query/reference orientation.
- Record exact tool, database/assembly/resource, sensitivity, limits, and output path.
- For remote calls, retain the returned table/object and note no-match or throttling messages.
- For local calls, check the binary version/permissions and verify an expected output file is non-empty and parseable.
- For AlphaFold, verify `selected_prediction.pdb` and `predicted_aligned_error.json` in `out`; do not infer biological confidence beyond the supplied pLDDT/PAE values.
