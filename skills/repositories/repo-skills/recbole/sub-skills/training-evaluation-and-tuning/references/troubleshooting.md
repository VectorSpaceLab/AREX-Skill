# Troubleshooting RecBole training, evaluation, checkpoints, HPO, and runtime

Use this checklist when a RecBole run fails, returns surprising metrics, cannot load a checkpoint, or behaves differently under CPU/GPU/Ray/distributed settings.

## Import and installation failures

Symptoms:

- `ModuleNotFoundError: No module named 'recbole'`
- `ImportError` for `hyperopt`, `ray`, `torch`, `scipy`, or optional logging backends
- helper scripts fail before printing a dry-run config

Actions:

1. Confirm the active Python environment can import RecBole:
   ```bash
   python -c "import recbole; print(recbole.__version__ if hasattr(recbole, '__version__') else recbole.__file__)"
   ```
2. For basic training/evaluation, RecBole and PyTorch must import. HyperTuning additionally needs Hyperopt; Ray workflows need Ray; significance testing needs SciPy.
3. The bundled helpers print targeted import messages and do not require a source checkout.
4. Avoid enabling W&B unless credentials and `wandb` are intentionally configured.

## Dataset/config path failures

Symptoms:

- dataset not found,
- empty or filtered-out dataset,
- unknown field/token,
- Ray trial can find config files but not data files.

Actions:

1. Route atomic data schema, field names, `load_col`, and data root layout to the configuration/data sibling.
2. For normal runs, make paths relative to the process working directory or pass absolute paths.
3. For Ray, make `data_path` absolute. Ray changes each trial's working directory under `local_dir`, so a relative `data_path` such as `./dataset` may point at the trial directory instead of the project directory.
4. When using bundled helpers with `--work-dir`, config file paths are converted to absolute paths before changing directories; dataset paths from config still need to resolve under RecBole's rules.

## No-checkpoint vs saved-checkpoint confusion

Symptoms:

- `FileNotFoundError` when `Trainer.evaluate(load_best_model=True)` tries to load a checkpoint.
- User expected no writes but RecBole created a checkpoint.
- User expected a checkpoint but cannot find one.

Actions:

- For no-checkpoint smoke tests, pass `saved=False` into `run`, `run_recbole`, or `objective_function`.
- If evaluating manually after `trainer.fit(..., saved=False)`, call `trainer.evaluate(..., load_best_model=False)`.
- For saved runs, pass `saved=True` and set `checkpoint_dir` explicitly under a run directory.
- Check logs for the saved `*.pth` path.
- `save_dataset=True` and `save_dataloaders=True` create additional serialized files; they are useful for reproducibility but are not needed for a minimal smoke test.

## Checkpoint loading failures

Symptoms:

- `torch.load` fails,
- checkpoint model architecture mismatch,
- loading expects unavailable CUDA device,
- `load_data_and_model` cannot rebuild data.

Actions:

1. Verify the checkpoint path exists and is a file.
2. Use the same RecBole version family and compatible model code used to create the checkpoint.
3. Ensure the original dataset/config information stored in the checkpoint can still resolve the dataset. If data moved, recreate a compatible config/run or place data where the checkpoint config expects it.
4. If the checkpoint was trained on GPU but loading on CPU, try a CPU-compatible run/config. Some low-level PyTorch errors may require loading with a compatible PyTorch/CUDA environment.
5. In this source version, the verified public loader signature is `load_data_and_model(model_file)`. Inspect your installed signature before passing optional dataset/dataloader paths.

## Case-study top-k failures

Symptoms:

- user token not found,
- `token2id` returns unexpected ids,
- top-k output contains internal ids only,
- full-sort scoring is slow or memory-heavy.

Actions:

- Convert external user tokens with `dataset.token2id(dataset.uid_field, tokens)` before calling case-study helpers.
- Convert internal item ids back with `dataset.id2token(dataset.iid_field, topk_iids.cpu())`.
- Use `full_sort_topk` when only top-k results are needed; `full_sort_scores` materializes scores for all items.
- Remember that padding and history items can be masked to `-inf`.
- Unknown tokens are usually a data/config issue, not a training issue.

## Metric interpretation issues

Symptoms:

- user compares incompatible numbers,
- validation and test metrics have different keys,
- early stopping seems to optimize the wrong metric.

Actions:

