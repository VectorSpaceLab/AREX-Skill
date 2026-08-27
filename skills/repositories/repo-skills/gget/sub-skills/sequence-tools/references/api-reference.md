# Sequence-tools API reference

The tables below describe the public contract of gget's sequence modules, English documentation, CLI, tests, and small fixtures. Internal package paths and vendored binaries are deliberately not runtime dependencies.

## Shared input and output rules

`blast`, `blat`, and `alphafold` use the package FASTA reader when a string looks like a `.fa` or `.txt` path. The reader requires a first line beginning with `>` and a sequence line after each header; consecutive headers raise `ValueError`. BLAST and BLAT submit only the first record and warn/log when more records are present. A nonexistent path raises `FileNotFoundError`. A path with an unsupported extension raises `ValueError`.

Literal sequence strings are uppercased by BLAST/BLAT. Default nucleotide detection accepts only `A`, `T`, `G`, `C`, and `N`; the protein set includes standard amino-acid letters and ambiguity symbols. Explicit type/program settings are safer for an ambiguous protein or translated workflow. A string containing a dot is treated as a possible path by these modules, so a literal containing a dot should be passed carefully or put in a FASTA file.

For tabular functions, Python returns a pandas `DataFrame` unless `json=True`, in which case it returns JSON-compatible list-of-dictionary records. `save=True` in BLAST/BLAT writes fixed names in the current directory (`gget_blast_results.csv/.json` or `gget_blat_results.csv/.json`). The CLI instead uses `-o/--out` and prints CSV by default; its `--csv` flag selects JSON output (the parser's internal boolean is named `csv`, but is passed as `json=True`).

## BLAST

```python
gget.blast(
    sequence: str,
    program: str = "default",
    database: str = "default",
    limit: int = 50,
    expect: float = 10.0,
    low_comp_filt: bool = False,
    megablast: bool = True,
    verbose: bool = True,
    wrap_text: bool = False,
    json: bool = False,
    save: bool = False,
) -> pandas.DataFrame | list[dict] | None
```

`sequence` is a literal or a `.fa`/`.txt` path. `program` is one of `blastn`, `blastp`, `blastx`, `tblastn`, or `tblastx`; with `default`, nucleotide-like input chooses `blastn`, otherwise protein-like input chooses `blastp`. `database` is one of `nt`, `nr`, `refseq_rna`, `refseq_protein`, `swissprot`, `pdbaa`, or `pdbnt`. With defaults, nucleotide chooses `nt` and protein chooses `nr`. If a program is explicit, a non-default database is required. Invalid program/database combinations raise `ValueError` before network submission.

`limit` is passed as both description and hit-list limit. `expect` is the E-value cutoff; `low_comp_filt=True` enables low-complexity filtering. `megablast=True` enables MegaBLAST for `blastn` (the remote service ignores it where not applicable). `wrap_text=True` only prepares a wrapped copy of the description column; the returned table remains the normal result table. A successful result table contains the NCBI description table fields such as Description, Scientific Name, taxid, scores, query coverage, E-value, and accession. No significant similarity, expired/failed RID, or unexpected status logs an error and returns `None`.

The remote implementation waits at least 11 seconds before its first fetch and 61 seconds between unsuccessful status polls. Follow NCBI's stated service rules and do not use this as a high-volume parallel client. For a protein sequence against structures, use `database="pdbaa"`; for nucleotide-to-protein translated search, choose a compatible explicit program/database rather than relying on type detection.

CLI essentials:

```text
gget blast SEQUENCE [-p PROGRAM] [-db DATABASE] [-l LIMIT] [-e EXPECT]
                 [-lcf] [-mbo] [-o OUTPUT] [--csv] [--quiet]
```

`--mbo` turns MegaBLAST off. `--csv` makes the CLI write/print JSON false, i.e. CSV; without it the CLI uses JSON output. The deprecated `-seq/--sequence` option is accepted, but a positional sequence is the current interface.

## BLAT

```python
gget.blat(
    sequence: str,
    seqtype: str = "default",
    assembly: str = "human",
    json: bool = False,
    save: bool = False,
    verbose: bool = True,
) -> pandas.DataFrame | list[dict] | None
```

`seqtype` is `DNA`, `protein`, `translated%20RNA`, or `translated%20DNA`. `default` detects DNA versus protein. `assembly="human"`/`"homo_sapiens"` maps to `hg38`; `mouse`/`mus_musculus` maps to `mm39`; `zebrafinch`/`taeniopygia_guttata` maps to `taeGut2`; any other string is sent as the short UCSC assembly name. UCSC may fall back to its default genome for an unrecognized assembly, so inspect the returned `genome` value rather than trusting the request.

Input longer than 8,000 characters is truncated to the first 8,000 characters. UCSC results are normalized to columns:

```text
genome, query_size, aligned_start, aligned_end, matches, mismatches,
%_aligned, %_matched, chromosome, strand, start, end
```

Coordinates are adjusted to the website's one-based display. No matches, a too-short sequence (the service commonly requires around 20 bases/residues), or a bad assembly can return `None`. Transient HTTP 429/5xx, network, and non-JSON throttle pages are retried four times with exponential backoff. `save=True` writes `gget_blat_results.csv` or `gget_blat_results.json` in the current directory.

CLI:

```text
gget blat SEQUENCE [-st {DNA,protein,translated%20RNA,translated%20DNA}]
                [-a ASSEMBLY] [-o OUTPUT] [--csv] [--quiet]
```

## MUSCLE 5

```python
gget.muscle(
    fasta: str | list[str],
    super5: bool = False,
    out: str | None = None,
    verbose: bool = True,
) -> None
```

`fasta` is a FASTA/text path, a literal sequence, or a list of sequences. A one-element list is treated as its single item. With `super5=False`, gget invokes MUSCLE v5 `-align INPUT -output OUTPUT` (PPP workflow). With `super5=True`, it invokes `-super5 INPUT -output OUTPUT`; use this for a few hundred sequences or when time/memory is more important than the PPP choice. The input type may be nucleotide or amino acid; validate that all records represent the intended molecule type before alignment.

With `out="path/results.afa"`, the parent directory is created and the aligned FASTA remains there. With `out=None`, an ephemeral `.afa` is read back and printed as a colored Clustal-style view, then removed; the Python function still returns `None`. The CLI's positional `fasta` accepts one or more strings, `--super5` selects Super5, and `--out` is the persistent `.afa` path.

The package normally selects a platform-specific bundled MUSCLE executable and attempts `chmod 755`; if unavailable it tries the source compiler on Linux/macOS. This generated skill does not copy that executable or compiler checkout. A failed executable load should be diagnosed as a local environment problem, not confused with malformed sequence input.

## DIAMOND

```python
gget.diamond(
    query: str | list[str],
    reference: str | list[str],
    translated: bool = False,
    diamond_db: str | None = None,
    sensitivity: str = "very-sensitive",
    threads: int = 1,
    diamond_binary: str | None = None,
    verbose: bool = True,
    json: bool = False,
    out: str | None = None,
) -> pandas.DataFrame | list[dict]
```

`query` is the sequence(s) to search; `reference` is the target sequence set. Each can be a literal, list, or FASTA path. The required reference is not optional. `translated=False` invokes DIAMOND `blastp` (protein query vs protein reference). `translated=True` invokes `blastx` (nucleotide query vs amino-acid reference). It does not mean that both inputs are nucleotide sequences.

Allowed `sensitivity` values are `fast`, `mid-sensitive`, `sensitive`, `more-sensitive`, `very-sensitive`, and `ultra-sensitive`. `threads` is passed to database creation and alignment. `diamond_binary` overrides the package-selected executable. `out` is a folder: it receives `DIAMOND_results.tsv`, and, for JSON mode, `gget_diamond_results.json`; CSV mode receives `gget_diamond_results.csv`. Without `out`, temporary input/output/database artifacts are deleted after reading the result.

The normal DataFrame/JSON schema is:

```text
query_accession, subject_accession, identity_percentage,
query_seq_length, subject_seq_length, length, mismatches, gap_openings,
query_start, query_end, subject_start, subject_end, e-value, bit_score
```

`diamond_db` is the database basename supplied to `makedb`; when omitted it is temporary, and when `out` is provided it defaults inside that output folder. Treat a custom database as a lifecycle/output path, not as a guarantee that the current wrapper reuses an already-built database: the implementation runs `version`, `makedb`, and alignment every call. In the inspected implementation, database creation uses `diamond_db`, while the subsequent alignment command passes the reference-file path as its `--db` argument. If a custom/reference-file run reports an invalid DIAMOND database, preserve the diagnostic and verify the wrapper/binary rather than deleting the reference or reversing the biological meaning of query/reference.

CLI syntax is intentionally asymmetric:

```text
gget diamond QUERY [QUERY ...] -ref REFERENCE [REFERENCE ...]
             [-x] [-db DB_BASENAME] [-s SENSITIVITY] [-t THREADS]
             [-bin BINARY] [-o OUTPUT_FOLDER] [--csv] [--quiet]
```

Put the positional query before `-ref`; otherwise an unoptioned token can be parsed as an additional query. In Python, keep `query=` and `reference=` named to avoid this class of error.

## ELM

```python
gget.elm(
    sequence: str,
    uniprot: bool = False,
    sensitivity: str = "very-sensitive",
    threads: int = 1,
    diamond_binary: str | None = None,
    expand: bool = False,
    verbose: bool = True,
    json: bool = False,
    out: str | None = None,
) -> tuple[pandas.DataFrame, pandas.DataFrame] | tuple[list[dict], list[dict]]
```

The default `sequence` is an amino-acid string. Set `uniprot=True` when it is a UniProt accession; gget first checks local ELM instances and may fetch the sequence from UniProt if the accession has no local ELM instance. For a raw amino-acid sequence, gget predicts direct regex motifs and uses DIAMOND against the local ELM instances FASTA to identify orthologous proteins. `sensitivity`, `threads`, and `diamond_binary` are forwarded to that local DIAMOND call.

Before the first run, execute `gget.setup("elm")` or `gget setup elm` with network and write access. The setup downloads four files: `elm_instances.fasta`, `elms_classes.tsv`, `elm_instances.tsv`, and `elm_interaction_domains.tsv`. A custom `setup(..., out=...)` location is only a separate raw copy; `gget.elm` reads the package's default data directory and will not automatically use that custom folder.

The return tuple is `(ortholog_df, regex_df)`. `ortholog_df` contains validated motif instances associated with DIAMOND-matched orthologs, alignment coordinates, identity, and `motif_inside_subject_query_overlap`. `regex_df` contains local regex matches, including `Instances (Matched Sequence)`, `motif_start_in_query`, and `motif_end_in_query`; `expand=True` adds protein names, organisms, and references. False-positive and true-negative instances are filtered. Empty tables are valid and are accompanied by warnings. With `out`, CSV mode writes `ELM_ortho_results.csv` and `ELM_regex_results.csv`; JSON mode writes corresponding `.json` files.

CLI:

```text
gget setup elm
gget elm SEQUENCE [-u] [-s SENSITIVITY] [-t THREADS] [-bin BINARY]
         [-e] [-o OUTPUT_FOLDER] [--csv] [--quiet]
```

## PDB

```python
gget.pdb(
    pdb_id: str,
    resource: str = "pdb",
    identifier: str | int | None = None,
    save: bool = False,
) -> Any
```

Allowed resources are `pdb`, `mmcif`, `entry`, `pubmed`, `assembly`, `branched_entity`, `nonpolymer_entity`, `polymer_entity`, `uniprot`, `branched_entity_instance`, `polymer_entity_instance`, and `nonpolymer_entity_instance`. `pdb` returns legacy structure text when available and automatically falls back to mmCIF; `mmcif` directly returns mmCIF text. All metadata resources return decoded JSON objects. `assembly` requires `identifier`; entity resources require an entity ID; instance resources require a chain ID. `save=True` writes structure text as `<pdb_id>.pdb` or `<pdb_id>.cif` based on what was actually fetched, and metadata as `<pdb_id>_<identifier>_<resource>.json` or `<pdb_id>_<resource>.json` in the current directory.

CLI:

```text
gget pdb PDB_ID [-r RESOURCE] [-i IDENTIFIER] [-o OUTPUT]
```

The CLI output path is managed by the command layer and can be a chosen file. Use explicit `resource="mmcif"`/`-r mmcif` for large structures or downstream tools that expect modern format.

## AlphaFold

```python
gget.alphafold(
    sequence: str | list[str],
    out: str | None = <date-time>_gget_alphafold_prediction,
    multimer_for_monomer: bool = False,
    relax: bool = False,
    multimer_recycles: int = 3,
    plot: bool = True,
    show_sidechains: bool = True,
    verbose: bool = True,
    jackhmmer_savedir: str | None = None,
) -> None
```

Input is a protein sequence, a list of chains, or a `.fa`/`.txt` path. One sequence uses the monomer model unless `multimer_for_monomer=True`; multiple sequences use the multimer model. `multimer_recycles=20` can increase multimer accuracy at substantial cost compared with the default 3. `relax=True` adds AMBER relaxation and therefore requires OpenMM. `plot=True` requires the optional interactive plotting stack; set it false for headless runs. `jackhmmer_savedir` chooses the parent directory for temporary MSA files; the implementation may use up to about 2 GB of disk space.

Validation constraints from the implementation are minimum 16 residues per sequence, maximum 3,400 per sequence, maximum 2,500 for a monomer model, and maximum 3,400 total. It warns above 3,000 total residues because accuracy/runtime are not fully validated. A successful `out` folder contains `selected_prediction.pdb` and `predicted_aligned_error.json`; plotting may also write `gget_alphafold_results.png`. The function returns `None`.

The runtime requires an AlphaFold installation, model parameters, Jackhmmer and its MSA databases, `pdbfixer`, and compatible OpenMM when relaxing. gget warns that this wrapper is no longer maintained and is unsupported on Windows. Setup downloads large third-party software/data and must be an explicit user decision; do not attempt it during ordinary skill discovery.
