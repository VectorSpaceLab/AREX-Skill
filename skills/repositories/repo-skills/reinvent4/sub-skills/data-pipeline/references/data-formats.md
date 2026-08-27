# Data Formats and Config Keys

`reinvent_datapre` is a dedicated preprocessing CLI for SMILES datasets. It is not a `reinvent` `run_type`; invoke it separately with a TOML data-pipeline config.

## CLI

```bash
reinvent_datapre FILE --log-filename data_pipeline.log
```

- `FILE` is a TOML config path.
- `--log-filename FILE` writes preprocessing logs to a file; otherwise logs go to stderr.
- `reinvent_datapre --help` accepts exactly the config `FILE` plus `--log-filename`.
- If importing the installed package fails while asking for `reinvent --help`, install missing runtime dependencies before diagnosing the data-pipeline config. One observed environment needed `scipy` because the main `reinvent` CLI imports plotting utilities that use `scipy.stats.gaussian_kde`; this is separate from data-pipeline schema mistakes.

## Minimal Config

```toml
input_csv_file = "input.tsv"
smiles_column = "SMILES"
separator = "\t"
output_smiles_file = "processed.smi"
num_procs = 1
chunk_size = 500

[filter]
elements = ["I", "O", "Cl", "N", "C", "F", "S", "Br"]
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
report_errors = false
```

## Top-Level Keys

- `input_csv_file`: required input file path. Despite the name, it may point to CSV-like delimited text, `.smi`, or `.smi.gz`.
- `smiles_column`: column containing SMILES. Default schema value is `"SMILES"`.
- `separator`: single-character delimiter used by Polars. Default is tab, written as `"\t"` in TOML.
- `output_smiles_file`: required output path for one processed SMILES per line.
- `num_procs`: worker process count, integer `>= 1`, default `1`. Runtime clips it to available CPU cores and warns when adjusted.
- `chunk_size`: molecules per multiprocessing chunk, integer `>= 1`, default `500`.
- `transform_file`: optional path to an RDKit normalization transform file. If the first line starts with `// TRANSFORM_NAME:`, that name can be listed in `filter.transforms`; otherwise use `"from_file"`.
- `filter`: required in practical configs because preprocessing expects a filter table before it adds base elements and builds filters.

## Filter Keys

- `elements`: additional allowed element symbols. REINVENT adds the base organic set `{C, O, N, S, F, Cl, Br, I}` at runtime. Values must be valid periodic-table symbols.
- `transforms`: list of transform names. Built-ins include `"standard"` and `"four_valent_nitrogen"`; a `transform_file` can also be applied with `"from_file"` or its declared transform name.
- `min_heavy_atoms`, `max_heavy_atoms`: regex-stage heavy atom bounds.
- `max_mol_weight`: approximate regex-stage molecular weight ceiling.
- `min_carbons`: minimum carbon count.
- `max_num_rings`, `max_ring_size`: RDKit-stage ring limits.
- `keep_stereo`: when false, regex handling strips stereochemistry markers before RDKit canonicalization.
- `keep_isotope_molecules`: when false, isotope-labelled molecules are rejected.
- `uncharge`: applies RDKit uncharging and reionization before final SMILES generation.
- `canonical_tautomer`: optional slower tautomer canonicalization; useful only when tautomer collapse is intentional.
- `kekulize`: writes Kekulé SMILES when true.
- `randomize_smiles`: randomizes atom order in output SMILES; keep false for deterministic preprocessing.
- `report_errors`: logs RDKit chemistry problems and skips problem molecules early.
- `inchi_key_deduplicate`: deduplicates final molecules by InChIKey instead of only canonical output SMILES; when duplicates share an InChIKey, the last encountered SMILES is kept.

## Input Behavior

- `.smi` and `.smi.gz` inputs are read without a header. The first delimited field is assigned to `smiles_column`.
- Other suffixes are read with a header and must contain `smiles_column` exactly, including case.
- The delimiter must match `separator`; wrong delimiters often show up as a missing SMILES column or one-column rows containing the whole line.
- Headered CSV/TSV files may include extra columns, but `reinvent_datapre` only reads the selected SMILES column.

## Output Behavior

- `output_smiles_file` contains one filtered, cleaned SMILES per line and no header.
- Duplicates are collapsed after RDKit processing. Without `inchi_key_deduplicate`, final canonical SMILES are converted to a set.
- `regex.smi` is written in the current working directory as an intermediate list after regex filtering. Run from an output/work directory where this side-effect is acceptable.
- Output order is not guaranteed because sets are used during filtering and deduplication.
