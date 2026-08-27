# Customization Recipes

## Replace MNIST with a custom dataset

1. Add a new datamodule class in the target package, following the LightningDataModule shape: constructor, `prepare_data` if needed, `setup`, train/val/test dataloaders, and optional state methods.
2. Create `configs/data/<name>.yaml` with `_target_` pointing to the new class and only constructor parameters that exist.
3. Keep data operations separated:
   - `prepare_data()` may download or create files but should not assign runtime state.
   - `setup()` should assign datasets and be safe on every process.
4. For distributed training, ensure the batch size is divisible by total world size or adapt the guard.
5. Add or adapt tests that can instantiate the datamodule without network. Use tiny fixtures or mocks for real data when possible.

## Add a new model or network component

1. Add a module under the target package, for example `src/models/my_module.py` or the renamed package equivalent.
2. Implement a `LightningModule` with `forward`, train/val/test steps, metric logging, and `configure_optimizers`.
3. Add a config in `configs/model/<name>.yaml` with:
   - `_target_` for the LightningModule;
   - nested `net._target_` for the component if used;
   - optimizer/scheduler partials;
   - any flags such as `compile`.
4. Align logged metric names with callbacks and hparam search. If the model logs `val/f1`, update checkpoint monitor and `optimized_metric` accordingly.
5. Run `_target_` import checks and config instantiation before training.

## Rename the default `src` package

Template-derived projects often rename `src` to a project package. Update all of these together:

- Python imports in source and tests.
- `setup.py` distribution name if desired, package discovery, and console scripts (`train_command = newpkg.train:main`, `eval_command = newpkg.eval:main`).
- Every config `_target_` under `configs/data`, `configs/model`, callback/logger extensions, and any custom groups.
- CI coverage target such as `pytest --cov src`.
- Documentation and Makefile commands if entry files move.
- Any tests that import `src.train`, `src.eval`, data modules, model modules, or helpers.

Then run:

```bash
python <this-skill>/sub-skills/customize-data-model/scripts/check_hydra_targets.py --repo-root .
python <this-skill>/scripts/check_lightning_hydra_project.py --repo-root . --config-name train.yaml --instantiate
```

## Keep configs and constructors synchronized

Hydra forwards config keys to constructors. When a constructor changes:

- remove stale config keys;
- add new required keys;
- keep `_partial_: true` only where an object should be partially applied;
- ensure nested objects such as `net` are compatible with the parent module's signature;
- update tests to cover instantiation and at least one batch shape/metric when data is available.
