---
name: taxonomy-helper
description: "Use the optional gimme_taxa workflow to resolve taxon names or
  parent TaxIDs into descendant TaxIDs or taxon metadata for
  ncbi-genome-download."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Taxonomy helper

`gimme_taxa.py` is an optional, experimental contributed workflow. It uses
ETE3's `NCBITaxa` interface and a local NCBI taxonomy database to resolve each
comma-separated positional input (a taxon name, a numeric TaxID, or both) and
then either emit descendants or describe the supplied taxa. It is a separate
preparation step; it is not part of the main download CLI.

Use the bundled helper at [`scripts/gimme_taxa.py`](scripts/gimme_taxa.py), not
an original source checkout. The helper's parser preserves the public spellings
`-v/--verbose`, `-d/--database`, `-u/--update`, `-j/--just-taxids`,
`-i/--taxon-info`, and `-o/--outfile`.

## Choose an output mode

- **Download input (`-j` / `--just-taxids`)**: write one descendant TaxID per
  line, with no header. This is the only output mode intended for direct use as
  an `ncbi-genome-download --taxids` input file. See
  [`../download-and-filter/SKILL.md`](../download-and-filter/SKILL.md) for the
  consuming download command and its filters.
- **Default descendant report**: write a header followed by tab-separated rows
  with `parent_taxid`, `descendent_taxid`, and `descendent_name`. This is for
  inspection, not direct `--taxids` consumption.
- **Taxon metadata (`-i` / `--taxon-info`)**: write a header followed by
  tab-separated `name`, `taxid`, `rank`, and `lineage` columns for the supplied
  taxa. If `-i` and `-j` are both supplied, the source's `taxon-info` branch
  takes precedence.

The source spelling `descendent` in the default header is intentional. Do not
silently deduplicate or reorder rows: the helper emits the returned ETE3
sequence once for each supplied parent. The actual names and descendants are
properties of the local taxonomy database and were not live-queried during
verification.

## Safety boundary

A lookup can have network and filesystem side effects. Constructing
`NCBITaxa` may create or download a local taxonomy SQLite database when no
usable database exists. `--update` (`-u`) explicitly asks ETE3 to refresh that
database and can take several minutes and require network access. Prefer an
explicit, writable `--database` path in a controlled workspace, record that
path, and use the same path on later runs. Do not enable `--update` merely to
produce help or to test parsing.

The helper requires a Python environment in which ETE3 and its expected
runtime dependencies `six` and `numpy` are installed. Installation and
database acquisition are deliberately outside the download skill's normal
verification: no live taxonomy database query was run. First run `--help`,
then make a deliberate decision about dependency installation, database
location, and network access before querying.

For checksums, file existence, and downstream output validation, follow
[`../output-and-integrity/SKILL.md`](../output-and-integrity/SKILL.md). Treat the
TaxID file as generated input: inspect its headerless, one-ID-per-line format
before passing it onward.

## Minimal handoff pattern

```bash
# Set this to the generated skill directory; the commands below are portable.
export SKILL_ROOT="${SKILL_ROOT:?Set SKILL_ROOT to the generated skill directory}"
WORKDIR="$(mktemp -d)"

# Parser-only check; this does not instantiate ETE3 or access the network.
python "$SKILL_ROOT/sub-skills/taxonomy-helper/scripts/gimme_taxa.py" --help

# Deliberate lookup: choose a writable database and output file first.
python "$SKILL_ROOT/sub-skills/taxonomy-helper/scripts/gimme_taxa.py" \
  --database "$WORKDIR/taxonomy.sqlite" \
  --just-taxids \
  --outfile "$WORKDIR/descendant-taxids.txt" \
  Escherichia

# Consume only after inspecting the generated file.
ncbi-genome-download --taxids "$WORKDIR/descendant-taxids.txt" bacteria
```

The lookup command may download/create the database. Add `--update` only when
refreshing it is intended, and use `-v` or `-vv` when diagnostic output is
needed. Keep helper diagnostics on stderr and the data file on `--outfile` (or
stdout when `--outfile` is omitted) so shell redirection cannot accidentally
mix status text into the TaxID file.
