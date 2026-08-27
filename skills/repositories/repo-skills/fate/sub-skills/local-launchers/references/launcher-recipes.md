# Local Launcher Recipes

## Purpose

Read this when authoring or adapting service-free FATE launcher scripts. The recipes here are distilled from FATE 2.2 local-launcher docs, local ML tutorials, and launcher examples, then rewritten so a future agent does not need to reopen the source checkout.

A local launcher is not a FateFlow job. It uses `fate.arch.launchers.multiprocess_launcher.launch` to spawn local processes for parties such as `guest:9999`, `host:10000`, and `arbiter:10000`, initializes local standalone computing/federation contexts, and calls direct `fate.ml` module APIs.

## Minimal launcher skeleton

```python
from dataclasses import dataclass, field
from fate.arch.launchers.argparser import HfArgumentParser
from fate.arch.launchers.multiprocess_launcher import launch

@dataclass
class MyArguments:
    guest_data: str = field(default=None)
    host_data: str = field(default=None)


def run(ctx):
    # ctx is created separately for each spawned party.
    # Branch on ctx.is_on_guest / ctx.is_on_host / ctx.is_on_arbiter.
    args, _ = HfArgumentParser(MyArguments).parse_args_into_dataclasses(
        return_remaining_strings=True
    )
    ...

if __name__ == "__main__":
    launch(run, extra_args_desc=[MyArguments])
```

Run pattern:

```bash
python my_launcher.py --parties guest:9999 host:10000 --log_level INFO \
  --guest_data ./guest.csv --host_data ./host.csv
```

Important rules:

- `launch(run)` is the documented program entry point for the local multiprocess launcher.
- The `--parties` values are strings in `role:party_id` form. Inside FATE they are parsed to `(role, party_id)` tuples.
- The launcher spawns one process per party. A cheap import check is not the same as a training run.
- Use `extra_args_desc=[YourDataclass]` when the run function parses task-specific arguments with `HfArgumentParser`.
- The default context mode is local. Do not add cluster-only addresses unless you intentionally set `--context_type cluster` and have the cluster backend configured.

## Local context choices

Two safe local patterns appear in the docs and source:

### Let `launch()` create contexts

Use this for normal launcher scripts:

```python
from fate.arch.launchers.multiprocess_launcher import launch

def run(ctx):
    ...  # one call per party

launch(run)
```

The launcher constructs a computing session id from the federation session and local party. For local mode, the helper initializes standalone computing and standalone federation.

### Create a context manually

Use manual context creation for data preflight, notebooks, or unit-like checks before writing a launcher:

```python
from fate.arch.context import create_context

parties = [("guest", "9999"), ("host", "10000")]
ctx = create_context(
    local_party=("guest", "9999"),
    parties=parties,
    federation_session_id="demo-session",
)
```

For Homo NN FedAVG, include the arbiter/server role:

```python
parties = [("guest", "9999"), ("host", "10000"), ("arbiter", "10000")]
```

The DeepSpeed-on-Eggroll tutorial uses non-local engines and host/port settings. Treat that as an advanced cluster path, not the default local launcher path.

## Data setup rules by role

### Hetero tabular data

Vertical/hetero recipes split features by party over common samples.

- Guest normally has labels and a match-id column.
- Host normally has no label but has the same match-id column.
- The launcher examples use match-id columns such as `id` for breast data and `idx` for motor data.
- `CSVReader(...).to_frame(ctx, path)` reads a CSV path into a FATE `DataFrame`.
- `PandasReader(...).to_frame(ctx, pandas_df)` is useful for preflight or generated in-memory data.

Guest breast-style reader:

```python
from fate.arch import dataframe

reader = dataframe.CSVReader(
    sample_id_name=None,
    match_id_name="id",
    delimiter=",",
    label_name="y",
    label_type="int32",
    dtype="float32",
)
input_data = reader.to_frame(ctx, args.guest_data)
```