1. Check `metrics`, `topk`, `valid_metric`, and `eval_args.mode`.
2. Do not mix ranking metrics (`Recall`, `MRR`, `NDCG`, `Hit`, `MAP`, `Precision`, `GAUC`, coverage/popularity/diversity metrics) with value metrics (`AUC`, `MAE`, `RMSE`, `LogLoss`) in one evaluation setting.
3. Use `valid_score_bigger` from the result dictionary to know whether larger validation score is better.
4. Keep split, order, negative-sampling/evaluation mode, and seed policy identical when comparing models.
5. `full` ranking and sampled modes such as `uni100` or `pop100` are not directly equivalent.

## HyperTuning and Hyperopt failures

Symptoms:

- `Illegal param type`,
- search runs too many trials,
- no model/dataset in objective,
- missing Hyperopt dependency,
- result export missing or empty.

Actions:

- Validate the parameter file with `scripts/recbole_hyperopt_template.py --params-file ./model.hyper --validate`.
- Use supported range types only: `choice`, `uniform`, `loguniform`, `quniform`.
- Quote inner list values in `choice`, for example `mlp_hidden_size choice ['[64,64,64]','[128,128]']`.
- For `exhaustive`, count the full grid before running; RecBole may override `max_evals` to the exhaustive space size.
- For `random` or `bayes`, set `max_evals` explicitly.
- Keep `epochs` small while validating the pipeline.
- Ensure fixed config supplies `model`, `dataset`, data settings, and evaluation settings.

## Ray tuning failures

Symptoms:

- dataset/config found in normal runs but not in Ray trials,
- trials start in a different directory,
- GPU requested but no trials can be scheduled,
- Ray API/scheduler errors.

Actions:

1. Use absolute fixed config paths in `tune.with_parameters(objective_function, config_file_list=[...])`.
2. Set absolute `data_path` in the fixed config. This is the most common fix when Ray changes the working directory to `local_dir`.
3. Match resources and RecBole config:
   - GPU trials: `resources_per_trial={"gpu": 1}` plus compatible RecBole GPU config.
   - CPU trials: `resources_per_trial={"cpu": N, "gpu": 0}` plus `use_gpu: False`.
4. Initialize Ray deliberately: `ray.init()` for local, `ray.init(address='auto')` for an existing cluster.
5. If scheduler metrics are missing, make sure the metric passed to `ASHAScheduler(metric=..., mode=...)` is reported by `objective_function` (for example `recall@10`).

## GPU and CUDA failures

Symptoms:

- CUDA unavailable,
- invalid `gpu_id`,
- out of memory,
- model/device mismatch,
- CPU smoke works but GPU run fails.

Actions:

- CPU is valid for smoke tests: set `use_gpu=False`.
- For GPU, verify PyTorch CUDA availability and that the requested GPU ids are visible.
- Reduce `train_batch_size`, `eval_batch_size`, model size, or `topk` if memory is exhausted.
- Keep `show_progress=False` in agent/non-interactive logs.
- Do not present CPU success as proof that an optional GPU/distributed workflow has been verified.

## Distributed training failures

Symptoms:

- process group timeout,
- hang at launch,
- wrong rank count,
- address/port conflict,
- only one node returns results.

Actions:

- Single-node smoke: keep `nproc=1` and `world_size=-1`.
- For single-node multi-process, set `nproc` to the number of processes/GPU ranks and let `world_size` default or match `nproc`.
- For multi-node, every node must agree on master `ip`, `port`, and total `world_size`.
- `group_offset` must be the lowest global rank on the current node and must not overlap other nodes.
- Check firewall/port availability and GPU visibility before launching.
- Distributed runs multiply resource use; do not use them as default examples.

## Significance-test issues

Symptoms:

- user wants a quick model comparison but asks for significance,
- p-values look inconsistent,
- paired test inputs have different lengths.

Actions:

- Explain cost: two models times `run_times` full trainings.
- Generate one shared seed list and run both models with each seed.
- Collect common metrics from each `test_result` and use `scipy.stats.ttest_rel` on matched arrays.
- Choose `alternative` deliberately; default two-sided tests differ from one-sided `less`/`greater` tests.
- Do not mix different data splits, configs, or metric definitions between models.

## Safe helper behavior

- `recbole_train_eval_smoke.py` prints a dry-run config unless `--run` is supplied.
- `recbole_hyperopt_template.py` writes/validates parameter files by default; it only launches HPO with `--run`.
- `recbole_save_load_recipe.py` validates checkpoint paths and prints a recipe; it only loads and performs top-k case-study scoring when a model file plus `--topk` and `--users` are supplied.
