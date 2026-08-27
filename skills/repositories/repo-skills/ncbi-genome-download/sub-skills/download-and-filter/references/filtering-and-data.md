# Filtering and input data

Candidate selection reads one NCBI assembly summary for each configured group,
then applies every configured filter to each parsed row. The summary URL is
constructed as:

```text
{uri}/{section}/{group}/assembly_summary.txt
```

The default base is `https://ftp.ncbi.nlm.nih.gov/genomes`. The parser accepts
commented/header variants and maps tab-separated fields such as
`assembly_accession`, `refseq_category`, `taxid`, `species_taxid`,
`organism_name`, `infraspecific_name`, `isolate`, `assembly_level`,
`relation_to_type_material`, and `ftp_path`. Rows whose `ftp_path` is `na` are
skipped with a warning because there is no assembly directory to download.

## Selection order and conjunction

For each row, the implementation checks, in order:

1. relation to type material;
2. genus/organism name;
3. extracted strain;
4. species TaxID;
5. organism TaxID;
6. assembly accession;
7. assembly level;
8. RefSeq category;
9. usable `ftp_path`.

The checks are an intersection: adding a filter can only retain rows that
satisfy it as well as all earlier/later filters. A format choice does not filter
rows; it controls which files are made into jobs after a row survives.

## Section, group, and format rules

### Section and group

Supported groups are `archaea`, `bacteria`, `fungi`, `invertebrate`,
`metagenomes`, `plant`, `protozoa`, `vertebrate_mammalian`,
`vertebrate_other`, and `viral`, plus the expansion token `all`.

- `refseq` supports every listed group except `metagenomes`.
- `genbank` supports all listed groups, including `metagenomes`.
- `all` is resolved after section selection, so `refseq all` excludes
  `metagenomes` while `genbank all` includes it.
- `groups="bacteria,viral"` is valid; `groups="bacteria, viral"` is not the
  same request because the second value begins with a space.

The section controls the summary URL and available group set. It is not a
post-download label that can be changed independently.

### File formats

Available format keys are:

```text
genbank fasta rm features gff protein-fasta genpept wgs cds-fasta
rna-fna rna-fasta assembly-report assembly-stats translated-cds
```

`all` expands to all of them. Use a comma-separated string with no spaces,
for example `fasta,assembly-report`. Format keys are translated into NCBI file
suffixes only after candidate selection; they do not change which summary rows
match.

### Assembly levels

The user-facing values map to the exact NCBI summary strings:

| Value | Summary `assembly_level` |
|---|---|
| `complete` | `Complete Genome` |
| `chromosome` | `Chromosome` |
| `scaffold` | `Scaffold` |
| `contig` | `Contig` |

`all` expands to all four. Matching is exact against the mapped summary value.

### RefSeq category

The accepted values are `reference`, `representative`, and `na`; `all`
expands to all three. The implementation maps the first two to the summary
strings `reference genome` and `representative genome`, while `na` remains
`na`. This filter is applied to the summary field even when the selected
section is GenBank; do not assume `--refseq-categories` changes GenBank into
RefSeq.

## Taxonomic and identity filters

### Genus / organism name

`--genera` / `genera` is a simple string operation on the summary's
`organism_name`; it is not a taxonomy database lookup.

- Default matching is a case-sensitive prefix test, with an additional
  convenience check against `genus.capitalize()`. Thus `Azorhizobium` and
  `azorhizobium` match an organism name beginning `Azorhizobium`, but the
  operation is still a prefix test, not normalization of arbitrary spelling.
- A value such as `Streptomyces coelicolor` is allowed and matches rows whose
  organism name starts with that text. Quote it in a shell.
- Multiple values are ORed within the genus filter and must be comma-separated
  without spaces: `--genera "Streptomyces coelicolor,Escherichia coli"`.
- `--fuzzy-genus` changes each value to a case-insensitive substring search
  anywhere in `organism_name`. For example, `--genera coelicolor
  --fuzzy-genus` can match `Streptomyces coelicolor A3(2)`.

