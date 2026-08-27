# MSA and Template Troubleshooting

## Wrong `.aligned.pqt` Schema

Symptoms:

- `Invalid schema` from `parse_aligned_pqt_to_msa_context`.
- Validator reports missing columns, nulls, or invalid source labels.

Likely causes:

- The parquet table is not the Chai format.
- Required columns are missing: `sequence`, `source_database`, `pairing_key`, `comment`.
- `source_database` contains a value outside Chai's recognized source labels.
- `pairing_key` or `comment` contains null values instead of empty strings.

Fix:

```bash
python scripts/validate_aligned_pqt.py msas/*.aligned.pqt
```

Then rewrite the table so all required columns are present as strings. For hand-built tables, prefer `query`, `uniref90`, `uniprot`, `bfd_uniclust`, and `mgnify` source values.

## First Row Is Not the Query

Symptoms:

- Assertion failure: `First row must be query`.
- Validator reports `first row source_database is ...; expected query`.

Likely causes:

- A3M rows were sorted before writing parquet.
- The query row was dropped while merging multiple A3M sources.
- A server/staging artifact was manually edited.

Fix:

- Move the query sequence to row 0.
- Set row 0 `source_database` to `query`.
- Ensure there is exactly one `query` row.
- Keep row 0 `pairing_key` empty.

## Wrong Parquet Filename

Symptoms:

- Chai logs `No MSA found for sequence: ...` even though files exist.
- Validator reports an unexpected basename.
- Folding silently behaves like single-sequence mode for a protein that should have local MSAs.

Likely causes:

- File was named by protein/entity name instead of the sequence hash.
- Hash used lowercase or unnormalized sequence text.
- Query sequence in the parquet does not match the FASTA protein sequence.

Fix:

- Rename the file to `sha256(query_sequence.upper()).aligned.pqt`.
- Use the bundled validator to print the expected basename.
- Confirm the FASTA protein sequence and row-0 parquet sequence are the same biological sequence.

## No Matching MSA for a FASTA Sequence

Symptoms:

- Warning: `No MSA found for sequence: ...`.
- No improvement from local MSAs.
- MSA coverage plot is absent or shallower than expected.

Likely causes:

- The local MSA directory does not contain the expected hash filename.
- The FASTA sequence changed after MSA generation.
- Non-protein entities were expected to have MSAs; Chai only loads these local MSAs for proteins.
- Duplicate protein sequences share one MSA file; this is okay, but unique sequences each need a file.

Fix:

- Hash the exact FASTA protein sequence and compare to filenames.
- Run `validate_aligned_pqt.py` on the MSA directory.
- Regenerate A3M/parquet files after any FASTA sequence edit.

## A3M Conversion Produces Unexpected Source Labels

Symptoms:

- CLI logs that it defaulted a source to `uniref90`.
- MSA rows from different databases are not distinguishable.

Likely causes:

- A3M filenames do not encode a Chai source, such as `hits_uniref90.a3m` or `hits_uniprot.a3m`.
- Multiple databases were merged into one A3M file before conversion.

Fix:

- Rename A3M files so the database source is inferable before running `chai-lab a3m-to-pqt`.
- For custom sources, choose the closest Chai source intentionally and document it in the `comment` column.
- For complex pairing policies, write the parquet table directly instead of relying on generic source inference.

## Lowercase Insertions Change Tokenization Expectations

Symptoms:

- Validator reports aligned-length mismatches.
- A3M rows appear longer than the query sequence in raw text.
- Deletion counts differ from a simple gap-only alignment mental model.

Likely causes:

- Lowercase A3M insertion letters were counted as aligned residues by a custom script.
- Period (`.`) characters or lowercase insertions were not treated as skipped/insertion characters.

Fix:

- Count only uppercase letters and `-` as aligned positions.
- Treat lowercase letters as insertions that increment deletion counts before the next aligned token.
- Run the validator to catch rows whose aligned lengths differ from row 0.

## MSA Server or Template Server Side Effects

Symptoms:

- Network calls happen during feature preparation.
- A CI or offline workflow hangs or fails.
- `output_dir/msas` creation fails because it already exists.

Likely causes:

- `--use-msa-server` or `use_msa_server=True` was enabled unintentionally.
- Server templates were requested without allowing the server MSA route.
- Reusing a non-empty output directory from a previous run.

Fix:

- Use local `--msa-directory` and `--template-hits-path` for offline/reproducible runs.
- Keep `use_msa_server=False` when passing `msa_directory`.
- Use a fresh output directory for each server-backed fold.
- Use `--msa-server-url` only when a private/approved ColabFold service is intended.

## Pairing-Key Misunderstandings

Symptoms:

- Multimer predictions do not reflect expected paired evolutionary signal.
- All rows are unpaired despite paired upstream MSAs.
- Rows pair across chains in biologically implausible ways.

Likely causes:

- Every hit has an empty `pairing_key`.
- Arbitrary pairing keys were reused across unrelated species or hits.
- Row-number pairing was used for independently generated A3M files.

Fix:

- Use shared species/taxonomy identifiers when pairing rows from independently generated MSAs.
- Use row-index keys only when an upstream paired search already guarantees corresponding rows.
- Preserve ColabFold pairing by using `stage_colabfold_outputs.py` rather than hand-merging pair A3Ms.

## Template m8 Query ID Mismatch

Symptoms:

- Chai logs no corresponding entries for a query ID.
- Templates are all empty even though the m8 file has rows.
- Local template hits work with server-style hashes only in one mode but not another.

Likely causes:

- Local `template_hits_path` uses sequence hashes while Chai is looking for FASTA entity names.
- The FASTA entity name changed after m8 creation.
- A staged ColabFold m8 file did not remap numeric IDs to Chai FASTA names.

Fix:

- For local template m8 files, set `query_id` to the exact protein FASTA entity name Chai sees.
- If `fasta_names_as_cif_chains=True`, make sure the entity naming route is also consistent with sibling input-format guidance.
- Use the staging helper for ColabFold outputs; it rewrites ColabFold numeric query IDs to Chai FASTA entity names.

## Custom CIF Folder Naming

Symptoms:

- Template loading downloads from RCSB even though local CIF files exist.
- Custom/non-RCSB template structures are not found.
- Template hits are skipped after CIF lookup.

Likely causes:

- `CHAI_TEMPLATE_CIF_FOLDER` is unset or points to the wrong directory.
- CIF filenames do not match `identifier.cif.gz`.
- `subject_id` in m8 does not use the same identifier before the underscore.

Fix:

```bash
export CHAI_TEMPLATE_CIF_FOLDER=/path/to/template_cifs
```

Then ensure local files follow:

```text
$CHAI_TEMPLATE_CIF_FOLDER/<identifier>.cif.gz
```

For `subject_id` `7WCU_A`, Chai expects the identifier `7WCU` and chain `A`.

## Missing `kalign`

Symptoms:

- Template alignment fails or hits are skipped.
- Error mentions `kalign is required for templates`.

Likely causes:

- `kalign>=3.3` is not installed on `PATH`.

Fix:

- Install `kalign` in the runtime environment using the operating-system or environment package manager appropriate for the deployment.
- Re-run a small local template parse before an expensive fold.

## Too Many Templates or Overbroad m8 Files

Symptoms:

- Error: `Too many templates in input`.
- Many template hits are loaded, skipped, or slow to process.

Likely causes:

- The m8 file contains too many hits per query.
- Hits include modified residues, sequence mismatches, or chains that fail tokenization.

Fix:

- Pre-filter m8 rows to a small, high-confidence set per query.
- Sort and inspect by `query_id` and `evalue`.
- Remove hits that do not match available CIF identifiers/chains.

## Staging ColabFold Outputs Fails

Symptoms:

- Error says `Expected exactly one csv file`.
- Missing `pair.a3m`, `uniref.a3m`, `bfd.mgnify30.metaeuk30.smag30.a3m`, or `pdb70.m8`.
- Staged FASTA sequences do not match staged MSA query sequences.

Likely causes:

- The ColabFold output tree does not match the expected directory layout.
- `sequences.csv` has extra columns or a different delimiter.
- ColabFold output was partially copied or renamed.

Fix:

- Restore the expected ColabFold-like tree before staging.
- Run `stage_colabfold_outputs.py --help` and then stage into a fresh output directory.
- Validate the generated `.aligned.pqt` files before folding.