Host breast-style reader:

```python
reader = dataframe.CSVReader(
    sample_id_name=None,
    match_id_name="id",
    delimiter=",",
    dtype="float32",
)
input_data = reader.to_frame(ctx, args.host_data)
```

SecureBoost tutorial preflight with Pandas adds a `sample_id` column before conversion:

```python
import pandas as pd
from fate.arch.dataframe import PandasReader

def csv_to_df(ctx, file_path, has_label=True):
    df = pd.read_csv(file_path)
    df["sample_id"] = list(range(len(df)))
    if has_label:
        reader = PandasReader(sample_id_name="sample_id", match_id_name="id", label_name="y", dtype="float32")
    else:
        reader = PandasReader(sample_id_name="sample_id", match_id_name="id", dtype="float32")
    return reader.to_frame(ctx, df)
```

### Homo NN tabular data

Horizontal/homo recipes give each client its own rows with the same feature schema and labels. The arbiter has no dataset/model and acts as the server.

```python
if ctx.is_on_guest:
    ds.load("./breast_homo_guest.csv")
elif ctx.is_on_host:
    ds.load("./breast_homo_host.csv")
elif ctx.is_on_arbiter:
    ...  # server/aggregation only
```

### TableReader

`TableReader` reads a table-like backend object rather than a CSV path or `pandas.DataFrame`. It requires `sample_id_name`; use it when a FATE table already exists in the local context, not for ordinary CSV files.

## Recipe: SSHE Logistic Regression

Use for hetero binary classification over guest/host CSVs.

```python
from fate.ml.glm.hetero.sshe import SSHELogisticRegression
from fate.arch import dataframe

ctx.mpc.init()
inst = SSHELogisticRegression(
    epochs=5,
    batch_size=300,
    tol=0.01,
    early_stop="diff",
    learning_rate=args.lr,
    init_param={"method": "random_uniform", "fit_intercept": True, "random_state": 1},
    reveal_every_epoch=False,
    reveal_loss_freq=2,
    threshold=0.5,
)
# Guest reader has label_name="y"; host reader omits label_name.
inst.fit(ctx, train_data=input_data)
model = inst.get_model()
```

Recommended command shape:

```bash
python sshe_lr_launcher.py --parties guest:9999 host:10000 --log_level INFO \
  --guest_data ./breast_hetero_guest.csv --host_data ./breast_hetero_host.csv
```

Notes:

- Call `ctx.mpc.init()` before fitting SSHE modules.
- Keep guest/host match-id columns aligned.
- Full fitting is cryptographic and data-dependent; do an import/signature check first.

## Recipe: SSHE Linear Regression

Use for hetero regression over guest/host CSVs. The launcher pattern matches SSHE LR but uses `SSHELinearRegression`. The motor-data recipe uses:

- guest match-id: `idx`
- guest label: `motor_speed`
- host match-id: `idx`
- label type: `float32`

```python
from fate.ml.glm.hetero.sshe import SSHELinearRegression

ctx.mpc.init()
inst = SSHELinearRegression(
    epochs=5,
    batch_size=300,
    tol=0.01,
    early_stop="diff",
    learning_rate=0.15,
    init_param={"method": "random_uniform", "fit_intercept": True, "random_state": 1},
    reveal_every_epoch=False,
    reveal_loss_freq=2,
    threshold=0.5,
)
inst.fit(ctx, train_data=input_data)
```

## Recipe: Hetero SecureBoost

Use for local vertically federated tree boosting. The tutorial and launcher use `PandasReader`, party-specific guest/host classes, and optional predict-from-model flow.

```python
from fate.ml.ensemble.algo.secureboost.hetero.guest import HeteroSecureBoostGuest
from fate.ml.ensemble.algo.secureboost.hetero.host import HeteroSecureBoostHost

if ctx.is_on_guest:
    bst = HeteroSecureBoostGuest(num_trees=3, objective="binary:bce", max_depth=3, learning_rate=0.3)
else:
    bst = HeteroSecureBoostHost(num_trees=3, max_depth=3)

bst.fit(ctx, data)
model_dict = bst.get_model()
```