Fuzzy mode is broader than the exact prefix mode and can produce unexpected
matches in strain or authority text embedded in the organism name. Use dry run
to inspect rows.

### Strain

`--strains` / `strains` compares exact strings to `get_strain(entry)`. The
extraction checks, in order:

1. `infraspecific_name`, taking the text after the final `=`;
2. `isolate`;
3. the portion of `organism_name` after its first two space-separated words
   (for non-viral entries);
4. `assembly_accession` as a fallback.

The filter values are not fuzzy and are not lowercased. A strain containing
spaces must be quoted, while comma-separated strain values must not contain
spaces after commas. A file is read one strain per line.

### TaxIDs

- `--species-taxids` / `species_taxids` compares exact strings to the summary's
  `species_taxid` field.
- `--taxids` / `taxids` compares exact strings to the summary's `taxid` field.

These filters do not expand descendants. Use the optional
[taxonomy-helper](../../taxonomy-helper/SKILL.md) when a user explicitly wants
taxonomic descendant expansion, then pass its generated one-ID-per-line file
to `--taxids`.

### Assembly accessions

`--assembly-accessions` / `assembly_accessions` compares exact strings such as
`GCF_000203835.1` by default. With `--fuzzy-accessions` or
`fuzzy_accessions=True`, each configured value is treated as a prefix, so
`GCF_000203835` matches `GCF_000203835.1`. Fuzzy accession matching is not a
substring search and does not ignore case.

## Type-material filter

Accepted relation values are:

```text
any all type reference synonym proxytype neotype
```

The named values map to these NCBI summary strings:

| Value | Required `relation_to_type_material` |
|---|---|
| `type` | `assembly from type material` |
| `reference` | `assembly from reference material` |
| `synonym` | `assembly from synonym type material` |
| `proxytype` | `assembly from proxytype material` |
| `neotype` | `assembly designated as neotype` |

The default is `any`, which includes rows with no relation value. `all` means
all five named relations are allowed and therefore excludes rows with an empty
relation. A named comma list is ORed within this filter, for example
`--type-materials type,reference`.

Avoid mixing `any` with a named relation when the intent is “missing relation OR
this named relation.” The setter normalizes any input containing `any` to
`['any']` (unless the same input also contains `all`, for which `all` takes
precedence), so `any,type` silently behaves like `any` and does not restrict to
type material. Use a named list such as `type,reference`, or make separate
requests if that distinction matters.

## List and file input rules

The config helper accepts either a Python list or a string. A string is split
on literal commas. For `genera`, `strains`, `species_taxids`, `taxids`, and
`assembly_accessions`, if the entire string is an existing regular file, the
file is read with `read().splitlines()` instead. This means:

- one item per line is the safe file format;
- line whitespace is not stripped by the helper;
- a non-existent path is treated as a literal comma-separated value;
- a list passed through the API is used as-is;
- shell quoting is needed for one item containing spaces;
- comma-separated values should have no spaces after commas.

Examples:

```text
# taxids.txt
9606
9685
```

```bash
ngd --section refseq --taxids taxids.txt --dry-run vertebrate_mammalian
ngd --section refseq --genera "Streptomyces coelicolor,Escherichia coli" \
    --dry-run bacteria
```

The optional taxonomy helper can generate a compatible one-ID-per-line file;
its database/update behavior is documented in
[taxonomy-helper](../../taxonomy-helper/SKILL.md), not here.

## Dry-run and no-match validation

A dry run calls summary retrieval and parsing, applies all filters, and then
prints each surviving row as:

```text
assembly_accession<TAB>organism_name<TAB>extracted_strain
```

It returns `0` if at least one row survives and does not call file-download job
creation. If no rows survive, the workflow logs the no-match message and
returns `1`. To diagnose an empty result, rerun with only the section/group,
then add one filter at a time; also check that the selected section has the
requested group and that rows have a non-`na` `ftp_path`.
