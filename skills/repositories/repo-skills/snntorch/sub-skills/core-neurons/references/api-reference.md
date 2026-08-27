# core-neurons API reference

This reference distills the snnTorch 1.0.0 neuron and layer APIs relevant to core-neuron workflows. Import most public classes with `import snntorch as snn`; lower-level module imports are only needed when you intentionally want implementation modules.

## Live constructor signatures

```python
snn.Leaky(beta, threshold=1.0, spike_grad=None, surrogate_disable=False, init_hidden=False, inhibition=False, learn_beta=False, learn_threshold=False, reset_mechanism='subtract', state_quant=False, output=False, graded_spikes_factor=1.0, learn_graded_spikes_factor=False, reset_delay=True)
snn.Synaptic(alpha, beta, threshold=1.0, spike_grad=None, surrogate_disable=False, init_hidden=False, inhibition=False, learn_alpha=False, learn_beta=False, learn_threshold=False, reset_mechanism='subtract', state_quant=False, output=False, reset_delay=True)
snn.RLeaky(beta, V=1.0, all_to_all=True, linear_features=None, conv2d_channels=None, kernel_size=None, threshold=1.0, spike_grad=None, surrogate_disable=False, init_hidden=False, inhibition=False, learn_beta=False, learn_threshold=False, learn_recurrent=True, reset_mechanism='subtract', state_quant=False, output=False, reset_delay=True)
snn.RSynaptic(alpha, beta, V=1.0, all_to_all=True, linear_features=None, conv2d_channels=None, kernel_size=None, threshold=1.0, spike_grad=None, surrogate_disable=False, init_hidden=False, inhibition=False, learn_alpha=False, learn_beta=False, learn_threshold=False, learn_recurrent=True, reset_mechanism='subtract', state_quant=False, output=False, reset_delay=True)
snn.Lapicque(beta=False, R=False, C=False, time_step=1, threshold=1.0, spike_grad=None, surrogate_disable=False, init_hidden=False, inhibition=False, learn_beta=False, learn_threshold=False, reset_mechanism='subtract', state_quant=False, output=False)
snn.Alpha(alpha, beta, threshold=1.0, spike_grad=None, surrogate_disable=False, init_hidden=False, inhibition=False, learn_alpha=False, learn_beta=False, learn_threshold=False, reset_mechanism='zero', state_quant=False, output=False)
snn.DeltaLeaky(delta_threshold=1.0, *args, **kwargs)  # remaining args pass through to Leaky
snn.LinearLeaky(beta, in_features, out_features, bias=True, device=None, dtype=None, threshold=1.0, spike_grad=None, surrogate_disable=False, learn_beta=False, learn_threshold=False, state_quant=False, output=True, graded_spikes_factor=1.0, learn_graded_spikes_factor=False, kernel_truncation_steps=None)
snn.StateLeaky(beta, channels, threshold=1.0, spike_grad=None, surrogate_disable=False, learn_beta=False, learn_threshold=False, state_quant=False, output=True, graded_spikes_factor=1.0, learn_graded_spikes_factor=False, kernel_truncation_steps=None)
snn.LeakyParallel(input_size, hidden_size, beta=None, bias=True, threshold=1.0, dropout=0.0, spike_grad=None, surrogate_disable=False, learn_beta=False, learn_threshold=False, graded_spikes_factor=1.0, learn_graded_spikes_factor=False, weight_hh_enable=False, device=None, dtype=None)
snn.SConv2dLSTM(in_channels, out_channels, kernel_size, bias=True, max_pool=0, avg_pool=0, threshold=1.0, spike_grad=None, surrogate_disable=False, init_hidden=False, inhibition=False, learn_threshold=False, reset_mechanism='none', state_quant=False, output=False)
snn.SLSTM(input_size, hidden_size, bias=True, threshold=1.0, spike_grad=None, surrogate_disable=False, init_hidden=False, inhibition=False, learn_threshold=False, reset_mechanism='none', state_quant=False, output=False)
snn.AssociativeLeaky(in_dim, d_value, d_key, num_spiking_neurons, use_q_projection=True)
snn.AssociativeLeaky.from_num_spiking_neurons(in_dim, num_spiking_neurons, use_q_projection=True)
snn.BatchNormTT1d(input_features, time_steps, eps=1e-5, momentum=0.1, affine=True)
snn.BatchNormTT2d(input_features, time_steps, eps=1e-5, momentum=0.1, affine=True)
snn.GradedSpikes(size, constant_factor)
```

