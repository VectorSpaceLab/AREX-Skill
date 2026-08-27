# Output layout and links

Return to the [output-and-integrity skill](../SKILL.md) for the side-effect
boundary and status contract. Selection/filtering belongs to
[download-and-filter](../../download-and-filter/SKILL.md); this page assumes
its candidate entries are already selected.

## Nested output (default)

With `--output-folder OUT` and without `--flat-output`, one assembly is laid
out as:

```text
OUT/
└── SECTION/                         # refseq or genbank
    └── DOMAIN/                      # e.g. bacteria or viral
        └── ASSEMBLY_ACCESSION/
            ├── MD5SUMS
            └── FILES_WITH_NCBI_SUFFIXES
```

`create_dir(entry, section, domain, output, flat_output=False)` creates
`OUT/SECTION/DOMAIN/ASSEMBLY_ACCESSION`, accepting an existing directory but
raising an `OSError` if a required path is a file. The default `OUT` from
`NgdConfig` is the current working directory, so always set an explicit
scratch or approved output for automation.

A nested directory is the safest default for multiple assemblies: identical
basenames from different accessions remain separated and their checksum
manifest is colocated with the files. `MD5SUMS` is downloaded and written to
this directory when missing or older than `md5_cache_days`; it is not a second
copy of every genome.

## Flat output

`--flat-output` makes `create_dir` return `OUT` itself:

```text
OUT/
├── FILES_FROM_ALL_SELECTED_ASSEMBLIES
└── (no persistent per-assembly MD5SUMS created by ngd)
```

The checksum text is fetched and parsed for each candidate, but the manifest is
not written into `OUT`. Because every file shares one directory, a basename
collision can overwrite or conflate files from different assemblies. Use flat
mode only when the selected set is known to have unique names and a downstream
consumer explicitly requires it. It can be combined with `--human-readable`,
but link-name collisions then remain possible as well.

## Human-readable hierarchy

`--human-readable` adds links under a separate tree while the canonical files
remain in the normal (nested or flat) location:

```text
OUT/human_readable/SECTION/DOMAIN/.../FILE  ->  canonical FILE
```

For non-viral domains, the exact directory components are:

```text
OUT/human_readable/SECTION/DOMAIN/GENUS/SPECIES/STRAIN/FILE
```

- `GENUS` is the first whitespace-delimited token of `organism_name`.
- `SPECIES` is the second token, or `sp.` if no second token exists.
- `STRAIN` comes from `infraspecific_name` after the last `=`, then
  `isolate`, then the remaining organism-name tokens, then the assembly
  accession. This is `get_strain` behavior.
- `STRAIN` has spaces, semicolons, `/`, and `\` changed to `_` by
  `get_strain_label`.

For `viral`, the path is instead:

```text
OUT/human_readable/SECTION/viral/ORGANISM_WITH_SPACES_AS_UNDERSCORES/STRAIN/FILE
```

Viral organism names are not split into genus/species, and the fallback strain
is the accession when the entry has no usable strain/isolate.

Links are made only after a file is downloaded and checked, or on a rerun when
`has_file_changed` says the canonical file is still valid. If the canonical
file is valid but the human-readable link is missing or points elsewhere,
ngd schedules a symlink-only `DownloadJob` with `full_url=None`; it does not
redownload the file. `create_symlink` removes an existing path (including a
broken link) before making the symbolic link. Protect unrelated files from
being placed at expected link paths: the implementation will unlink such an
existing path.

The `create_symlink` docstring describes a relative symbolic link, but inspect
what 0.3.4 actually writes: when `--output-folder` resolves to an absolute
path (the common case), `local_file` is absolute and `os.path.join` discards
the computed `..` prefix, so `os.readlink(link)` is absolute. With a relative
output argument the target can be relative. Do not promise that moving the
whole output tree preserves links; verify the actual target with
`os.readlink`, `os.path.islink`, and `os.path.realpath`, not just
`os.path.exists` (which follows links). A platform that cannot create
symlinks may fail at the link phase even when the canonical file is correct;
see [troubleshooting](troubleshooting.md).

## Formats and exact suffixes

`--formats` accepts one name, comma-separated names, or `all`. In 0.3.4 the
configured names map to these filename endings:

| Format | Required ending |
|---|---|
| `genbank` | `_genomic.gbff.gz` |
| `fasta` | `_genomic.fna.gz` |
| `rm` | `_rm.out.gz` |
| `features` | `_feature_table.txt.gz` |
| `gff` | `_genomic.gff.gz` |
| `protein-fasta` | `_protein.faa.gz` |
| `genpept` | `_protein.gpff.gz` |
| `wgs` | `_wgsmaster.gbff.gz` |
| `cds-fasta` | `_cds_from_genomic.fna.gz` |
| `rna-fna` | `_rna.fna.gz` |
| `rna-fasta` | `_rna_from_genomic.fna.gz` |
| `assembly-report` | `_assembly_report.txt` |
| `assembly-stats` | `_assembly_stats.txt` |
| `translated-cds` | `_translated_cds.faa.gz` |

The suffix is selected from the checksum manifest, not synthesized from the
accession. A missing suffix entry logs an error for that requested format and
produces no job for it; inspect the manifest rather than guessing a filename.
See [checksum matching gotchas](checksums-resume.md).

## Safe layout check without network

After a mocked fixture run, assert all of the following in a temporary `OUT`:

1. Nested mode has exactly `SECTION/DOMAIN/ACCESSION/MD5SUMS` and the selected
   file; flat mode has the selected file directly under `OUT` and no
   per-entry manifest produced by ngd.
2. The file's `md5sum` equals the checksum selected from the fixture manifest.
3. With human-readable mode, `os.path.islink(link)` is true and
   `os.path.realpath(link) == os.path.realpath(canonical_file)`.
4. Re-running with an unchanged canonical file creates only a missing link (if
   needed), not a file-download request.

Do not validate by invoking a live NCBI URL. For metadata checks, use the TSV
procedure in [metadata and concurrency](metadata-and-concurrency.md).
