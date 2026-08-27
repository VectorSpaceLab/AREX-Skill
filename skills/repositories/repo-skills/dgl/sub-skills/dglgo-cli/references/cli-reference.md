# DGL-Go CLI Reference

DGL-Go installs a `dgl` console command through the `dglgo` package. It requires a DGL runtime at least as new as DGL 0.8 and also uses Typer, PyYAML/ruamel.yaml, pydantic, autopep8, isort, OGB, RDKit, and scikit-learn for the full CLI/training stack. In environments where only core DGL is installed, `import dgl` can work while `dglgo` and the `dgl` command are unavailable.

## Command Tree

- `dgl --help`: show the top-level Typer command tree.
- `dgl configure PIPELINE --data DATA --model MODEL --cfg CFG.yaml`: generate a training config for `nodepred`, `nodepred-ns`, or `graphpred`.
- `dgl configure linkpred --data DATA --node-model MODEL --edge-model EDGE_MODEL --neg-sampler SAMPLER --cfg CFG.yaml`: generate a link prediction training config.
- `dgl recipe list`: print bundled YAML recipe filenames, pipeline names, and dataset names.
- `dgl recipe get RECIPE.yaml`: copy one bundled recipe YAML into the current directory.
- `dgl train --cfg CFG.yaml`: generate a pipeline script from YAML and execute training immediately.
- `dgl export --cfg CFG.yaml --output script.py`: generate a runnable Python script without executing it.
- `dgl configure-apply PIPELINE --data DATA --cpt SAVE_DIR/run_i.pth --cfg apply.yaml`: generate an inference config from a training checkpoint. Omit `--data` only when applying to the training dataset.
- `dgl apply --cfg apply.yaml`: generate and execute an inference script from an apply config.

The source CLI registers `configure`, `recipe`, `train`, `export`, `configure-apply`, and `apply`. Some older tests or docs may say `dgl config`; prefer the current `dgl configure` command.

## Training Pipelines

- `nodepred`: full-graph node classification.
- `nodepred-ns`: neighbor-sampling node classification; includes `eval_device` and `general_pipeline.sampler` settings.
- `linkpred`: link prediction with `node_model`, `edge_model`, and `neg_sampler` sections.
- `graphpred`: graph binary classification, commonly with OGB molecule datasets.

## Apply Pipelines

- `nodepred`: node classification inference from a checkpoint.
- `nodepred-ns`: neighbor-sampling node classification inference from a checkpoint.
- `graphpred`: graph classification inference from a checkpoint.
- `linkpred`: train/export config exists, but an apply pipeline is not registered in the source evidence. Do not promise `dgl configure-apply linkpred` unless the installed version proves it.

## Common Examples

Generate, inspect, train, and export a Cora GraphSAGE node classification run:

```bash
dgl configure nodepred --data cora --model sage --cfg cora_sage.yaml
python scripts/dglgo_config_linter.py cora_sage.yaml
dgl train --cfg cora_sage.yaml
dgl export --cfg cora_sage.yaml --output cora_sage_train.py
```

Use a bundled recipe:

```bash
dgl recipe list
dgl recipe get nodepred_cora_sage.yaml
python scripts/dglgo_config_linter.py nodepred_cora_sage.yaml
dgl export --cfg nodepred_cora_sage.yaml --output nodepred_cora_sage.py
```

Generate a link prediction config:

```bash
dgl configure linkpred --data cora --node-model sage --edge-model ele --neg-sampler persource --cfg linkpred_cora.yaml
```

Generate an apply config and export the inference script:

```bash
dgl configure-apply nodepred --data cora --cpt results/run_0.pth --cfg apply_cora.yaml
python scripts/dglgo_config_linter.py apply_cora.yaml
dgl export --cfg apply_cora.yaml --output apply_cora.py
dgl apply --cfg apply_cora.yaml
```

## Validation Habits

- Run `dgl --help`, `dgl configure --help`, and `dgl configure PIPELINE --help` before assuming model/dataset names in an installed version.
- Run the bundled linter before `dgl train` or `dgl apply`; it checks the YAML shape without importing DGL-Go, importing torch, loading checkpoints, or downloading datasets.
- Prefer `dgl export` when you need to customize the generated training loop, swap in a custom model, change loss logic, or audit checkpoint paths before execution.
