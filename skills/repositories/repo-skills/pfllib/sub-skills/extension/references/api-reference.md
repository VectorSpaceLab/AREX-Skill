# Extension API Reference

## Purpose

Read this when you are wiring a new algorithm, model, optimizer, or dataset
into the PFLlib registry.

## Core hook classes

### `Server`

From `system/flcore/servers/serverbase.py`.

Important methods and responsibilities:

- `__init__(args, times)` — capture the experiment settings and clone the
  initial model.
- `set_clients(clientObj)` — instantiate the client objects.
- `set_slow_clients()` / `select_slow_clients()` — mark slow trainers and slow
  senders.
- `select_clients()` — choose the participating clients for a round.
- `send_models()` / `receive_models()` — push the global model and collect local
  updates.
- `aggregate_parameters()` / `add_parameters()` — combine local models.
- `save_global_model()` / `save_results()` — persist checkpoints and h5 output.
- `evaluate()` / `test_metrics()` / `train_metrics()` — measure progress.
- `call_dlg()` — DLG privacy evaluation path.

### `Client`

From `system/flcore/clients/clientbase.py`.

Important methods and responsibilities:

- `__init__(args, id, train_samples, test_samples, **kwargs)` — capture the
  client-local state.
- `load_train_data()` / `load_test_data()` — rebuild a PyTorch DataLoader from
  the client split files.
- `set_parameters(model)` / `clone_model(model, target)` / `update_parameters()`
  — synchronize model state.
- `train()` — the per-client local optimization loop in the subclass.
- `test_metrics()` / `train_metrics()` — evaluate the client model.
- `save_item()` / `load_item()` — persist client-local artifacts.

## Model contract

The experiment runner and several algorithms assume the selected model can be
split into a backbone and a classifier head.

Common expectations:

- the model exposes an `fc` attribute for the classifier head
- some algorithms replace `fc` with `nn.Identity()` and wrap the model in
  `BaseHeadSplit`
- text models return log-probabilities or logits with the correct class count
- image models match the shape implied by the dataset family

If a new model does not have an `fc` attribute, you may need to adapt the
algorithm registration rather than only adding a new class.

## Dataset generator contract

Generators under `dataset/generate_*.py` usually follow this flow:

1. create `dataset/<name>/`
2. check whether the current split already exists
3. download or read the raw dataset
4. preprocess the raw data into arrays or token sequences
5. call `separate_data()`
6. call `split_data()`
7. call `save_file()`

The shared helpers live in `dataset/utils/dataset_utils.py` and
`dataset/utils/HAR_utils.py`.

## Optimizer hook

`system/flcore/optimizers/fedoptimizer.py` is the place to add a new optimizer
used by training code.

## Registry edits

When you add a new feature, check all of the following:

- import the new server/client/model module in `system/main.py`
- add the new algorithm branch in the algorithm selection block
- add the new model branch in the model selection block if needed
- ensure the dataset loader can find the new dataset name
- confirm the new CLI value shows up in `scripts/scan_registry.py`

## Optional dependency hooks

- `FedPAC` imports `cvxpy`.
- AG News and Sogou News require `torchtext`.
- torchvision-backed models rely on `torchvision`.
- DLG and memory reporting use the shared utilities in `system/utils/`.
