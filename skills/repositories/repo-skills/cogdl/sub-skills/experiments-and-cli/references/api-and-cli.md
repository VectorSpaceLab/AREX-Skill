# API and CLI Reference

## Verified public API

### `cogdl.experiment`

Signature: `experiment(dataset, model=None, **kwargs)`

Behavior:
- Normalizes a single dataset or model into list form.
- Builds default parsed args through `get_default_args(...)` unless an `args=` namespace is supplied.
- If `model` is omitted, the default model is `autognn`.
- If `search_space` is present, the call switches to AutoML mode.
- If `model == "autognn"` and the caller does not supply `search_space`, `seed`, or `n_trials`, the API supplies defaults.
- If `max_epoch` is present, it is treated as a deprecated alias for `epochs` with a warning.

Common kwargs observed in source and docs:
- `epochs`, `lr`, `weight_decay`, `hidden_size`, `seed`, `split`
- `cpu`, `devices`, `distributed`, `cpu_inference`
- `checkpoint_path`, `resume_training`
- `save_emb_path`, `load_emb_path`
- `logger`, `log_path`, `project`
- `use_best_config`, `n_trials`, `search_space`
- `args` for reusing an already parsed namespace

### `cogdl.options.get_default_args`

Signature: `get_default_args(dataset, model, **kwargs)`

Behavior:
- Converts dataset/model to lists.
- Seeds `sys.argv` so the parser path sees the requested `-m` and `-dt` values.
- Applies `--mw` and `--dw` if supplied.
- Parses dataset- and model-specific flags twice so architecture-specific arguments can be attached.
- Returns a namespace-like object with the requested kwargs applied.

### `gen_variants`

Signature: `gen_variants(**items)`

Behavior:
- Returns a namedtuple stream over the cartesian product of the requested lists.
- Used by `experiment()` to build combinations of dataset/model/seed/split.

### AutoML / `search_space`

- `AutoML` wraps `search_space(trial)` and runs Optuna trials.
- `n_trials` defaults to `3` in generic AutoML mode.
- When `model == "autognn"`, `n_trials` defaults to `20` unless explicitly set.
- Validation metric selection prefers a key containing `Val` or `val` when `metric` is not set.
- If no validation key is found, AutoML raises `KeyError("Unable to find validation metrics")`.

## Verified CLI parser surface from `scripts/train.py --help`

Required flags verified in help output:
- `--dataset` / `-dt`
- `--model` / `-m`
- `--dw` / `-t`
- `--mw`
- `--epochs`
- `--seed`
- `--devices`
- `--cpu`
- `--distributed`
- `--checkpoint-path`
- `--save-emb-path`
- `--load-emb-path`
- `--resume-training`
- `--logger`
- `--log-path`
- `--project`
- `--use-best-config`
- `--n-trials`

Other notable flags from the same parser:
- `--max-epoch`, `--patience`, `--lr`, `--weight-decay`, `--n-warmup-steps`, `--split`, `--clip-grad-norm`
- `--cpu-inference`, `--progress-bar`, `--local_rank`, `--master-port`, `--master-addr`
- `--return_model`, `--actnn`, `--fp16`, `--rp-ratio`, `--do_test`, `--do_valid`, `--unsup`, `--nstage`, `--eval-step`

## Result semantics

`experiment()` returns a dictionary keyed by `(dataset, model)` tuples.

Typical value shape:
- each key maps to a list of per-seed result dictionaries
- each result dictionary contains metric names such as `test_acc`, `val_acc`, or embedding-evaluation metrics depending on workflow

Printed output:
- `output_results(...)` tabulates means and standard deviations over seeds.
- The displayed header always begins with `Variant`.
- When multiple seeds are passed, the table shows `mean±std` strings per metric.

## Built-in dataset download warning

Built-in datasets may download or populate a cache the first time they are used.
That includes common benchmark names such as `cora`, `citeseer`, `pubmed`, `ppi`, `flickr`, `blogcatalog`, `mutag`, `ogbn-arxiv`, and other registry entries.
Treat first-run dataset access as optional network/cache work unless the data is already available locally.

## Verified wrapper defaults relevant to experiments

Default wrapper matches observed in source:
- `gcn` -> `node_classification_mw` + `node_classification_dw`
- `gat` -> `node_classification_mw` + `node_classification_dw`
- `gin` -> `graph_classification_mw` + `graph_classification_dw`
- `prone` -> `network_embedding_mw` + `network_embedding_dw`
- `gatne` -> `multiplex_embedding_mw` + `multiplex_embedding_dw`
- `stgcn` -> `stgcn_mw` + `stgcn_dw`

If a requested model is not in the default wrapper map, the experiment path may require explicit `mw` / `dw` values.
