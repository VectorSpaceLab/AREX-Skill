# Workflows

Use this page for the shortest path from raw tensors to encoded spikes, training, and inspection.

## 1) Turn raw tensors into spike codes

### Static input

Use `spikegen.rate` when the input is batch-first and you want a probabilistic rate code.

```python
from snntorch import spikegen
import torch

x = torch.tensor([[0.0, 0.25, 0.5, 1.0],
                  [1.0, 0.0, 0.75, 0.125]])
rate = spikegen.rate(x, num_steps=6, gain=0.5)
```

Use `spikegen.latency` when you want early spikes for large features.

```python
latency = spikegen.latency(x, num_steps=6, normalize=True, linear=True)
```

Use `spikegen.delta` when the signal itself is a sequence and spikes should mark changes between steps.

```python
seq = torch.tensor([1.0, 2.0, 0.0, 2.0, 2.9])
delta = spikegen.delta(seq, threshold=1.0, padding=True, off_spike=True)
```

### Time-varying input

If the tensor already has time as its first axis, set `time_var_input=True` and do not also pass `num_steps`.

```python
tv = torch.stack([x, x * 0.5], dim=0)  # [T, B, ...]
rate_tv = spikegen.rate(tv, time_var_input=True)
```

### Label targets

For class labels, use `spikegen.targets_convert` or the specialized `targets_rate` / `targets_latency` helpers.

- Spike-count classification: `spikegen.targets_convert(labels, num_classes=C, code='rate')`
- Latency targets: `spikegen.targets_convert(labels, num_classes=C, code='latency', num_steps=T, normalize=True, linear=True, bypass=True)`
- One-hot helpers: `to_one_hot`, `to_one_hot_inverse`, and `from_one_hot`

Rule of thumb:

- If you want a simple one-hot label tensor, keep the default rate settings.
- If you want time variation, make `first_spike_time`, `correct_rate`, or `incorrect_rate` non-default.
- If you use population coding later, keep the target class count aligned with the output layer size.

## 2) Pick a surrogate gradient

`surrogate.fast_sigmoid()` is the usual first choice when you want a smooth approximate gradient.

```python
from snntorch import surrogate
spike_grad = surrogate.fast_sigmoid(slope=25)
```

Pass the closure to the neuron layer:

```python
import snntorch as snn
lif = snn.Leaky(beta=0.5, spike_grad=spike_grad, init_hidden=True)
```

If you need a custom derivative, wrap it with `surrogate.custom_surrogate(fn)`.

## 3) Choose the loss and metric pairing

Decision guide:

- Count classification -> `SF.mse_count_loss()` or `SF.ce_count_loss()`
- Membrane training -> `SF.mse_membrane_loss()` or `SF.ce_max_membrane_loss()`
- Spike timing -> `SF.mse_temporal_loss()` or `SF.ce_temporal_loss()`
- Accuracy -> `SF.accuracy_rate()` or `SF.accuracy_temporal()`
- Sparsity regularization -> `SF.l1_rate_sparsity()`

Population code rule:

- Set `population_code=True` and `num_classes=C` when the output layer is grouped by class.
- Ensure `num_outputs` is divisible by `num_classes`.

For `mse_count_loss`, remember that the target spike count is tied to the chunk length. When you use TBPTT, compute count targets for the truncated chunk, not the full sequence.

## 4) Write a manual training loop when you need maximum control

Manual loops are the clearest route when you want explicit hidden-state control or unsupported regularization.

```python
import torch
import snntorch as snn
import snntorch.functional as SF
from snntorch import surrogate, utils

spike_grad = surrogate.fast_sigmoid(slope=25)
net = torch.nn.Sequential(
    torch.nn.Linear(4, 2, bias=False),
    snn.Leaky(beta=0.5, spike_grad=spike_grad, init_hidden=True, output=True),
)

loss_fn = SF.mse_count_loss(correct_rate=1.0, incorrect_rate=0.0)
optimizer = torch.optim.SGD(net.parameters(), lr=0.2)

for xb, yb in loader:
    utils.reset(net)
    spk_rec = []
    for _ in range(num_steps):
        spk, mem = net(xb)
        spk_rec.append(spk)
    spk_rec = torch.stack(spk_rec)
    loss = loss_fn(spk_rec, yb)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
```

