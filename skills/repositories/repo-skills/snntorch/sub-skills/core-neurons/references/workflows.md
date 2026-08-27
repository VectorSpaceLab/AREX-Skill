# core-neurons workflows

All examples here use synthetic tensors. They explain neuron and layer wiring only; route encoding choices, surrogate-gradient comparisons, losses, metrics, and full training recipes to the sibling training sub-skill.

## 1. Choose the state strategy first

| Strategy | Use when | Typical classes |
| --- | --- | --- |
| Manual state tuple | You want explicit time-loop control or non-sequential module logic. | `Leaky`, `Synaptic`, `RLeaky`, `RSynaptic`, `Lapicque`, `Alpha`, `SLSTM`, `SConv2dLSTM`, `DeltaLeaky` |
| `init_hidden=True` | You want a neuron to store its state internally, usually inside `nn.Sequential`. | Same stateful classes except `DeltaLeaky` needs extra care because its state is `(mem, mem_prev)`. |
| Stateless time-major operator | You already have a full sequence `(T, B, C)` and do not need stepwise recurrence. | `StateLeaky`, `LinearLeaky`, `AssociativeLeaky` |
| Time-parallel RNN-backed LIF | You want a fast `Leaky`-like sequence layer that returns spikes only. | `LeakyParallel` |
| Per-time helper layers | You need a layer list indexed by time step or a learnable spike magnitude. | `BatchNormTT1d`, `BatchNormTT2d`, `GradedSpikes` |

## 2. Manual explicit-state loop

Use this pattern when a custom module needs full access to each state tensor.

```python
import torch
import torch.nn as nn
import snntorch as snn

class Net(nn.Module):
    def __init__(self, in_features, hidden, out_features, steps):
        super().__init__()
        self.steps = steps
        self.fc1 = nn.Linear(in_features, hidden)
        self.lif1 = snn.Leaky(beta=0.8)
        self.fc2 = nn.Linear(hidden, out_features)
        self.lif2 = snn.Synaptic(alpha=0.7, beta=0.8)

    def forward(self, x):
        mem1 = self.lif1.reset_mem()
        syn2, mem2 = self.lif2.reset_mem()
        spk_rec, mem_rec = [], []
        for _ in range(self.steps):
            spk1, mem1 = self.lif1(self.fc1(x), mem1)
            spk2, syn2, mem2 = self.lif2(self.fc2(spk1), syn2, mem2)
            spk_rec.append(spk2)
            mem_rec.append(mem2)
        return torch.stack(spk_rec), torch.stack(mem_rec)
```

Key checks:

- Initialize the same number of state tensors that `forward` expects.
- Keep manually supplied state tensors on the same device and with the same batch/feature shape as the current input.
- Prefer `reset_mem()` over the deprecated `init_*` aliases in new code.

## 3. Hidden state with `nn.Sequential`

Use `init_hidden=True` when a neuron sits inside `nn.Sequential` and should pass only spikes to the next layer. Use `output=True` on the final neuron when the caller also needs membrane or synaptic state.

```python
import torch.nn as nn
import snntorch as snn
from snntorch import utils

net = nn.Sequential(
    nn.Linear(8, 16),
    snn.Leaky(beta=0.8, init_hidden=True),
    nn.Linear(16, 4),
    snn.Leaky(beta=0.8, init_hidden=True, output=True),
)

def forward_steps(x, steps):
    utils.reset(net)  # reset and detach hidden states for supported stateful neurons
    spk_rec, mem_rec = [], []
    for _ in range(steps):
        spk, mem = net(x)
        spk_rec.append(spk)
        mem_rec.append(mem)
    return torch.stack(spk_rec), torch.stack(mem_rec)
```

Do not pass `mem`, `syn`, or previous `spk` arguments to a neuron created with `init_hidden=True`; the state is now owned by the module instance.

## 4. Recurrent neurons

Use `RLeaky` or `RSynaptic` when output spikes should feed back into the state update.

- Dense recurrent feature vector: `snn.RLeaky(beta=0.8, linear_features=hidden)`.
- Convolutional recurrent map: `snn.RLeaky(beta=0.8, conv2d_channels=channels, kernel_size=3)`.
- One-to-one recurrent scaling: `snn.RLeaky(beta=0.8, all_to_all=False, V=0.5)`.

