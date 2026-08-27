# Cross-Cutting Troubleshooting

## When To Read

Read this when a pysam task fails before you know the correct sub-skill, or when an issue crosses installation, coordinates, indexes, file formats, and command wrappers.

## Triage by Symptom

| Symptom | Likely route | First action |
| --- | --- | --- |
| `ModuleNotFoundError`, `ImportError`, compiler errors, `Python.h`, linker errors, external `htslib` problems | `sub-skills/troubleshooting-build/SKILL.md` | Verify install with `scripts/check_pysam_environment.py`, then inspect build guidance. |
| BAM/CRAM/SAM fetch gives shifted positions, missing unmapped reads, missing index, pileup proxy errors | `sub-skills/alignment-io/SKILL.md` | Check coordinates, index presence, `until_eof`, `multiple_iterators`, and pileup lifetime. |
| VCF/BCF write fails because contig/INFO/FORMAT/sample is missing | `sub-skills/variant-io/SKILL.md` | Fix the `VariantHeader` before creating/writing records. |
| Tabix fetch returns no rows or shifted rows | `sub-skills/tabix-fasta/SKILL.md` | Check BGZF compression, sorted input, preset/column indexes, `zerobased`, and stale indexes. |
| `FastaFile` cannot open or fetch a reference | `sub-skills/tabix-fasta/SKILL.md` | Create/verify `.fai`, check `fasta.references`, and convert region coordinates carefully. |
| `pysam.samtools` or `pysam.bcftools` raises `SamtoolsError` | `sub-skills/command-wrappers/SKILL.md` | Use `usage()`, `get_messages()`, `catch_stdout=False`, or `save_stdout` as appropriate. |

## Coordinate Rules

- Use 0-based, half-open integer intervals in Python APIs such as `fetch("chr1", 10, 20)`.
- Use samtools-style region strings such as `"chr1:11-20"` when accepting command-style user input.
- Avoid mixing `region=` with explicit `contig/reference`, `start`, and `end` in the same call.
- Confirm whether an on-disk table is BED-style 0-based or GFF/VCF/SAM-style 1-based before indexing with tabix.

## Index Rules

- `AlignmentFile.fetch()` needs a BAM/CRAM/SAM index for random access; use `until_eof=True` only for sequential full-file iteration.
- `VariantFile.fetch()` needs a VCF/BCF index for interval access.
- `TabixFile.fetch()` needs a BGZF-compressed file plus `.tbi` or `.csi`.
- `FastaFile.fetch()` needs a FASTA `.fai` index or an index path that htslib can use.
- Rebuild indexes after changing data files; stale indexes can fail silently by returning wrong or missing rows.

## Public Environment Check

Run the bundled root helper from any environment where `pysam` should be installed:

```bash
python scripts/check_pysam_environment.py
```

A successful run imports core modules, checks wrapper availability, and exercises tiny source-free operations. If it fails at import, route to `troubleshooting-build`. If only a specific operation fails, route to the owning sub-skill.

## Avoid Runtime Source Dependencies

Do not tell future agents to open the original repository's docs, tests, or fixtures to use this skill. Use the bundled references and scripts in this generated skill tree. Original repo tests and docs are evidence for verification, not runtime dependencies.
