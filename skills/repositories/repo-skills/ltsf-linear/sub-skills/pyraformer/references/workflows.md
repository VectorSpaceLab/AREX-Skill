# Workflows

## Long-range forecasting

Use the long-range source entry point when the task is about the benchmark CSV datasets.

Typical train command:

```bash
python scripts/run_pyraformer_long.py --repo-root . -data ETTh1 -data_path ETTh1.csv -input_size 96 -predict_step 168 -n_head 6
```

Typical eval command:

```bash
python scripts/run_pyraformer_long.py --repo-root . -data ETTh1 -data_path ETTh1.csv -input_size 96 -predict_step 168 -n_head 6 -eval
```

Notes:

- The source script writes checkpoints under `models/LongRange/<data>/<predict_step>/`.
- `FC` is the default decoder family used by the benchmark scripts.
- `attention` is available when the user wants the seq2seq-style route instead of the benchmark default.

## Single-step forecasting

Use the single-step source entry point when the task is about electricity, flow, or wind preprocessed inputs.

Typical train command:

```bash
python scripts/run_pyraformer_single.py --repo-root . -data_path data/elect/ -dataset elect
```

Typical eval command:

```bash
python scripts/run_pyraformer_single.py --repo-root . -data_path data/elect/ -dataset elect -eval
```

Notes:

- The source script writes checkpoints under `models/SingleStep/<dataset>/`.
- `elect`, `flow`, and `wind` have fixed dataset-shape assumptions in the source loader.
- The `-pretrain` and `-hard_sample_mining` flags are inverted here because the parser uses `store_false`.

## Preprocessing and synthetic generation

Typical electricity preprocessing command:

```bash
python scripts/prepare_pyraformer_data.py elect --csv data/LD2011_2014.txt --output-dir data/elect
```

Typical flow preprocessing command:

```bash
python scripts/prepare_pyraformer_data.py flow --csv data/app_zone_rpc_hour_encrypted.csv --output-dir data/flow
```

Typical wind preprocessing command:

```bash
python scripts/prepare_pyraformer_data.py wind --csv data/EMHIRESPV_TSh_CF_Country_19862015.csv --output-dir data/wind
```

Typical synthetic generation command:

```bash
python scripts/prepare_pyraformer_data.py synthetic --output-file data/synthetic.npy
```

## Upstream sweep scripts

The upstream shell sweeps are reference-only and should be treated as benchmark presets rather than direct runtime helpers:

- `Pyraformer/scripts/LongForecasting.sh` covers the main long-range grid.
- `Pyraformer/scripts/LookBackWindow.sh` sweeps input lengths and horizons.

Use them as a map for dataset and horizon combinations, then translate the runs into the wrapper commands above when you want a smaller or safer execution.

## Optional TVM route

If the user explicitly asks about `use_tvm`, confirm that they want the optional CUDA/TVM path before enabling it.

- Require a constant `window_size` list.
- Treat `graph_attention.py` and other TVM internals as reference-only.
- Do not include the TVM path in the default smoke or minimum execution plan.
