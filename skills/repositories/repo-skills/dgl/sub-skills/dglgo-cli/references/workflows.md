# DGL-Go Workflows

## Configure, Train, Export

1. Confirm the `dgl` command comes from DGL-Go: `dgl --help` should list `configure`, `recipe`, `train`, `export`, `configure-apply`, and `apply`.
2. Generate a YAML config with `dgl configure` or copy one with `dgl recipe get`.
3. Lint the YAML with `python scripts/dglgo_config_linter.py CFG.yaml`.
4. Prefer `dgl export --cfg CFG.yaml --output train.py` when you need reviewable code or customization.
5. Run `dgl train --cfg CFG.yaml` only when dependencies, dataset downloads, device, and run time are acceptable.

Example:

```bash
dgl configure nodepred --data cora --model sage --cfg cora_sage.yaml
python scripts/dglgo_config_linter.py cora_sage.yaml
dgl export --cfg cora_sage.yaml --output cora_sage_train.py
dgl train --cfg cora_sage.yaml
```

## Recipes

1. List recipes with `dgl recipe list`.
2. Pick a filename matching the desired pipeline and dataset.
3. Copy it with `dgl recipe get FILENAME.yaml`.
4. Edit `device`, `save_path`, epoch counts, batch sizes, and model hyperparameters for the available runtime.
5. Lint and export before training.

Example:

```bash
dgl recipe list
dgl recipe get graphpred_hiv_gin.yaml
python scripts/dglgo_config_linter.py graphpred_hiv_gin.yaml
dgl export --cfg graphpred_hiv_gin.yaml --output graphpred_hiv_gin.py
```

## Custom CSV Data

1. Prepare CSV graph files plus metadata for DGL CSV loading. For schema details, use `datasets-and-io`.
2. Generate a config with `--data csv`.
3. Set `data.data_path` to the dataset directory.
4. Set `data.split_ratio` if the CSV data does not contain native masks/splits.
5. Lint before training or export.

Example:

```bash
dgl configure nodepred --data csv --model sage --cfg csv_sage.yaml
python scripts/dglgo_config_linter.py csv_sage.yaml
dgl export --cfg csv_sage.yaml --output csv_sage_train.py
```

For link prediction with custom splitting, include both values:

```yaml
data:
  name: csv
  data_path: ./my_csv_graph
  split_ratio: [0.8, 0.1, 0.1]
  neg_ratio: 3
```

## Apply a Checkpoint

1. Train a model with `general_pipeline.save_path` set to a known directory.
2. Locate the checkpoint as `save_path/run_0.pth`, `save_path/run_1.pth`, and so on.
3. Generate an apply config with `dgl configure-apply` and the same pipeline family when possible.
4. Lint the apply YAML.
5. Export the apply script for review or run `dgl apply` directly.

Example:

```bash
dgl configure-apply nodepred --data cora --cpt results/run_0.pth --cfg apply_cora.yaml
python scripts/dglgo_config_linter.py apply_cora.yaml
dgl export --cfg apply_cora.yaml --output apply_cora.py
dgl apply --cfg apply_cora.yaml
```

`configure-apply` loads checkpoint metadata with torch, so it can fail before writing YAML if the checkpoint is missing, incompatible, or produced by a different environment. The linter checks only the final YAML shape; it does not load checkpoints.

## Exported Script Customization

Exported scripts embed model code, data-loading code, config dictionaries, and training or inference loops. For edits such as changing a GNN layer, adding metrics, replacing the loss, or modifying neighbor-sampling internals, use `message-passing-training` after export. Keep DGL-Go YAML responsible for selecting pipeline/model/data and the exported script responsible for deeper experiment customization.