Prediction pattern:

```python
pred_ctx = ctx.sub_ctx("predict")
if ctx.is_on_guest:
    pred_bst = HeteroSecureBoostGuest()
else:
    pred_bst = HeteroSecureBoostHost()
pred_bst.from_model(model_dict)
pred = pred_bst.predict(pred_ctx, data)
```

The guest side returns prediction data; the host side participates and may not produce the same printed output.

## Recipe: Pearson correlation

The Pearson launcher imports `PearsonCorrelation`, initializes MPC, reads guest/host CSVs with aligned `id`, then fits:

```python
from fate.ml.statistics.pearson_correlation import PearsonCorrelation

ctx.mpc.init()
inst = PearsonCorrelation()
inst.fit(ctx, input_data=input_data)
print(inst.vif)
```

Use this when the user asks for local feature-correlation/VIF-style checks across one guest and one host. Source evidence shows `PearsonCorrelation.fit` raises when more than one host is present, so do not present it as a multi-host Pearson recipe.

## Recipe: Hetero NN with SSHE aggregate layer

Use for vertically partitioned neural networks with guest/host models.

Core imports:

```python
import torch as t
from fate.ml.nn.hetero.hetero_nn import HeteroNNTrainerGuest, HeteroNNTrainerHost, TrainingArguments
from fate.ml.nn.model_zoo.hetero_nn_model import HeteroNNModelGuest, HeteroNNModelHost, SSHEArgument
```

Guest setup pattern:

```python
bottom_model = t.nn.Sequential(t.nn.Linear(10, 8), t.nn.ReLU())
top_model = t.nn.Sequential(t.nn.Linear(8, 1), t.nn.Sigmoid())
model = HeteroNNModelGuest(
    top_model=top_model,
    bottom_model=bottom_model,
    agglayer_arg=SSHEArgument(
        guest_in_features=8,
        host_in_features=8,
        out_features=8,
        layer_lr=0.01,
    ),
)
optimizer = t.optim.Adam(model.parameters(), lr=0.01)
loss = t.nn.BCELoss()
```

Host setup pattern:

```python
bottom_model = t.nn.Sequential(t.nn.Linear(20, 8), t.nn.ReLU())
model = HeteroNNModelHost(
    bottom_model=bottom_model,
    agglayer_arg=SSHEArgument(
        guest_in_features=8,
        host_in_features=8,
        out_features=8,
        layer_lr=0.01,
    ),
)
optimizer = t.optim.Adam(model.parameters(), lr=0.01)
loss = None
```

Trainer pattern:

```python
args = TrainingArguments(num_train_epochs=3, per_device_train_batch_size=256)
if ctx.is_on_guest:
    trainer = HeteroNNTrainerGuest(ctx=ctx, model=model, train_set=dataset, optimizer=optimizer, loss_fn=loss, training_args=args)
else:
    trainer = HeteroNNTrainerHost(ctx=ctx, model=model, train_set=dataset, optimizer=optimizer, training_args=args)
trainer.train()
pred = trainer.predict(dataset)
```

Caveat: FATE documentation states Hetero-NN currently does not support multi-GPU training and the SSHE layer is incompatible with GPU training. Keep CPU as the default path.

## Recipe: Hetero NN with FedPass

FedPass changes the protection strategy and often the data split. The documented launcher uses image data where the guest has labels/no features and the host has features/no labels.

Guest model pattern:

```python
from fate.ml.nn.model_zoo.hetero_nn_model import FedPassArgument, TopModelStrategyArguments

model = HeteroNNModelGuest(
    top_model=LeNetTop(),
    top_arg=TopModelStrategyArguments(
        protect_strategy="fedpass",
        fed_pass_arg=FedPassArgument(
            layer_type="linear",
            in_channels_or_features=84,
            hidden_features=64,
            out_channels_or_features=10,
            passport_mode="multi",
            activation="relu",
            num_passport=1000,
            low=-10,
        ),
    ),
)
```

