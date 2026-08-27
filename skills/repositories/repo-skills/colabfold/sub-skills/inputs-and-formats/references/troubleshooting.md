# Input troubleshooting

Use this reference for failures owned by input preparation and format interpretation. Route search, prediction, relaxation, and output-ranking failures to sibling sub-skills.

## Optional dependency failures

### `ModuleNotFoundError: No module named 'colabfold'`

Cause: the package is not installed in the active Python environment.

Checks:

```bash
python - <<'PY'
import colabfold
import colabfold.input
print(colabfold.__file__)
PY
```

Fix: activate an environment where ColabFold is installed. Input parsing does not require GPU, databases, or AlphaFold parameters.

### `pandas` missing for CSV/TSV

Cause: `get_queries` imports `pandas` only for `.csv` and `.tsv` inputs.

Fix options:

- Install/activate an environment with `pandas`.
- Convert the job list to FASTA when only `id` and `sequence` are needed.
- Use the bundled validator to catch missing columns before calling expensive workflows.

### `RuntimeError: alphafold is not installed`

Cause: importing `colabfold.batch` loads optional AlphaFold dependencies. This is not required for FASTA/A3M/CSV parsing from `colabfold.input`.

Fix:

- For input-only work, import `parse_fasta`, `classify_molecules`, `get_queries`, `msa_to_str`, and `pdb_to_string` from `colabfold.input`.
- For prediction or template conversion workflows, route to `../batch-prediction/SKILL.md` and use an environment with prediction extras.

## Backend failures

### GPU/JAX/CUDA warnings during input work

Cause: a tool imported prediction modules instead of lightweight input helpers.

Fix:

- Avoid importing `colabfold.batch` just to parse inputs.
- Use `python sub-skills/inputs-and-formats/scripts/validate_colabfold_input.py ...`, which performs no GPU or JAX work.
- If GPU failures happen during `colabfold_batch`, route to batch prediction.

### OpenMM or relaxation import errors

Cause: relaxation dependencies are unrelated to input validation.

Fix: validate inputs without importing relaxation code. Route Amber/OpenMM work to `../relaxation-and-outputs/SKILL.md`.

## Data and config failures

### Empty FASTA or A3M

Symptoms:

- Standalone empty `.a3m` raises a `ValueError`.
- Empty files in a directory may be logged and skipped.

Fix:

```bash
python sub-skills/inputs-and-formats/scripts/validate_colabfold_input.py inputs/
```

Then remove empty files or add at least one FASTA/A3M record with a header and sequence.

### FASTA sequence appears before first header

Cause: ColabFold FASTA parsing expects records beginning with `>`.

Fix:

```text
>job_name
SEQUENCE
```

Do not rely on implicit names or raw sequence-only files.

### Complex is not detected

Causes:

- Chains are on separate FASTA records in a single file, but directory FASTA parsing keeps only the first record per file.
- A precomputed complex A3M lost its `#lengths\tcardinalities` header.
- CSV sequence contains unexpected separators or quoting issues.

Fix:

- Put complex chains in one FASTA sequence separated by `:`.
- Preserve serialized A3M headers from `msa_to_str`.
- For CSV/TSV, quote fields if needed and verify the parsed query count.

### AF3 ligand SMILES fails or is split into extra chains

Cause: aromatic SMILES colons conflict with ColabFold's colon chain separator.

Fix: replace SMILES aromatic colons with semicolons in FASTA input. ColabFold converts semicolons back to colons for `smiles|...` entries.

```text
>ligand_case
PROTEINSEQ:smiles|c1cc;cc1
```

If a copy count is present, make it an integer:

```text
PROTEINSEQ:ccd|ATP|2
```

### Duplicate or unsafe job names

Cause: prediction workflows sanitize job names by replacing unsafe characters with `_`. Different raw names can collide.

Fix:

- Use unique IDs containing only letters, digits, `_`, `.`, and `-`.
- For directories, remember job names come from file stems, not FASTA headers.
- Check sanitized uniqueness before large batches.

## CLI/API failures

### `AssertionError` for CSV/TSV columns

Cause: CSV/TSV lacks required `id` or `sequence` columns.

Fix:

```csv
id,sequence
job1,ACDEFGHIK
```

Optional columns are `a3mpath` and `templatepath`.

### `ValueError: Unknown file format`

Cause: standalone input file suffix is not one of `.csv`, `.tsv`, `.a3m`, `.fasta`, `.faa`, `.fa`, `.pdb`, or `.cif`.

Fix: rename or convert the file to a supported suffix. Do not pass compressed archives directly to `get_queries`.

### PDB/mmCIF parsing fails for input sequence extraction

Causes:

- AlphaFold dependencies are not installed.
- The structure lacks parseable protein polymer records.
- mmCIF required fields such as `_entity_poly_seq.mon_id` are missing.

Fix:

- For simple PDB filtering, use `pdb_to_string` with `chains` and `models`.
- For mmCIF conversion/repair, use prediction/template guidance because `validate_and_fix_mmcif` may modify files and requires heavier dependencies.

## Workflow failures owned by this sub-skill

### Mixed A3M/FASTA directory behaves unexpectedly

Expected behavior:

- `.a3m` entries are treated as precomputed MSA input.
- FASTA entries are treated as sequence-only input.
- Default sorting by length can reorder jobs after directory iteration.

Fix:

```bash
python sub-skills/inputs-and-formats/scripts/validate_colabfold_input.py mixed_inputs/ --sort none --json
```

Review each record's `has_a3m`, `sequence_kind`, sanitized name, and duplicate-name warnings before routing to MSA search or prediction.

### Precomputed complex A3M treated as monomer

Cause: missing or malformed serialized header.

Fix: regenerate or preserve the A3M via `msa_to_str`. The first line should look like:

```text
#8,4	2,1
```

### Validator cannot import ColabFold but files look valid

The bundled validator needs ColabFold importable to mirror parser behavior. If that is unavailable, use it only after activating the correct environment, or manually apply the format rules in `data-formats.md` for a first-pass review.
