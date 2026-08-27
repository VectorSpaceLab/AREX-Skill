# gimme_taxa workflow

This optional contributed workflow converts taxon names or parent TaxIDs into
TaxIDs suitable for `ncbi-genome-download --taxids`, or emits a report about
those taxa. It is experimental and depends on ETE3's local NCBI taxonomy
database. It is not a replacement for the main download CLI.

## Safe, deliberate procedure

1. **Choose the runtime.** Use the same Python environment for the helper and
   any later wrapper commands. Before a lookup, confirm that `ete3`, `six`, and
   `numpy` are importable. The helper's `--help` path is safe to run without
   constructing `NCBITaxa`; it is the parser-only verification path.
2. **Choose the database path.** Pass `--database PATH` (`-d PATH`) to make the
   local database location explicit. The source default is `None`; ETE3 may
   create/download a local database, commonly under the user's home directory.
   A non-default database is not automatically reused, so repeat the same
   `--database` path on later runs. Make sure the parent directory is writable.
3. **Decide whether network access is allowed.** Instantiating `NCBITaxa` may
   create or download the taxonomy database. Add `--update` (`-u`) only when a
   refresh is intentionally requested; it can take several minutes. A lookup
   can therefore have network and local filesystem effects even though the
   output is a small text file.
4. **Specify inputs.** Give one positional `taxid` argument containing a
   comma-separated list of numeric TaxIDs and/or taxon names, for example
   `561,2172` or `561,Methanobrevibacter`. The source strips single and double
   quote characters and then splits on commas. Names are resolved through the
   local ETE3 database; numeric strings are accepted as integer TaxIDs if name
   translation does not find them.
5. **Select one output intent.** Use `--just-taxids` (`-j`) for a headerless
   one-ID-per-line descendant file. Use `--taxon-info` (`-i`) to describe the
   supplied taxa instead. With neither flag, get the default descendant report.
   If both `-i` and `-j` are given, the source takes the `taxon-info` branch.
6. **Choose output handling.** Use `--outfile PATH` (`-o PATH`) for a durable
   file. If omitted, the source writes data to stdout. The adapted helper
   retains this behavior; do not combine data stdout with unrelated command
   output. Prefer an explicit file for a downstream TaxID handoff.
7. **Run and inspect.** Start with `--help`; then run the chosen lookup only
   after accepting its database/network side effects. With `-v` (`--verbose`),
   increase verbosity by repeating the flag (for example `-vv`). At verbosity
   above one, database location and update status are written to stderr.
   Check the output file is readable, has the expected header/columns, and has
   one valid TaxID per line in `-j` mode before using it.
8. **Handoff.** Pass the inspected `-j` file to the main CLI's `--taxids`
   option, for example:

   ```bash
   export SKILL_ROOT="${SKILL_ROOT:?Set SKILL_ROOT to the generated skill directory}"
   WORKDIR="$(mktemp -d)"
   python "$SKILL_ROOT/sub-skills/taxonomy-helper/scripts/gimme_taxa.py" \
     --database "$WORKDIR/taxonomy.sqlite" \
     --just-taxids \
     --outfile "$WORKDIR/escherichia-descendants.txt" \
     Escherichia
   ncbi-genome-download --taxids "$WORKDIR/escherichia-descendants.txt" bacteria
   ```

   The second command is the main download workflow; see
   [`../../download-and-filter/SKILL.md`](../../download-and-filter/SKILL.md) for its
   options and filtering behavior. See
   [`../../output-and-integrity/SKILL.md`](../../output-and-integrity/SKILL.md) for
   output and checksum concerns.

## Output formats

### `--just-taxids` / `-j`

No header is written. Each returned descendant TaxID is written as a decimal
string followed by a newline:

```text
123
456
```

This is the handoff format for `--taxids`. The exact IDs, count, order, and
whether a query yields any descendants depend on the local taxonomy database;
no live result is promised by this skill.

### Default descendant report

Without `-j` or `-i`, the first line is exactly:

```text
parent_taxid\tdescendent_taxid\tdescendent_name
```

Each later line is a tab-separated parent TaxID, descendant TaxID, and translated
descendant name:

```text
561\t562\tEscherichia coli
```

The header uses the source's `descendent` spelling.

### `--taxon-info` / `-i`

The first line is exactly:

```text
name\ttaxid\trank\tlineage
```

Each later line contains the supplied taxon's translated name, numeric TaxID,
rank, and a semicolon-separated lineage whose entries are formatted as
`<lineage_taxid>:<lineage_name>`:

```text
Escherichia coli\t562\tspecies\t1:root;2:Bacteria
```

The example values are format illustrations only, not a verified live result.

## Handoff cautions

- Only `-j` output is shaped as direct `--taxids` input. Do not pass the
  default report or `-i` report as a TaxID file.
- Keep the database path and output path separate. A database path is not an
  output TaxID file.
- If stdout is used, redirect only the data stream. Verbose diagnostics from
  the helper are sent to stderr, but ETE3 or environment-level messages should
  still be reviewed before treating a redirected file as clean input.
- Validate output and record provenance before a potentially large download;
  consult the sibling output/integrity skill for the repository's general
  checks.