Host aggregate-layer pattern:

```python
model = HeteroNNModelHost(
    bottom_model=LeNetBottom(),
    agglayer_arg=FedPassArgument(
        layer_type="conv",
        in_channels_or_features=8,
        out_channels_or_features=16,
        kernel_size=(5, 5),
        stride=(1, 1),
        passport_mode="multi",
        activation="relu",
        num_passport=1000,
    ),
)
```

The launcher example downloads MNIST through `torchvision.datasets.MNIST(download=True)`. That is not safe as a default in generated checks; treat it as a reference recipe unless the user explicitly approves data download/training.

## Recipe: Homo NN FedAVG

Homo NN uses horizontal federated learning. Guest and host are clients; arbiter is the server.

Core imports:

```python
from fate.ml.nn.homo.fedavg import FedAVGArguments, FedAVGClient, FedAVGServer, TrainingArguments
```

Local single-client preflight before federated launch:

```python
trainer = FedAVGClient(
    ctx=ctx,
    model=model,
    train_set=dataset,
    optimizer=optimizer,
    loss_fn=loss_func,
    training_args=args,
    fed_args=fed_args,
)
trainer.set_local_mode()
trainer.train()
```

Federated launcher pattern:

```python
if ctx.is_on_guest or ctx.is_on_host:
    trainer = FedAVGClient(
        ctx=ctx,
        model=model,
        train_set=dataset,
        optimizer=optimizer,
        loss_fn=loss_func,
        training_args=args,
        fed_args=fed_args,
    )
else:
    trainer = FedAVGServer(ctx)
trainer.train()
```

Command shape:

```bash
python homo_nn_launcher.py --parties guest:9999 host:10000 arbiter:10000 --log_level INFO
```

DeepSpeed-on-Eggroll is a separate advanced tutorial using `FederationEngine.OSX`, `ComputingEngine.EGGROLL`, `eggroll task submit`, explicit hosts/ports, and GPUs. Do not turn it into a required local launcher path.

## Recipe: SMPC `proc` wrappers

The launcher examples include two SMPC-style wrappers that take a `module:Class` string, import the class, check that it is an `MPCModule` subclass, initialize `ctx.mpc`, instantiate the class, and call `fit(ctx)`.

Pattern:

```python
import importlib

ctx.mpc.init()
module_name, cls_name = args.proc.split(":", 1)
module = importlib.import_module(module_name)
mpc_cls = getattr(module, cls_name)
# Example code checks issubclass(mpc_cls, MPCModule) before fitting.
inst = mpc_cls()
inst.fit(ctx)
```

Use the bundled checker first:

```bash
python sub-skills/local-launchers/scripts/check_launcher_imports.py \
  --proc some.module:SomeMPCClass --expect-subclass-mpc
```

If `fate.ml.mpc` or `MPCModule` is absent from the installed distribution, treat SMPC `proc` execution as unavailable in that environment rather than inventing replacement APIs.

## Reference-only shortcut list

The launcher shortcut script in the evidence set recaps these command shapes:

```bash
python sshe_lr_launcher.py --parties guest:9999 host:10000 --log_level INFO \
  --guest_data ./breast_hetero_guest.csv --host_data ./breast_hetero_host.csv
python secureboost_launcher.py --parties guest:9999 host:10000 --log_level INFO
python sshe_nn_launcher.py --parties guest:9999 host:10000 --log_level INFO
python fedpass_nn_launcher.py --parties guest:9999 host:10000 --log_level INFO
```

Treat those as patterns. Before running equivalent commands, ensure the target script exists in the user’s workspace, the CSV paths are real, and the user understands it will start a multiprocess training run.
