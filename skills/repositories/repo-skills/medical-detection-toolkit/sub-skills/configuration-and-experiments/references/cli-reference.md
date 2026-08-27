# CLI reference and bounded invocation

`exec.py` is the legacy top-level execution entry point. Live `--help` was
checked in the inspection environment without starting a job. The parser
accepts the following options:

| Option | Default | Meaning and safe interpretation |
|---|---|---|
| `-m`, `--mode` | `train_test` | `train`, `test`, `train_test`, `analysis`, or `create_exp`; unknown values raise a runtime error |
| `-f`, `--folds` | `None` | one or more integer fold IDs; `None` means `range(cf.n_cv_splits)`; the parser does not enforce bounds |
| `--exp_dir` | `/path/to/experiment/directory` | experiment output/snapshot directory; replace the placeholder explicitly |
| `--server_env` | false | selects deployment/cloud path behavior in configs and loaders |
| `--data_dest` | `None` | alternate final data directory, particularly used by server-side data handling |
| `--use_stored_settings` | false | training may use the existing experiment snapshot; testing forces stored settings |
| `--resume_to_checkpoint` | `None` | checkpoint path; a fold must also be selected with `--folds` |
| `--exp_source` | `experiments/toy_exp` | source experiment directory containing `configs.py` and `data_loader.py` |
| `-d`, `--dev` | false | in-memory bounded development settings; not a correctness or performance result |

For a version-aware read-only view, run the bundled helper from the generated
skill directory:

```bash
python sub-skills/configuration-and-experiments/scripts/inspect_cli.py
python sub-skills/configuration-and-experiments/scripts/inspect_cli.py --check \
  --mode create_exp --folds 0 --exp-dir /absolute/work/mdt-exp \
  --exp-source experiments/toy_exp
```

The helper does not import `exec.py`, access the source checkout implicitly, or
write files. If given `--exec-file`, it parses a bounded copy of the file with
`ast` and reports literal `add_argument` declarations; that file is an input,
not a runtime dependency.

## Mode behavior

### `train`

`exec.py` calls `utils.prep_exp(args.exp_source, args.exp_dir,
args.server_env, args.use_stored_settings)`, puts `cf.data_dest` in the config,
dynamically imports the configured model and the source data loader, defaults
to all CV folds, and for each fold sets `cf.fold_dir` to
`<exp_dir>/fold_<fold>`, `cf.fold`, and `cf.resume_to_checkpoint`. It creates
that fold directory if absent, then enters the CUDA-backed training routine.
Do not use this mode for config validation.

### `train_test`

This follows the `train` setup and immediately runs the test routine after each
fold. It can therefore create checkpoints, plots, logs, predictions, and
metrics. The default mode is not safe merely because the parser accepts it.

### `test`

Testing calls `prep_exp(..., is_training=False, use_stored_settings=True)`,
which reads `configs.py`, `model.py`, and `backbone.py` from the experiment
snapshot and copies the snapshot model/backbone into the source `models`
directory as temporary modules. It then loops over selected/all folds and
loads test predictions. A complete, compatible snapshot is required. This is
not a CPU-only smoke test.

### `analysis`

Analysis also loads stored settings but does not construct a training model. It
loads saved predictions and applies prediction aggregation. With
`hold_out_test_set=True`, it assigns `cf.folds=args.folds`, creates CSV output,
and otherwise loops over folds, evaluates predictions, and scores the test
DataFrame. Saved prediction format and metrics belong to
[../inference-and-evaluation](../../inference-and-evaluation/SKILL.md).

### `create_exp`

This is intended to create the experiment directory and copy scripts without
starting a job. It calls `prep_exp` with `use_stored_settings=True` and the
training default. It can still create directories/copies and may touch source
temporary model modules through the legacy preparation path. Use a new,
explicitly disposable workspace and inspect the resulting snapshot; do not
assume it is a no-write dry run.

## Fold and checkpoint rules

- No `--folds` means `0 ... cf.n_cv_splits-1`; the common default is 0 through
  4.
- `--folds 0 2` is a valid selective request if those folds exist. Use one or
  more IDs; do not pass a comma-separated string.
- `--resume_to_checkpoint` only sets the resume path for each requested fold;
  it does not select a fold. Always pair it with `--folds N` and verify that
  the checkpoint contains the expected `params.pth` and monitoring pickle.
- In non-hold-out experiments, the data loader reads `fold_ids.pickle` under
  `exp_dir` and uses the selected fold's test indices. In hold-out experiments,
  test data comes from `cf.pp_test_data_path` and the folds are used for model
  selection/ensembling as configured.
- `--dev` in train/train_test forces folds `[0, 1]`, one epoch, a small number
  of batches/patients, and one saved model; in test it forces folds `[0, 1]`,
  one test epoch and one patient. This still enters model/data code and is
  intentionally excluded from configuration-only verification.
- If a request names a fold outside the configured range, stop before the
  framework creates a partial fold directory. The CLI has no explicit guard.

## Invocation policy

The legacy execution entry point accepts the modes and flags in the table
above. Before invoking it in a maintained checkout, run the bundled static
helper with `--check`, replace the placeholder output directory with a fresh
absolute workspace, validate the experiment source/config and fold IDs, and
review the copy/mutation caveat in [experiment-layout](experiment-layout.md).
The helper's check is the portable command-generation smoke; it never launches
training, testing, analysis, or snapshot copying.

Use stored settings only when the snapshot is intentionally the source of
truth. Keep server/data-destination flags aligned with the config's deployment
assumptions. Do not use shell paths containing unquoted spaces with legacy copy
calls. Full train/test/analysis invocation remains a checkout-and-data workflow,
not a runtime dependency of this generated skill.
