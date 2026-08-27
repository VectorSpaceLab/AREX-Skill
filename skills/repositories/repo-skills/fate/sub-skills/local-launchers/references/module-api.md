# Local Launcher Module API

## Purpose

Read this when choosing imports and constructor arguments for service-free FATE local launcher authoring. The facts below are backed by installed package inspection for `pyfate` 2.2.0 / import name `fate`, `fate_utils` 0.1.0, and assigned source/docs evidence.

## Package and backend facts

- Distribution `pyfate` version: `2.2.0`; import name: `fate`.
- Distribution `fate_utils` version: `0.1.0`; required by local cryptographic/dataframe paths.
- `fate_client` and `fate_flow` were installed in the verified environment, but service-backed Pipeline/FateFlow APIs are intentionally out of this sub-skill; route to `pipeline-workflows` or `deployment`.
- Verified PyTorch baseline: `torch` 2.3.1 CPU build; `torch.cuda.is_available()` was false during construction. Treat GPU/DeepSpeed as optional and unverified here.

## Context and launcher APIs

| API | Import | Verified signature / use |
| --- | --- | --- |
| `Context` | `from fate.arch import Context` or `from fate.arch.context import Context` | `Context(device=CPU, computing=None, federation=None, metrics_handler=None, namespace=None, cipher=None)` |
| `CipherKit` | `from fate.arch import CipherKit` | `CipherKit(device, cipher_mapping=None)` |
| `create_context` | `from fate.arch.context import create_context` | `create_context(local_party, parties, federation_session_id, federation_engine=STANDALONE, federation_conf=None, computing_session_id=None, computing_engine=STANDALONE, computing_conf=None)` |
| `HfArgumentParser` | `from fate.arch.launchers.argparser import HfArgumentParser` | `HfArgumentParser(dataclass_types, **kwargs)` generates CLI args from dataclass fields. |
| `LauncherArguments` | `from fate.arch.launchers.multiprocess_launcher import LauncherArguments` | `LauncherArguments(parties, federation_session_id=<factory>, tracer_id=<factory>, data_dir=None, log_level='INFO')` |
| `MultiProcessLauncher` | `from fate.arch.launchers.multiprocess_launcher import MultiProcessLauncher` | `MultiProcessLauncher(console, parties=None, federation_session_id=None, data_dir=None, log_level=None)` |
| `launch` | `from fate.arch.launchers.multiprocess_launcher import launch` | `launch(f, **kwargs)`; documented entry point for normal scripts. |

### `create_context` tuple rules

`local_party` is a tuple like `("guest", "9999")`. `parties` is a list of such tuples. The multiprocess launcher accepts strings like `guest:9999` and parses them into tuples. Bad tuple shapes or rank/party mismatches are common launcher errors; see [troubleshooting.md](troubleshooting.md).

## DataFrame readers

| Reader | Verified signature | Use |
| --- | --- | --- |
| `CSVReader` | `CSVReader(sample_id_name=None, match_id_list=None, match_id_name=None, delimiter=',', label_name=None, label_type='int', weight_name=None, weight_type='float32', dtype='float32', na_values=None, partition=4, block_row_size=None)` | Convert a CSV file path into a FATE `DataFrame`: `CSVReader(...).to_frame(ctx, path)`. |
| `PandasReader` | `PandasReader(sample_id_name=None, match_id_list=None, match_id_name=None, label_name=None, label_type='int32', weight_name=None, weight_type='float32', dtype='float32', partition=4, block_row_size=None)` | Convert a `pandas.DataFrame` into a FATE `DataFrame`: `PandasReader(...).to_frame(ctx, df)`. Source checks require `match_id_name` when `sample_id_name` is supplied. |
| `TableReader` | `TableReader(sample_id_name=None, match_id_name=None, match_id_list=None, match_id_range=0, label_name=None, label_type='int', weight_name=None, weight_type='float32', header=None, delimiter=',', dtype='float32', anonymous_site_name=None, na_values=None, input_format='dense', tag_with_value=False, tag_value_delimiter=':', block_row_size=None)` | Convert an existing local table-like object. Source code requires `sample_id_name` and currently supports dense input format. |

Reader selection:

- Use `CSVReader` for user-supplied CSV paths in launcher scripts.
- Use `PandasReader` for preflight, tiny fixtures, and generated dataframes.
- Use `TableReader` only when the user already has a FATE table object and can provide header/sample-id information.

## Direct ML module constructors

### SSHE GLM

Import:

```python
from fate.ml.glm.hetero.sshe import SSHELogisticRegression, SSHELinearRegression
```

Verified constructors:

```text
SSHELogisticRegression(epochs, batch_size, tol, early_stop, learning_rate, init_param, reveal_every_epoch=False, reveal_loss_freq=1, threshold=0.5)
SSHELinearRegression(epochs, batch_size, tol, early_stop, learning_rate, init_param, reveal_every_epoch=False, reveal_loss_freq=1, threshold=0.5)
```

Pattern:

- Call `ctx.mpc.init()`.
- Convert guest/host CSVs to FATE `DataFrame`s.
- Call `inst.fit(ctx, train_data=input_data)`.
- Read `inst.get_model()` when the fit completes.

### Hetero SecureBoost

Imports:

```python
from fate.ml.ensemble.algo.secureboost.hetero.guest import HeteroSecureBoostGuest
from fate.ml.ensemble.algo.secureboost.hetero.host import HeteroSecureBoostHost
```

Verified constructors:

