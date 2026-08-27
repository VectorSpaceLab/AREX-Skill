# Gene annotation API and schemas

This reference consolidates the public signatures in the generated integration
signature report with the implementation and English command documentation.
The calls are network operations unless a caller replaces the upstream clients
in a test harness.

## `gget.ref`

Python signature:

```python
gget.ref(
    species: str | None,
    which: str | list[str] = "all",
    release: int | None = None,
    ftp: bool = False,
    save: bool = False,
    list_species: bool = False,
    list_iv_species: bool = False,
    verbose: bool = True,
) -> Any
```

Species is normally `genus_species`. `human` maps to `homo_sapiens`, `mouse`
to `mus_musculus`, and `human_grch37` to the GRCh37 assembly. With
`species=None`, set one of `list_species=True` or `list_iv_species=True` to
return a sorted list of species for which both GTF and DNA/FASTA listings are
available. `release=None` uses the latest listing; a numeric release selects a
release listing and warns if it is above the currently observed latest release.

Accepted `which` values are `all`, `gtf`, `cdna`, `dna`, `cds`, `ncrna`, and
`pep`. Pass a string or a list, but do not combine `all` with another value.
The meanings are annotation GTF, transcript cDNA, genome DNA, coding CDS,
non-coding RNA transcript FASTA, and translated peptide FASTA. A non-vertebrate
species is resolved through an Ensembl Genomes kingdom (plants, protists,
metazoa, or fungi); an explicit database name is not an argument to `ref`.

With `ftp=False`, the result is a nested dictionary keyed by the normalized
species. Each selected resource contains `ftp`, `ensembl_release`,
`release_date`, `release_time`, and `bytes`. For `which="all"`, resource keys
are `transcriptome_cdna`, `genome_dna`, `annotation_gtf`, `coding_seq_cds`,
`non-coding_seq_ncRNA`, and `protein_translation_pep`. A resource unavailable
for a species can have an empty `ftp` and empty date/size fields. With
`ftp=True`, the result is a list of URL strings in the requested `which` order;
`all` expands in the order GTF, cDNA, DNA, CDS, ncRNA, peptide.

Python `save=True` writes `gget_ref_results.json` when `ftp=False` and
`gget_ref_results.txt` when `ftp=True` in the current working directory. The
CLI adds `--download` (curl), `--out_dir`, and `--out`; Python does not expose
those path arguments.

CLI form:

```text
gget ref [species] [-w all|gtf,cdna,dna,cds,ncrna,pep] [-r RELEASE]
         [-ftp] [-l|--list_species] [-liv|--list_iv_species]
         [-d|--download] [-od|--out_dir DIR] [-o|--out FILE] [-q|--quiet]
```

The CLI positional species is optional only for the list flags. The source
parser also accepts deprecated `-s/--species`; prefer the positional form.

## `gget.search`

Python signature:

```python
gget.search(
    searchwords: str | list[str],
    species: str,
    release: int | None = None,
    id_type: str = "gene",
    seqtype: str | None = None,
    andor: str = "or",
    limit: int | None = None,
    wrap_text: bool = False,
    json: bool = False,
    save: bool = False,
    verbose: bool = True,
) -> pandas.DataFrame | list[dict[str, Any]] | None
```

`searchwords` is case-insensitive free text. `id_type` is `gene` or
`transcript`; `andor="or"` retains rows matching at least one term, while
`andor="and"` retains IDs matching all terms. `limit` keeps the first rows
after stable-ID sorting/grouping. `seqtype` is deprecated: if supplied, the
implementation logs an error and returns rather than using it; use `id_type`.

A normal DataFrame has these columns:

```text
ensembl_id, gene_name, ensembl_description, ext_ref_description,
biotype, synonym, url
```

`synonym` is kept as a list (with `[None]` for a missing synonym). The query
matches display labels, descriptions, external synonyms, and gene/transcript
attributes; it is not a full-text search of arbitrary Ensembl tables. `url` is
an Ensembl gene-summary URL. With `json=True`, return is a list of record
mappings with the same keys, JSON nulls, and list-valued synonyms. With
`wrap_text=True`, long description/URL cells are displayed wrapped; use the
returned DataFrame for data processing. With `save=True`, write
`gget_search_results.csv` or `gget_search_results.json` in the current working
directory.

Species handling:

- `human` and `mouse` are shortcuts.
- A plain species name resolves to a matching current or requested Ensembl
  core database. For `mouse` and `human` ambiguity, the implementation chooses
  its standard core assembly and logs a warning where applicable.
- A string containing `core` is treated as an explicit core database; any
  supplied `release` is then overridden.
- For invertebrates, pass the explicit core database when release selection is
  needed. The documented `release` argument does not apply to invertebrate
  species, and a database name containing a release wins.

CLI form:

```text
gget search WORD... -s|--species SPECIES [-r RELEASE]
            [-t|--id_type gene|transcript] [-ao|--andor or|and]
            [-l|--limit N] [-csv|--csv] [-o|--out FILE] [-q|--quiet]
```