## Stateful neuron return contracts

For these classes, `reset_mem()` is the current reset/initialization method. The `init_*` helpers still exist but are deprecated aliases to `reset_mem()` unless noted.

| Class | Forward state arguments | Normal return when `init_hidden=False` | Return when `init_hidden=True` and `output=False` | State helper |
| --- | --- | --- | --- | --- |
| `Leaky` | `mem` | `spk, mem` | `spk` | `reset_mem()` / `init_leaky()` returns `mem` |
| `Synaptic` | `syn, mem` | `spk, syn, mem` | `spk` | `reset_mem()` / `init_synaptic()` returns `syn, mem` |
| `RLeaky` | previous `spk, mem` | `spk, mem` | `spk` | `reset_mem()` / `init_rleaky()` returns `spk, mem` |
| `RSynaptic` | previous `spk, syn, mem` | `spk, syn, mem` | `spk` | `reset_mem()` / `init_rsynaptic()` returns `spk, syn, mem` |
| `Lapicque` | `mem` | `spk, mem` | `spk` | `reset_mem()` / `init_lapicque()` returns `mem` |
| `Alpha` | `syn_exc, syn_inh, mem` | `spk, syn_exc, syn_inh, mem` | `spk` | `reset_mem()` / `init_alpha()` returns `syn_exc, syn_inh, mem` |
| `SConv2dLSTM` | `syn, mem` | `spk, syn, mem` | `spk` | `reset_mem()` / `init_sconv2dlstm()` returns `syn, mem` |
| `SLSTM` | `syn, mem` | `spk, syn, mem` | `spk` | `reset_mem()` / `init_slstm()` returns `syn, mem` |
| `DeltaLeaky` | one `mem` argument containing `(mem, mem_prev)` | `spk, (mem, mem_prev)` | `spk, (mem, mem_prev)` | `reset_mem()` returns `(None, None)`; inherited `init_leaky()` delegates to it |

When `output=True`, the stateful classes above return the spike plus their state tensors even with `init_hidden=True`; this is the usual way to make the final neuron in `nn.Sequential` expose membrane state while earlier hidden neurons pass only spikes.

## Time-major and helper-layer contracts

| Class/helper | Input shape | Return | Notes |
| --- | --- | --- | --- |
| `StateLeaky` | `(T, B, C)` | `spk, mem` if `output=True`; else `mem` | Uses a causal exponential depthwise convolution over time, not stepwise recurrent state. `mem_reset()` and `fire_inhibition()` are intentionally unsupported. |
| `LinearLeaky` | `(T, B, in_features)` | `spk, mem` if `output=True`; else `mem`, with channel dimension `out_features` | Applies an internal `nn.Linear` at each time step and then `StateLeaky(channels=out_features)`. |
| `LeakyParallel` | `(L, H_in)` or `(L, N, H_in)` | `spk` only, shape ending in `hidden_size` | Wraps a one-layer `nn.RNN(non_linearity='relu')`; no explicit hidden-state return, no `init_hidden`, no explicit reset mechanism. |
| `AssociativeLeaky` | `(T, B, in_dim)` | one tensor, normally `(T, B, num_spiking_neurons)` | Uses projections `to_v`, `to_k`, `to_alpha`, and optional `to_q`; it does not return `(spk, mem)`. |
| `BatchNormTT1d` | per-step input accepted by `nn.BatchNorm1d` | `nn.ModuleList` length `time_steps` | Index by time step: `bntt[t](x_t)`. Bias is disabled (`bn.bias is None`). |
| `BatchNormTT2d` | per-step input accepted by `nn.BatchNorm2d` | `nn.ModuleList` length `time_steps` | Same pattern as `BatchNormTT1d`, but for 2D feature maps. |
| `GradedSpikes` | spike tensor broadcastable with weights `(size, 1)` | scaled tensor of same broadcasted shape | Multiplies spikes by learnable weights initialized from `constant_factor` or uniform `U(0.5, 1.5)`. |

