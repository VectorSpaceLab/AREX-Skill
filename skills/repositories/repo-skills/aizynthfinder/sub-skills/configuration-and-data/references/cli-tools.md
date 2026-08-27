# CLI Tools for Data Setup

AiZynthFinder installs public console scripts for data setup. This skill gives recipes and safety checks; do not execute network downloads, MongoDB writes, or molbloom writes unless the user explicitly asks.

## Installed Scripts

Relevant data/config scripts:

- `download_public_data`: downloads public model/template/filter/stock assets and writes a generated `config.yml`.
- `smiles2stock`: converts SMILES input into HDF5, MongoDB, or molbloom stock data.

Other interfaces such as `aizynthcli` and `aizynthapp` execute retrosynthesis and belong to planning-workflows.

## `download_public_data`

Usage:

```bash
download_public_data /path/to/data-dir
```

Behavior:

- Takes one positional `path` argument.
- Downloads public model, template, filter, ringbreaker, and stock files into that directory.
- Writes `config.yml` in the target directory.
- Uses network access and may download large files.
- Stops with a nonzero exit if an HTTP download fails.

Safe guidance:

1. Ask the user to choose a target directory with enough storage.
2. Confirm network access is allowed.
3. Create or verify the directory if needed.
4. Run the command only after explicit user intent.
5. Validate the generated `config.yml` with `validate_aizynth_config.py` before using it for search.

Do not present `download_public_data` as a dry-run command; it downloads immediately.

## `smiles2stock` Basics

Required arguments:

```bash
smiles2stock --files molecules.smi --output stock.hdf5
```

Important options:

| Option | Values | Notes |
| --- | --- | --- |
| `--files` | one or more inputs | Required. Plain mode expects one SMILES per line. |
| `--output` | path or source tag | Required. HDF5/molbloom output path or MongoDB source tag. |
| `--source` | `plain`, `module` | Default `plain`. Module mode imports an `extract_smiles` function. |
| `--target` | `hdf5`, `mongo`, `molbloom`, `molbloom-inchi` | Default `hdf5`. Mongo and molbloom have side effects or extras. |
| `--host` | MongoDB host | Used for Mongo target. |
| `--bloom_params` | two integers | Required in practice for molbloom targets: filter size and approximate molecule count. |

## HDF5 Stock from Plain SMILES

Use this when the input files contain one SMILES per line and the desired output is a local HDF5 stock.

```bash
smiles2stock --files file1.smi file2.smi --output stock.hdf5 --target hdf5
```

The tool sanitizes SMILES with RDKit, converts valid molecules to InChI keys, drops duplicate InChI keys, and stores a dataframe under HDF5 key `table` with an `inchi_key` column.

Recommended follow-up config:

```yaml
stock:
  local_stock: stock.hdf5
```

## Module-Based SMILES Extraction

Use module mode when input files are CSV, SDF-derived text, supplier exports, or other formats. The module must be importable and expose `extract_smiles`, either with no arguments or with a filename argument.

```bash
PYTHONPATH=$PWD smiles2stock --source module --files load_zinc file1.csv file2.csv --output stock.hdf5
```

Safe guidance:

- Review the custom module before running it; it is arbitrary Python code.
- Keep the module local to the user's project and avoid embedding checkout-specific paths in reusable configs.
- Confirm module mode imports `load_zinc`, not `load_zinc.py`.

## MongoDB Stock Creation

Mongo target writes to a MongoDB database and deletes existing documents with the same `source` tag before inserting the new stock.

```bash
smiles2stock --files molecules.smi --output supplier_2026q1 --target mongo --host mongo-hostname
```

Safety requirements before running:

- User explicitly requests a MongoDB write.
- `pymongo` is installed.
- The MongoDB host and credentials are correct.
- The source tag in `--output` is safe to replace.
- The user understands existing documents for that source tag are deleted before insert.

Recommended config:

```yaml
stock:
  supplier:
    type: mongodb
    host: mongo-hostname
    database: stock_db
    collection: molecules
```

If `--host` is omitted, Mongo connection code may use `MONGODB_HOST` or `localhost` depending on context.

## Molbloom Stock Creation

Molbloom targets require the optional `molbloom` package.

SMILES-based bloom filter:

```bash
smiles2stock --files molecules.smi --output stock.bloom --target molbloom --bloom_params 10000000 1000000
```

InChI-key bloom filter:

```bash
smiles2stock --files molecules.smi --output stock.bloom --target molbloom-inchi --bloom_params 10000000 1000000
```

Safety requirements before running:

- User confirms molbloom is installed or agrees to install optional extras.
- User chooses filter-size and approximate-molecule parameters appropriate for expected false-positive behavior.
- Output path can be overwritten or is new.

Recommended config for InChI-key bloom:

```yaml
stock:
  bloom_stock:
    type: bloom
    path: stock.bloom
    smiles_based: false
```

Recommended config for SMILES-based bloom:

```yaml
stock:
  bloom_stock:
    type: bloom
    path: stock.bloom
    smiles_based: true
```

Do not imply bloom lookup works in an environment until `molbloom` can be imported.

## Safe Static Validation Recipe

After drafting a config or generating one with public data:

```bash
python skills/aizynthfinder/sub-skills/configuration-and-data/scripts/validate_aizynth_config.py config.yml
python skills/aizynthfinder/sub-skills/configuration-and-data/scripts/validate_aizynth_config.py config.yml --json
```

This validator checks YAML shape, env placeholders, bond list shape, policy/filter/stock shape, and likely local asset paths without importing AiZynthFinder or loading assets.

## Command Selection Guide

- Need public starter assets and a generated config: use `download_public_data` after confirming network/storage.
- Need a local HDF5 stock from plain SMILES: use `smiles2stock --target hdf5`.
- Need a local stock from custom supplier format: review a custom `extract_smiles` module, then use `smiles2stock --source module`.
- Need a MongoDB-backed stock: use `smiles2stock --target mongo` only after explicit database-write approval.
- Need a compact bloom filter stock: use a molbloom target only after confirming optional dependency and bloom parameters.