CLI search is JSON by default; `--csv` switches the output to CSV. The
`--json` flag exists as a deprecated compatibility option because JSON is now
the default. The positional `WORD...` form and `--species` are preferred.

## `gget.info`

Python signature:

```python
gget.info(
    ens_ids: str | list[str],
    wrap_text: bool = False,
    ncbi: bool = True,
    uniprot: bool = True,
    pdb: bool = False,
    json: bool = False,
    verbose: bool = True,
    save: bool = False,
    expand: bool = False,
    ensembl_only: bool = False,
) -> pandas.DataFrame | dict[str, Any] | None
```

Input may contain Ensembl, WormBase, or FlyBase IDs and may mix them. For IDs
starting with `ENS`, the version suffix is removed for the lookup, duplicate
clean IDs are removed while preserving first-seen order, and the returned
`ensembl_id` is populated with the latest version reported by Ensembl. A
versioned ID therefore does not pin a historical annotation. Non-`ENS` IDs are
passed through for WormBase/FlyBase handling.

The default DataFrame row contains Ensembl fields plus optional provider data.
Common columns include `ensembl_id`, `uniprot_id`, `pdb_id`, `ncbi_gene_id`,
`species`, `assembly_name`, `primary_gene_name`, `ensembl_gene_name`,
`synonyms`, `parent_gene`, `protein_names`, `ensembl_description`,
`uniprot_description`, `ncbi_description`, `subcellular_localisation`,
`object_type`, `biotype`, `canonical_transcript`, `seq_region_name`, `strand`,
`start`, and `end`. Gene and transcript expansion also exposes list-valued
`all_transcripts`, `transcript_biotypes`, `transcript_names`,
`transcript_strands`, `transcript_starts`, `transcript_ends`, `all_exons`,
`exon_starts`, `exon_ends`, `all_translations`, `translation_starts`, and
`translation_ends` when the object supports them. Exact columns vary with
object type and provider flags.

`json=True` returns a dictionary keyed by the reported ID. Transcript, exon,
and translation collections are represented as lists of dictionaries rather
than the parallel DataFrame columns. `ncbi=False` and `uniprot=False` reduce
provider calls. `pdb=True` adds PDB IDs and can increase runtime. If every ID
is missing, return is `None`; missing IDs in a mixed request are warned about
and omitted. UniProt is queried for reviewed records first and falls back to
unreviewed records when no reviewed match exists. No UniProt match is not an
Ensembl lookup failure.

`expand` is deprecated because expansion is now always performed. `ensembl_only`
is deprecated; use `ncbi=False, uniprot=False` and leave `pdb=False`. The
implementation still recognizes the deprecated arguments for compatibility.
`wrap_text=True` displays wrapped long text. Python `save=True` writes
`gget_info_results.csv` or `gget_info_results.json` in the current working
directory. Split lists larger than 1,000 IDs into chunks.

CLI form:

```text
gget info ID... [-n|--ncbi] [-u|--uniprot] [-pdb|--pdb]
           [-csv|--csv] [-o|--out FILE] [-q|--quiet]
```

The CLI flags `--ncbi` and `--uniprot` are negative switches: supplying them
turns those provider queries off. CLI JSON is the default; `--csv` selects
CSV. `--expand`, `--ensembl_only`, `--ens_ids`, and `--json` are deprecated
compatibility flags.

## `gget.seq`

Python signature:

```python
gget.seq(
    ens_ids: str | list[str],
    translate: bool = False,
    isoforms: bool = False,
    save: bool = False,
    transcribe: bool | None = None,
    seqtype: Any = None,
    verbose: bool = True,
) -> list[str] | None
```

The return is an alternating list of FASTA header and sequence strings, not a
DataFrame or JSON object. `translate=False` requests nucleotide sequence from
Ensembl REST. `translate=True` resolves a gene to its canonical transcript (or
uses a transcript ID directly), then requests amino-acid records from UniProt.
UniProt-reviewed records are preferred, with an unreviewed fallback. An
unmatched protein produces no FASTA record and may leave an empty list.

`isoforms=True` applies to gene IDs: nucleotide mode fetches all transcript
sequences, while protein mode queries all transcript IDs returned by `info` and
keeps only UniProt matches. For a transcript ID, the flag is ignored and one
transcript is requested; the implementation warns about this. A plain gene ID
with `isoforms=False` is sent to Ensembl as a gene sequence, whose header
contains its genomic description. A protein header includes the query
transcript, UniProt accession, gene name, organism, and sequence length.

Ensembl IDs beginning with `ENS` have a dot-version removed before the request;
WormBase and FlyBase IDs are not normalized with this rule. `transcribe` and
`seqtype` are deprecated; use `translate`. Python `save=True` additionally
writes `gget_seq_results.fa` in the current working directory and still
returns the FASTA-line list.

CLI form:

```text
gget seq ID... [-t|--translate] [-iso|--isoforms]
         [-o|--out FASTA] [-q|--quiet]
```

CLI `--translate` means amino acid and otherwise means nucleotide. CLI `-o`
can choose the FASTA path; there is no JSON/DataFrame mode. Deprecated
`--seqtype` and `--ens_ids` aliases should not be used.