## Reset mechanisms

Valid `reset_mechanism` strings are `"subtract"`, `"zero"`, and `"none"`. The current implementation stores them in `reset_mechanism_val` as `0`, `1`, and `2`, and the property setter updates that buffer when changed after construction.

| Default reset | Classes |
| --- | --- |
| `"subtract"` | `Leaky`, `Synaptic`, `RLeaky`, `RSynaptic`, `Lapicque` |
| `"zero"` | `Alpha` |
| `"none"` | `SConv2dLSTM`, `SLSTM` |
| no stepwise reset | `DeltaLeaky`, `StateLeaky`, `LinearLeaky`, `LeakyParallel`, `AssociativeLeaky`, BNTT helpers, `GradedSpikes` |

`reset_delay=True` is available on `Leaky`, `Synaptic`, `RLeaky`, and `RSynaptic`; it keeps the default delayed reset timing. Only change it when you intentionally need immediate post-spike reset behavior and have a tiny reproducer.

## Learnable parameters and buffers

- `threshold` becomes an `nn.Parameter` when `learn_threshold=True`; otherwise it is a registered buffer.
- `graded_spikes_factor` becomes an `nn.Parameter` when `learn_graded_spikes_factor=True`; otherwise it is a registered buffer.
- `Leaky`, `Synaptic`, `RLeaky`, `RSynaptic`, and `Alpha` store `beta`/`alpha` directly as buffers or parameters according to their `learn_*` flags.
- `StateLeaky` and `LinearLeaky` represent `beta` through `tau = 1 / (1 - beta + 1e-12)`. With `learn_beta=True`, inspect `module.tau` for the learnable parameter; `module.beta` is a derived property.
- `LeakyParallel` copies/clamps `beta` into the RNN hidden-hidden weights at initialization. With `learn_beta=True`, the trainable object is `module.rnn.weight_hh_l0`, not a separate `beta` parameter.
- `RLeaky` and `RSynaptic` use `learn_recurrent=True` by default. With `all_to_all=True`, `module.recurrent` is an `nn.Linear` or `nn.Conv2d`; with `all_to_all=False`, one-to-one recurrent scaling uses `V`.

## Recurrent wiring choices

For `RLeaky` and `RSynaptic`:

- `all_to_all=True` requires exactly one wiring family:
  - dense 1D: provide `linear_features` matching the spike feature dimension; or
  - convolutional: provide both `conv2d_channels` and `kernel_size`.
- Do not provide `linear_features` together with `conv2d_channels`/`kernel_size`.
- `all_to_all=False` forbids `linear_features`, `conv2d_channels`, and `kernel_size`; pass `V` for elementwise or shared recurrent scaling.

## Special class notes

- `Lapicque` accepts either `beta` or enough RC-circuit parameters (`R`, `C`, `time_step`) to infer the missing physical quantity. Use `Leaky` when the main goal is a simple learnable first-order decay.
- `Alpha` requires `alpha > beta` and `beta != 1`.
- `DeltaLeaky` spikes on absolute membrane-change magnitude exceeding `delta_threshold` and does not perform the standard hard membrane reset.
- `SConv2dLSTM` forbids setting both `max_pool` and `avg_pool`; pooling changes the spike output shape but leaves `syn`/`mem` in the unpooled state shape.
- `AssociativeLeaky.from_num_spiking_neurons` requires a positive perfect square and sets `d_value = d_key = sqrt(num_spiking_neurons)`.
