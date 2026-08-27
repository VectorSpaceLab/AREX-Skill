# core-neurons troubleshooting

Use this guide before changing the mathematical model. Most failures come from state tuple counts, hidden-state ownership, device placement, or time/batch/channel shape conventions.

## Fast triage

1. Identify the class and expected state tuple in [API reference](api-reference.md).
2. Decide whether state is manual or internal (`init_hidden=True`). Do not mix both in one call.
3. Check input shape: stepwise cells consume one time step; `StateLeaky`, `LinearLeaky`, `LeakyParallel`, and `AssociativeLeaky` consume time-major sequences.
4. Move modules and manually supplied states to the same device before the first forward call.
5. Reset/detach hidden states between independent batches or truncated-BPTT chunks.

## Symptom-to-fix table

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ValueError: too many values to unpack` or missing return values | Used the wrong state/return tuple count. | `Leaky`/`Lapicque`: `spk, mem`; `Synaptic`/`SLSTM`/`SConv2dLSTM`: `spk, syn, mem`; `Alpha`: `spk, syn_exc, syn_inh, mem`; `RLeaky`: `spk, mem` with previous `spk` as input state; `RSynaptic`: `spk, syn, mem` with previous `spk` as input state. |
| `TypeError` says state should not be passed with `init_hidden=True` | Manual state arguments were supplied to a module that owns its state internally. | Call `lif(input_)` only, or recreate the neuron with `init_hidden=False` and pass states explicitly. |
| `nn.Sequential` breaks because a neuron returns a tuple | Earlier sequential neurons are returning `(spk, state)` into the next layer. | Set intermediate neurons `init_hidden=True`. Set `output=True` only on the final neuron whose state the caller needs. |
| Final membrane is not returned | `init_hidden=True` defaults to returning only spikes. | Add `output=True` on the final stateful neuron. |
| Hidden state leaks from one batch into the next | Internal state was not reset. | Use `snntorch.utils.reset(net)` for supported stateful neurons inside a module tree, or call class/instance reset helpers such as `snn.Leaky.reset_hidden()` or `layer.reset_mem()`. |
| Backprop graph grows across chunks | Hidden states were reused without detaching. | Use `snntorch.utils.reset(net)` when a full reset is desired, or call `detach_hidden()` on the relevant neuron class between truncated-BPTT chunks. |
| Manual state is on CPU while input is on CUDA | State tensors were initialized before moving the module/input, or manually created on the wrong device. | Move the module with `.to(device)` before the first forward, create manual states on the same device, and recreate/reset states after device moves. |
| `LeakyParallel(..., device='cuda')` raises mixed-device errors | In this release, the constructor's hidden-weight mask can be created on CPU while RNN weights are on CUDA. | Construct `LeakyParallel` without `device=...`, then call `.to(device)` on the module before forwarding CUDA inputs. |
| `reset_mechanism` is rejected | Invalid reset string. | Use exactly `"subtract"`, `"zero"`, or `"none"`. Current defaults: subtract for `Leaky`/`Synaptic`/`RLeaky`/`RSynaptic`/`Lapicque`, zero for `Alpha`, none for `SLSTM`/`SConv2dLSTM`. |
| Reset timing is off by one step | `reset_delay` default behavior was assumed incorrectly. | For `Leaky`, `Synaptic`, `RLeaky`, and `RSynaptic`, keep `reset_delay=True` unless you have a reproducer requiring immediate post-spike reset. |
| `mem_reset()` or `fire_inhibition()` raises `NotImplementedError` | Called stepwise-reset APIs on a sequence-convolution neuron. | `StateLeaky` and `LinearLeaky` do not maintain stepwise hidden state; use full-sequence inputs and do not call `mem_reset()`/`fire_inhibition()`. |
| `DeltaLeaky` rejects missing `mem` | `DeltaLeaky(init_hidden=False)` expects a pair state. | Pass `mem=(mem, mem_prev)` as the single state argument, or use `init_hidden=True` and let the first forward initialize `(mem, mem_prev)`. |
| `Alpha` constructor raises `ValueError` | Invalid decay ordering. | Ensure `alpha > beta` and `beta != 1`. |
| `RLeaky`/`RSynaptic` constructor raises wiring errors | Mixed dense/conv recurrent settings or missing feature dimensions. | For `all_to_all=True`, provide only `linear_features` or provide both `conv2d_channels` and `kernel_size`. For `all_to_all=False`, provide none of those and use `V`. |
| `SConv2dLSTM` constructor rejects pooling | Both `max_pool` and `avg_pool` were set. | Choose one pooling mode or neither. Remember pooling changes only the spike output spatial shape. |
| `BatchNormTT*` behaves like a list, not a layer | It returns a `ModuleList`. | Index it per time step: `out_t = bntt[t](x_t)`. Bias is intentionally disabled (`bn.bias is None`). |
| Learnable beta seems missing | The class stores the learnable object under a different name. | For `StateLeaky`/`LinearLeaky`, inspect `tau`; `beta` is derived. For `LeakyParallel`, inspect `rnn.weight_hh_l0`; `beta` only seeds recurrent weights. |
| Learnable threshold has no gradient | Loss did not depend on the spike/membrane path, or `learn_threshold=False`. | Verify `threshold` appears in `named_parameters()` and run a tiny synthetic backward pass. |
| `AssociativeLeaky.from_num_spiking_neurons` raises `ValueError` | `num_spiking_neurons` is not a positive perfect square. | Use a square such as `16` or `64`, or call the explicit constructor with matching `d_value * d_key`. |

## Shape conventions by family

- Stepwise dense neurons: pass one time step, usually shaped `(B, features)`, and keep each state tensor the same shape.
- Stepwise convolutional neurons: pass one time step, usually `(B, C, H, W)`; `SConv2dLSTM` states use `(B, out_channels, H, W)`.
- Time-major sequence layers: `StateLeaky`, `LinearLeaky`, `LeakyParallel`, and `AssociativeLeaky` use `(T, B, C_or_features)`.
- `LinearLeaky` changes the feature dimension from `in_features` to `out_features`.
- `LeakyParallel` changes the last dimension from `input_size` to `hidden_size` and returns spikes only.
- `AssociativeLeaky` returns a single tensor; do not unpack it as `(spk, mem)`.

## Device placement checklist

- Prefer `module = module.to(device)` before creating or forwarding manual states.
- For manual states, use `torch.zeros_like(input_)` or `.to(input_.device)` rather than default CPU tensors.
- After moving a model to a new device, reset hidden states before reusing it.
- For `LeakyParallel` on CUDA, avoid constructor `device='cuda'`; construct first, then call `.to('cuda')`.

## Reset and detach checklist

- Independent batch or evaluation sample: reset hidden state.
- Truncated backpropagation chunk: detach hidden state, and reset only when the sequence boundary is real.
- `init_hidden=True` inside a module tree: `snntorch.utils.reset(net)` is the safest first reset/detach choice for supported stateful neurons.
- Manual state tuple: carry and detach the tuple yourself; class-level helpers only know about internally tracked instances.
