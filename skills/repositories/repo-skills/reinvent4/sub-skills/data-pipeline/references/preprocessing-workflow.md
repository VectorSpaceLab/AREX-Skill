# Preprocessing Workflow

Use this workflow to build a reliable REINVENT4 SMILES preprocessing job before downstream sampling, scoring, transfer learning, staged learning, or enumeration.

## 1. Prepare a Tiny Representative Fixture

Generate a fixture that deliberately includes valid molecules, duplicates, invalid syntax, a salt/fragment, a stereochemical molecule, and an unexpected element:

```bash
python sub-skills/data-pipeline/scripts/make_tiny_smiles_fixture.py --out-dir dpl_smoke --format csv --separator comma
```

The helper writes a fixture data file and a matching `data_pipeline.toml`. Use it as a local pattern for column names, delimiters, and expected filtering behavior.

## 2. Build the Real Config

Start with a conservative, deterministic config:

```toml
input_csv_file = "library.tsv"
smiles_column = "SMILES"
separator = "\t"
output_smiles_file = "library.cleaned.smi"
num_procs = 1
chunk_size = 500

[filter]
elements = ["C", "N", "O", "S", "F", "Cl", "Br", "I"]
transforms = ["standard"]
min_heavy_atoms = 2
max_heavy_atoms = 90
max_mol_weight = 1200.0
min_carbons = 2
max_num_rings = 12
max_ring_size = 7
keep_stereo = true
keep_isotope_molecules = true
uncharge = true
kekulize = false
randomize_smiles = false
report_errors = true
inchi_key_deduplicate = false
```

Prefer `randomize_smiles = false` while validating. Turn on `inchi_key_deduplicate` when tautomer/salt/representation-level duplicates matter more than preserving the exact last canonical string set.

## 3. Validate Without Running Preprocessing

```bash
python sub-skills/data-pipeline/scripts/validate_data_pipeline_config.py data_pipeline.toml --sample-rows 50
```

The validator checks TOML parsing, required fields, allowed top-level/filter keys, delimiter shape, input existence, selected SMILES column, output parent, transform-file naming, numeric bounds, and a sample of likely invalid or suspicious SMILES. It does not import REINVENT, import RDKit, write output, or launch preprocessing.

Use `--strict` when warnings should fail CI-style checks:

```bash
python sub-skills/data-pipeline/scripts/validate_data_pipeline_config.py data_pipeline.toml --strict
```

## 4. Run a Smoke Preprocess

Run from a scratch/output directory so `regex.smi` lands somewhere expected:

```bash
reinvent_datapre data_pipeline.toml --log-filename data_pipeline.log
```

Review:

- Number of input SMILES.
- Number after regex filtering.
- Discarded tokens when `num_procs = 1`.
- Number after chemistry filtering.
- `output_smiles_file` exists and has plausible one-column SMILES.
- `regex.smi` does not reveal an unexpectedly aggressive token filter.

## 5. Scale Safely

- Increase `num_procs` only after the one-core run behaves correctly.
- Keep `chunk_size` modest unless profiling shows multiprocessing overhead dominates.
- Expect runtime to clip `num_procs` to available cores.
- Avoid `canonical_tautomer = true` on a large dataset until a subset confirms the cost is acceptable.
- Do not overwrite a curated output unless the validation report explicitly notes that overwrite is intended.

## Filter Semantics

### Regex Stage

The regex stage tokenizes SMILES and rejects entries before RDKit cleanup when they violate cheap rules:

- Empty SMILES are skipped.
- Tokens outside the supported SMILES token regex are silently dropped from tokenization; treat this as a reason to inspect `regex.smi` and logs.
- Bracketed high-valent or charged halogen tokens such as `[Cl+]`, `[Br+3]`, or `[IH]` are rejected.
- Elements must be in the runtime allowed set: base elements `{C, O, N, S, F, Cl, Br, I}` plus configured `elements`.
- Heavy atom, carbon count, and approximate molecular-weight thresholds are enforced.
- Isotopes are either normalized to element patterns or rejected according to `keep_isotope_molecules`.
- Stereochemistry markers are preserved or stripped according to `keep_stereo`.
- Atom-map indexes are stripped to the atom pattern.

### RDKit Stage

The RDKit stage parses and standardizes surviving SMILES:

- Chooses the largest fragment with organic preference.
- Applies RDKit normalization transforms from `filter.transforms` and optional `transform_file`.
- Rejects molecules that fail RDKit parsing, sanitization, chemistry-problem reporting, ring-count limits, or ring-size limits.
- Optionally uncharges and reionizes molecules.
- Optionally canonicalizes tautomers.
- Emits canonical, stereochemistry-aware, Kekulé, or randomized SMILES according to config flags.

### Deduplication Stage

- Default deduplication converts final RDKit SMILES to a set and writes one copy of each string.
- `inchi_key_deduplicate = true` deduplicates by RDKit InChIKey using the associated molecule objects and keeps the last SMILES for each key.
- Output order should not be used as a stable signal.

## Downstream Handoff

- For `run_type = "sampling"`, use the cleaned `.smi` as a seed file only when the selected generator mode expects seed/conditional input; see `sampling`.
- For `run_type = "scoring"`, use the cleaned `.smi` as the scoring `smiles_file`; see `scoring`.
- For `run_type = "transfer_learning"` or `run_type = "staged_learning"`, validate that the cleaned SMILES format matches the model family and learning config; see `learning`.
- For `run_type = "enumeration"`, keep data-pipeline cleanup separate from peptide/library enumeration config; see `enumeration`.