```text
HeteroSecureBoostGuest(num_trees=3, max_depth=3, complete_secure=0, learning_rate=0.3, objective='binary:bce', num_class=1, max_bin=32, l2=0.1, l1=0, min_impurity_split=0.01, min_sample_split=2, min_leaf_node=1, min_child_weight=1, goss=False, goss_start_iter=0, top_rate=0.2, other_rate=0.1, gh_pack=True, split_info_pack=True, hist_sub=True, random_seed=42)
HeteroSecureBoostHost(num_trees=3, max_depth=3, complete_secure=0, max_bin=32, hist_sub=True)
```

Pattern:

- Instantiate the guest class on guest; host class on host.
- Call `fit(ctx, data)`.
- Use `get_model()` / `from_model(model_dict)` for model dump/load inside local scripts.
- Use `ctx.sub_ctx('predict')` or a separate context scope for prediction to avoid mixing training/prediction federation names.

### Pearson correlation

Import:

```python
from fate.ml.statistics.pearson_correlation import PearsonCorrelation
```

Source-backed constructor and method:

```text
PearsonCorrelation(local_only=False, calc_local_vif=True, select_cols=None)
fit(ctx, input_data)
get_model()
```

Source code checks one-host scope: `fit` raises if more than one host exists. Use this for one guest + one host feature-correlation/VIF launchers.

### Hetero NN

Imports:

```python
from fate.ml.nn.hetero.hetero_nn import HeteroNNTrainerGuest, HeteroNNTrainerHost, TrainingArguments
from fate.ml.nn.model_zoo.hetero_nn_model import HeteroNNModelGuest, HeteroNNModelHost, SSHEArgument, FedPassArgument
```

Verified constructors:

```text
HeteroNNModelGuest(top_model, bottom_model=None, agglayer_arg=None, top_arg=None, ctx=None)
HeteroNNModelHost(bottom_model=None, agglayer_arg=None, ctx=None)
SSHEArgument(guest_in_features=8, host_in_features=8, out_features=8, layer_lr=0.01, precision_bits=None)
FedPassArgument(merge_type='sum', layer_type='conv', in_channels_or_features=8, out_channels_or_features=8, kernel_size=3, stride=1, padding=0, bias=True, hidden_features=128, activation='relu', passport_distribute='gaussian', passport_mode='single', loc=-1.0, scale=1.0, low=-1.0, high=1.0, num_passport=1, ae_in=None, ae_out=None)
HeteroNNTrainerGuest(ctx, model, training_args, train_set, val_set=None, loss_fn=None, optimizer=None, data_collator=None, scheduler=None, tokenizer=None, callbacks=[], compute_metrics=None)
HeteroNNTrainerHost(ctx, model, training_args, train_set, val_set=None, optimizer=None, data_collator=None, scheduler=None, tokenizer=None, callbacks=[], compute_metrics=None)
```

Training arguments are HuggingFace-style. Verified key fields include `output_dir`, `do_train`, `do_eval`, `do_predict`, `num_train_epochs`, `per_device_train_batch_size`, `per_device_eval_batch_size`, `learning_rate`, `evaluation_strategy`, `logging_strategy`, `save_strategy`, `use_cpu=True`, `no_cuda=False`, and `deepspeed=None`.

Use `SSHEArgument` for the SSHE aggregate layer. Use `FedPassArgument` with `TopModelStrategyArguments` or aggregate-layer arguments for FedPass patterns as shown in [launcher-recipes.md](launcher-recipes.md).

### Homo NN FedAVG

Imports:

```python
from fate.ml.nn.homo.fedavg import FedAVGArguments, FedAVGClient, FedAVGServer, TrainingArguments
```

Verified constructors:

```text
FedAVGArguments(aggregate_strategy='epoch', aggregate_freq=1, aggregator='secure_aggregate')
FedAVGClient(ctx, model, training_args, fed_args, train_set, val_set=None, loss_fn=None, optimizer=None, scheduler=None, callbacks=[], data_collator=None, tokenizer=None, use_hf_default_behavior=False, compute_metrics=None, local_mode=False)
FedAVGServer(ctx, local_mode=False)
```

Patterns:

- Local preflight: instantiate `FedAVGClient(..., local_mode=True)` or call `trainer.set_local_mode()` before `trainer.train()`.
- Federated local launcher: guest and host instantiate `FedAVGClient`; arbiter instantiates `FedAVGServer`.
- Include `arbiter` in `--parties` for federated FedAVG.

### Preprocessing helpers

Imports:

```python
from fate.ml.preprocessing.feature_scale import FeatureScale
from fate.ml.preprocessing.union import Union
```

Verified constructors:

```text
FeatureScale(method='standard', scale_col=None, feature_range=None, strict_range=True)
Union(axis=0)
```

These are useful support modules inside local scripts, but do not use them as a substitute for FateFlow Pipeline components when the user specifically asks for service-backed component workflows.

## Helper script usage

Cheap standard check:

```bash
python sub-skills/local-launchers/scripts/check_launcher_imports.py --check-standard
```

Check a specific class:

```bash
python sub-skills/local-launchers/scripts/check_launcher_imports.py \
  --module fate.ml.nn.homo.fedavg --object FedAVGClient
```

Check a launcher script file without running training:

```bash
python sub-skills/local-launchers/scripts/check_launcher_imports.py \
  --module-path ./my_launcher.py --object run --expect-callable
```

Only run training when the user explicitly asks and has provided data/party arguments. See the helper `--help` output for the double-confirmation flags.