The same wiring rules apply to `RSynaptic`, with an added `alpha` synaptic decay. Keep previous output spikes in the state tuple: `spk, mem` for `RLeaky`; `spk, syn, mem` for `RSynaptic`.

## 5. StateLeaky and LinearLeaky over full sequences

Use these when the input is already time-major `(T, B, C)` and a causal exponential kernel over the whole sequence is acceptable.

```python
import torch
import snntorch as snn

x = torch.randn(12, 3, 5)       # T, B, input channels
layer = snn.LinearLeaky(beta=0.9, in_features=5, out_features=7, output=True)
spk, mem = layer(x)             # both are (12, 3, 7)
state = snn.StateLeaky(beta=0.8, channels=7, output=False)
mem_only = state(spk)           # (12, 3, 7)
```

`kernel_truncation_steps=K` keeps only the most recent `K` exponential-filter taps. With `learn_beta=True`, inspect `module.tau`, not `module.beta`, for the learnable parameter.

## 6. LeakyParallel safe use

`LeakyParallel` processes all time steps at once and returns spikes only. It is useful for sequence-level smoke checks and acceleration experiments, but it is not a drop-in replacement for stepwise `Leaky` when code expects a membrane state.

```python
import torch
import snntorch as snn

x = torch.rand(10, 4, 8)  # T, B, input_size
lif = snn.LeakyParallel(input_size=8, hidden_size=16, beta=0.9, learn_beta=True)
spk = lif(x)             # (10, 4, 16)
```

Bundled helpers:

```bash
python scripts/leakyparallel_forward_smoke.py
python scripts/leakyparallel_train_smoke.py
```

These helpers adapt the repository's example training pattern into synthetic-data checks and deliberately avoid downloads or external simulator tooling.

## 7. Spiking LSTM cells

`SLSTM` and `SConv2dLSTM` simulate one time step per call. Use explicit loops or `init_hidden=True`.

- `SLSTM(input_size, hidden_size)` expects `input_` shaped `(B, input_size)` and states `syn, mem` shaped `(B, hidden_size)`.
- `SConv2dLSTM(in_channels, out_channels, kernel_size)` expects `input_` shaped `(B, in_channels, H, W)` and states shaped `(B, out_channels, H, W)`.
- `SConv2dLSTM(max_pool=K)` or `avg_pool=K` pools the spike output only; `syn` and `mem` remain in the unpooled state shape.

Bundled helper:

```bash
python scripts/spiking_lstm_smoke.py
```

## 8. AssociativeLeaky workflow

Use `AssociativeLeaky` for the SSM-style associative-memory spiking model with time-major inputs.

```python
import torch
import snntorch as snn

x = torch.randn(6, 2, 16)
model = snn.AssociativeLeaky.from_num_spiking_neurons(
    in_dim=16, num_spiking_neurons=16, use_q_projection=True
)
y = model(x)  # (6, 2, 16)
```

Use the explicit constructor when `d_value` and `d_key` should differ. The convenience constructor requires a positive perfect square and sets both dimensions to the square root.

Bundled helper:

```bash
python scripts/associative_leaky_smoke.py
```

## 9. BatchNormTT and GradedSpikes

`BatchNormTT1d` and `BatchNormTT2d` return a `ModuleList`, not a single layer. Index by time step:

```python
bntt = snn.BatchNormTT1d(input_features=8, time_steps=T)
y = torch.stack([bntt[t](x[t]) for t in range(T)])
```

Use `GradedSpikes(size, constant_factor)` when a spike vector should be multiplied by learnable per-neuron weights. If `constant_factor` is `None`, weights initialize from a uniform range; otherwise they initialize to `constant_factor`.

## 10. Difficult synthetic usability cases

- Mixed state reset: `scripts/mixed_state_chain_smoke.py` combines `Leaky`, `LinearLeaky`, and `StateLeaky`, resets the `Leaky` hidden state between identical batches, and asserts expected hidden-state and sequence shapes.
- Associative chunking: `scripts/associative_leaky_smoke.py` checks `AssociativeLeaky.from_num_spiking_neurons` with `use_q_projection` both true and false, comparing full-batch and chunked-batch outputs and gradients.