Why this route:

- It avoids the legacy wrapper naming rules.
- It makes time-first/time-invariant handling obvious.
- It keeps custom regularization and inspection simple.

## 5) Use the legacy backprop wrappers only when you need them

`backprop.BPTT`, `backprop.TBPTT`, and `backprop.RTRL` can run a full epoch-style step with one call.

Wrapper checklist:

- Spiking layers should use `init_hidden=True`.
- Time-varying data: `time_var=True` and no explicit `num_steps`.
- Static data: `time_var=False` and pass `num_steps`.
- Inputs laid out as `[B, T, ...]`: set `time_first=False`.
- Use snnTorch functional losses and `SF.l1_rate_sparsity()` with the wrapper names.
- The wrappers call `utils.reset(net)` internally.

Example:

```python
loss = backprop.BPTT(
    net,
    loader,
    optimizer=optimizer,
    criterion=loss_fn,
    num_steps=1,
    time_var=False,
    device='cpu',
)
```

## 6) Inspect outputs and gradients with monitors

Attach monitors from `snntorch.functional.probe` to capture forward data and gradients.

```python
from snntorch.functional import probe

out_mon = probe.OutputMonitor(net, instance=snn.Leaky)
grad_mon = probe.GradOutputMonitor(net, instance=snn.Leaky)
```

After a forward/backward pass:

- `out_mon.records` contains layer outputs.
- `grad_mon.records` contains backward gradients.
- `out_mon['lif1']` returns all records for the `lif1` layer.
- Call `clear_recorded_data()` between runs and `remove_hooks()` when finished.

To probe a membrane variable, use `AttributeMonitor('mem', pre_forward=False, net, instance=snn.Leaky)`.

## 7) Split or subset torchvision-style datasets

Use the dataset helpers before constructing `DataLoader`s.

- `utils.data_subset(dataset, subset, idx=0)` keeps one chunk out of `subset` chunks.
- `utils.valid_split(ds_train, ds_val, split, seed=0)` makes paired train/validation sets.

Important:

- Both helpers mutate `.data` and `.targets` in place.
- They are meant for dataset objects that actually expose those attributes.

## 8) Quantize hidden state values

Create the quantizer and pass it to a neuron constructor:

```python
from snntorch.functional import quant

q = quant.state_quant(num_bits=4, uniform=True, threshold=1.0)
lif = snn.Leaky(beta=0.5, threshold=1.0, state_quant=q)
```

When to choose what:

- `uniform=True` for evenly spaced levels.
- `uniform=False` for a non-uniform level distribution.
- `thr_centered=True` when you want levels concentrated around the threshold.

## 9) Use STDP for local learning or inspection

`STDPLearner` is the route when you want local spike-timing updates around a linear or convolutional synapse.

The easiest pattern is:

1. Forward through the synapse and a spike-only wrapper around the neuron.
2. Call `learner.step(on_grad=True)` to write the local update into `weight.grad`.
3. Step an optimizer, or call `learner.step(on_grad=False)` if you only want the raw delta.

Example shape pattern:

```python
import torch.nn as nn
import snntorch as snn
from snntorch.functional.stdp_learner import STDPLearner

class SpikeOnly(nn.Module):
    def __init__(self, neuron):
        super().__init__()
        self.neuron = neuron

    def forward(self, x):
        spk, _ = self.neuron(x)
        return spk

syn = nn.Linear(2, 2, bias=False)
sn = SpikeOnly(snn.Leaky(beta=0.9))
learner = STDPLearner(syn, sn, tau_pre=2.0, tau_post=3.0)
```

Notes:

- `step()` consumes the recorded spikes it reads.
- If the wrapped neuron returns `(spk, mem)`, expose only the spike tensor to the learner.
- Recreate the learner when you need a fresh STDP episode; do not rely on `STDPLearner.reset()` in this release.

## 10) Run the bundled smoke checks

- `scripts/spike_encoding_smoke.py` -> rate, latency, delta, and target coding
- `scripts/synthetic_bptt_smoke.py` -> one-step BPTT with `fast_sigmoid`, `mse_count_loss`, and monitors
- `scripts/shape_mismatch_diagnostic.py` -> deliberate spike/target mismatch and fix
- `scripts/stdp_smoke.py` -> local STDP update on a synthetic linear synapse
