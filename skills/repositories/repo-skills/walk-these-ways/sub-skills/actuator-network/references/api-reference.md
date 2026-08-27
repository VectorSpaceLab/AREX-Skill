# Actuator-network API reference

These signatures are transcribed from `scripts/actuator_net/utils.py`. The
source module also imports plotting, image, and repository utilities, so use
these as behavioral references rather than importing the source module from a
source-relative working directory. For input alignment, see
[data-format.md](data-format.md); for safe execution choices, see
[workflow.md](workflow.md).

## `Act`

```python
class Act(nn.Module):
    def __init__(self, act, slope=0.05):
    def forward(self, input):
```

`act` is a string. The source supports `relu`, `leaky_relu`, `sp`,
`leaky_sp`, `elu`, `leaky_elu`, `ssp`, `leaky_ssp`, `tanh`, `leaky_tanh`,
`swish`, and `softsign`; an unknown name raises `RuntimeError`. `slope` is
used by the leaky variants. For the actuator model, the verified choice is
`softsign` and the default slope is not otherwise relevant.

## `build_mlp`

```python
def build_mlp(in_dim, units, layers, out_dim,
              act='relu', layer_norm=False, act_final=False):
```

The returned value is `torch.nn.Sequential`. It starts with
`Linear(in_dim, units)` plus `Act(act)`, adds `layers - 1` more
`Linear(units, units)` plus activation pairs, then adds `Linear(units,
out_dim)`. If `act_final=True`, it appends the activation; if
`layer_norm=True`, it appends `LayerNorm(out_dim)` after the output. The
actuator source call is:

```python
build_mlp(in_dim=6, units=32, layers=2, out_dim=1, act='softsign')
```

That is two hidden 32-unit layers with softsign and a one-dimensional linear
output. `layer_norm` and `act_final` remain false by default.

## `ActuatorDataset`

```python
class ActuatorDataset(Dataset):
    def __init__(self, data):
    def __len__(self):
    def __getitem__(self, idx):
```

`data` is a dictionary of indexable arrays/tensors. `__len__` returns the
length of `data['joint_states']`; `__getitem__` returns a dictionary containing
`v[idx]` for every key/value pair. The source training call supplies:

```python
ActuatorDataset({"joint_states": xs, "tau_ests": ys})
```

The source expects `xs` to have six columns and `ys` one column. It does not
perform schema validation here, so validate first with the bundled scripts.

## `train_actuator_network`

```python
def train_actuator_network(xs, ys, actuator_network_path):
```

Source defaults and behavior:

- prints `xs.shape` and `ys.shape`;
- computes `num_train = num_data // 5 * 4` and the remaining validation size;
- uses `ActuatorDataset`, `random_split`, `DataLoader(batch_size=128,
  shuffle=True)`, and MSE loss;
- builds the 6 -> 32 -> 32 -> 1 softsign MLP described above;
- uses `Adam(lr=8e-4, eps=1e-8, weight_decay=0.0)`;
- hard-codes `epochs = 100` and `device = 'cuda:0'`;
- prints epoch loss, validation loss, and MAE;
- scripts and saves the model to `actuator_network_path` during the loop and
  returns the trained model.

The source has no epoch, device, seed, or overwrite parameter. Treat its 100
epochs and CUDA requirement as opt-in source behavior only. Prefer a bounded
adapter that makes these controls explicit, and re-load the final TorchScript
on CPU before use. Do not call this function from an unapproved or headless
smoke check.

## `train_actuator_network_and_plot_predictions`

```python
def train_actuator_network_and_plot_predictions(
    log_dir_root, log_dir, actuator_network_path,
    load_pretrained_model=False):
```

The source forms its input path by string concatenation:

```python
log_path = log_dir_root + log_dir + "log.pkl"
```

It loads `data['hardware_closed_loop'][1]`, requires `tau_est`, extracts
`joint_pos`, `joint_pos_target`, `joint_vel`, `tau_est`, and `torques`, builds
samples with `step = 2`, and then either loads the TorchScript artifact on CPU
when `load_pretrained_model=True` or trains with the function above. It then
predicts and calls Matplotlib to show a 6-by-2, 12-joint plot.

This helper has no defaults for `log_dir_root`, `log_dir`, or
`actuator_network_path`; only `load_pretrained_model` defaults to `False`. Its
relative path convention, implicit plotting, hard-coded CUDA training, and
lack of overwrite/shape guards are reasons it is reference-only here. Use the
bundled read-only validator/data extractor and the no-plot CPU workflow instead.

For failure symptoms and recovery, read [troubleshooting.md](troubleshooting.md).
