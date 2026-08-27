# Stocks and Assets

AiZynthFinder configs point to model checkpoints, reaction template tables, stock files, optional route-distance models, and sometimes external services. This reference explains what each asset must provide and what optional dependencies are needed.

## Expansion Model Assets

A template-based expansion policy needs two assets:

- `model`: a trained policy checkpoint. ONNX and Keras/HDF5-style models are common. Remote TensorFlow serving is possible only when `use_remote_models: true` and the serving stack is configured.
- `template`: a table of retrosynthesis templates. HDF5 templates are read with key `table`; `.csv` and `.csv.gz` templates are read as tab-separated files with the first column as index.

Default template column is `retro_template`. If the table uses a different column, set `template_column` explicitly.

```yaml
expansion:
  uspto:
    type: template-based
    model: models/uspto_model.onnx
    template: templates/uspto_templates.csv.gz
    template_column: retro_template
```

The number of model output dimensions must match the number of template rows. A mask file, if provided, must be a NumPy `.npz` containing a Boolean vector with the same length as the template table.

## Filter Model Assets

A quick filter needs one model checkpoint:

```yaml
filter:
  feasibility:
    type: quick-filter
    model: models/uspto_filter_model.onnx
    filter_cutoff: 0.05
```

`exclude_from_policy` can skip filter rejection for named expansion policies. `use_remote_models: true` means the model is expected from a TensorFlow-serving endpoint rather than loaded as a local checkpoint.

## Stock File Formats

File-backed in-memory stocks store precomputed InChI keys. AiZynthFinder accepts:

- HDF5 files with key `table` and an `inchi_key` column by default.
- CSV files with an `inchi_key` column by default.
- Text files with one InChI key per row.
- Optional price metadata in a configured `price_col`; prices must be unique per InChI key, non-null, and non-negative.

Examples:

```yaml
stock:
  hdf5_stock: stocks/zinc_stock.hdf5
  csv_stock:
    type: inchiset
    path: stocks/supplier.csv
    inchi_key_col: inchi_key
    price_col: price
  text_stock:
    type: inchiset
    path: stocks/local_inchikeys.txt
```

For HDF5 and CSV stocks, the configured InChI-key column must exist. For text stocks, every line should already be an InChI key, not a SMILES string.

## MongoDB Stock

A MongoDB stock expects a database collection with documents containing at least:

- `inchi_key`: the lookup key.
- `source`: an availability/source label.

```yaml
stock:
  mongo_stock:
    type: mongodb
    host: mongo-hostname
    database: stock_db
    collection: molecules
```

Defaults are `host: localhost`, `database: stock_db`, and `collection: molecules`. If `host` is omitted, AiZynthFinder also checks `MONGODB_HOST` before falling back to `localhost`. MongoDB stock requires the optional `pymongo` dependency and a reachable MongoDB service. Do not imply the config will work until credentials, network access, and service availability are confirmed.

## Molbloom Stock

Molbloom stocks require the optional `molbloom` package. A short-form stock path ending in `.bloom` chooses a molbloom query automatically.

```yaml
stock:
  bloom_stock: stocks/stock.bloom
```

Full form can set whether lookup uses SMILES rather than InChI keys:

```yaml
stock:
  bloom_stock:
    type: bloom
    path: stocks/stock.bloom
    smiles_based: false
```

Creation of bloom filters is handled by `smiles2stock --target molbloom` or `--target molbloom-inchi`; do not run those commands unless the user confirms `molbloom` is installed and the output path can be written.

## Public Data Bundle

`download_public_data PATH` downloads public model, template, filter, and stock files and writes a `config.yml` under `PATH`. The generated config references:

- `uspto_model.onnx`
- `uspto_templates.csv.gz`
- `uspto_ringbreaker_model.onnx`
- `uspto_ringbreaker_templates.csv.gz`
- `uspto_filter_model.onnx`
- `zinc_stock.hdf5`

The command performs network downloads and can create large files. Use command recipes from `cli-tools.md`, but only execute after explicit user intent and after confirming storage/network constraints.

## Optional Dependencies and Services

| Capability | Needs | Failure surface |
| --- | --- | --- |
| MongoDB stock | `pymongo`, reachable MongoDB, valid credentials | Import error, authentication failure, host unavailable, wrong collection shape. |
| Molbloom stock | `molbloom` | Import error, unreadable `.bloom`, wrong lookup mode. |
| TensorFlow remote serving | `tensorflow`, `grpcio`, `tensorflow-serving-api`, server endpoint | Import error, unavailable server, model key mismatch. |
| Route-distance post-processing | `route-distances`, often `scipy` and plotting stack | Missing package/model, incompatible route-distance checkpoint. |
| Plotting and some analysis views | `matplotlib` and related packages | Import error or headless rendering issues. |

The base package includes core scientific dependencies, RDKit, pandas, PyTables, ONNX runtime, and command entry points, but optional extras still matter for the features above.

## Asset Review Checklist

When reviewing a config, identify each asset-like string and classify it:

- Local file expected: model, template, mask, stock file, route-distance model.
- External service expected: MongoDB host, remote TensorFlow serving source.
- Python import expected: custom strategy, custom stock query, scorer, or search algorithm.
- Output destination: stock output from `smiles2stock` or public-data download directory.

For local files, warn if the path is missing relative to the config file directory and also missing relative to the current working directory. For external services and custom imports, state what must be available but avoid probing unless the user asks.
