# Dependencies and troubleshooting

`gimme_taxa.py` is an optional, experimental ETE3 workflow. Its normal
installation and database behavior are not required for the main
`ncbi-genome-download` command.

## Dependency boundary

The helper's direct API is `ete3.NCBITaxa`. Use an isolated environment and
install the expected runtime set before a real lookup, for example:

```bash
python -m pip install ete3 six numpy
```

The bundled helper lazily imports these modules after argument parsing. Thus
`--help` and parser inspection do not instantiate ETE3 or touch a taxonomy
database, while a real query gives an actionable dependency error instead of a
long traceback when the environment is incomplete. The verified setup fact is
that the script's help path passes when `ete3`, `six`, and `numpy` are
installed. This skill did not perform a live database query.

## Symptoms and actions

### `ete3` is missing or cannot import

A lookup needs `ete3.NCBITaxa`; install ETE3 in the exact Python environment
used to invoke the bundled helper, then retry the import probe. Some ETE3
installation failures are transitive dependency failures, so also install or
repair `six` and `numpy`. Do not infer that a successful `ncbi-genome-download`
installation supplied this optional dependency set: the repository's normal
`setup.py` requirements do not include ETE3.

Run this parser-only check before a lookup:

```bash
export SKILL_ROOT="${SKILL_ROOT:?Set SKILL_ROOT to the generated skill directory}"
python "$SKILL_ROOT/sub-skills/taxonomy-helper/scripts/gimme_taxa.py" --help
```

If help fails, inspect the Python executable and package environment before
allowing any database access.

### `six` or `numpy` is missing

These are part of the expected ETE3 runtime setup for this helper. Install them
in the same environment as ETE3 (`python -m pip install six numpy`) or use the
environment's compatible package manager. A dependency error is not evidence
that the taxonomy database is corrupt. Re-run `--help`, then use an explicit
`--database` path for any lookup.

### Database path mismatch or an unexpected new database

`-d` / `--database` controls the ETE3 database file path. If it is omitted, the
source passes `None` and ETE3 chooses its default, commonly in the user's home
directory. If a database was first created at a custom path, omitting `-d` on a
later run can cause ETE3 to use or create a different default database. Repeat
the exact path on every lookup and update, and use `-vv` if you need the helper
to report `ncbi.dbfile` to stderr.

Do not copy an SQLite database while it is being updated. Treat the path as a
managed local artifact and ensure its parent and database file are accessible
by the invoking user.

### First-use download, `--update`, or network failure

`NCBITaxa(dbfile=...)` may create/download a local taxonomy database. `-u` /
`--update` calls ETE3's `update_taxonomy_database()` before the query. Both
operations can require network access and may take several minutes. Check
connectivity, proxy/firewall policy, disk space, and write permissions; retry
with the same explicit database path rather than silently switching paths.

If a reproducible offline run is required, arrange and validate the database
before invoking the helper. This skill does not claim that a particular ETE3
database URL, schema, cache location, or offline flag will work, because those
were not established from the source evidence and no live query was run.

### Invalid or unresolved name/TaxID

The positional argument is one comma-separated string. A taxon name is looked
up through `get_name_translator`; an input that is neither found as a name nor
convertible to an integer raises `ValueError` with `cannot convert to taxid`.
Check spelling, commas, and the database version. Numeric text can be accepted
as a TaxID even if it is not a useful node; later ETE3 lookup behavior should be
reported rather than guessed. Avoid adding unverified claims about aliases,
case folding, whitespace normalization, or exact descendant membership.

### Output-file permission, parent, or overwrite errors

`-o` / `--outfile` opens the target for writing and does not create missing
parent directories. Create and permission-check the destination directory
first. Existing output is replaced by the adapted helper's normal write mode;
choose a new path or back up an earlier result when provenance matters. Keep
`--database` and `--outfile` as different paths.

### Unexpected stdout or a contaminated TaxID file

Without `-o`, data is written to stdout. In `-j` mode it should contain only
one TaxID per line; in default and `-i` modes it begins with a header. Use
`-o` or redirect stdout to a dedicated file, and keep diagnostics separate with
`2>diagnostics.log`. Inspect the first lines and reject a file with a header,
columns, traceback, shell prompt, or other non-numeric content before passing
it to `--taxids`.

`-v` is a count option: `-v` sets level 1 and `-vv` sets level 2. At level 2,
the helper writes database/update messages to stderr. `--taxon-info` takes
precedence over `--just-taxids` when both are supplied, matching the source
branch order.

## Verification boundary

Verification covers static source inspection, parser/help behavior, frontmatter,
links, and output-format logic using an offline fake `ete3.NCBITaxa` only when
needed to exercise formatting. It intentionally does **not** instantiate the
real ETE3 client against NCBI, create/download a live taxonomy database, update
one, or assert current names, ranks, lineage values, descendant sets, or exact
network behavior. Those are environment- and database-version-dependent side
effects and must be treated as an explicit operator decision.
