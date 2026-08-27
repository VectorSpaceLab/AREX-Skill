# Core API Reference

This reference distills the stable, core `spikingjelly.activation_based` APIs that matter for building and debugging activation-based SNNs.

## Canonical tensor and state conventions

- Single-step tensors use `shape = [N, *]`.
- Multi-step tensors use `shape = [T, N, *]`.
- `step_mode='s'` means single-step behavior; `step_mode='m'` means time-major multi-step behavior.
- Stateful modules store their state inside the module and must be reset between batches.
- Prefer stable top-level imports such as `from spikingjelly.activation_based import neuron, layer, functional, surrogate, base, monitor, rnn`.

## 1) `base`: step modes, memory, and functional conversion

### Core interfaces

| API | Purpose | Notes |
| --- | --- | --- |
| `StepModule()` | Base interface for `step_mode`-aware modules | `supported_step_mode()` defaults to `('s', 'm')` |
| `SingleStepModule()` | Single-step-only interface | Supports `('s',)` |
| `MultiStepModule()` | Multi-step-only interface | Supports `('m',)` |
| `MemoryModule()` | Stateful `nn.Module` base class | Registers memories, resets, detaches, and exposes explicit functional helpers |

### Memory helpers

- `register_memory(name, value)` registers a state variable and its reset value.
- `reset()` restores registered memories.
- `detach()` detaches all tensor memories from the graph.
- `memories()`, `named_memories()`, `extract_memories()`, and `load_memories()` provide state traversal.
- `to_functional_forward(module, fn=None)` returns a callable with signature `(inputs, states, **kwargs) -> (outputs, updated_states)`.
- `materialize_states(inputs, states, step_mode)` lets a stateful module turn scalar or placeholder state into a shape/device-compatible tensor.

### Live-signature reminders

- `BaseNode` and `MemoryModule` are the core explicit-state contract for production neurons.
- `SimpleBaseNode` is the readable charge/fire/reset contract for teaching and custom dynamics.

## 2) `functional`: net-wide configuration and forward helpers

### Network configuration

| API | Signature shape | Purpose |
| --- | --- | --- |
| `reset_net(net)` | `reset_net(net: nn.Module)` | Reset every resettable submodule in a network |
| `collect_reset_modules(net)` | `-> tuple[nn.Module, ...]` | Collect callable `reset()` modules |
| `reset_collected_modules(modules)` | `-> None` | Reset a cached module tuple |
| `invalidate_reset_cache(net)` | `-> None` | Drop the cached reset-module list after model surgery or `torch.compile` |
| `set_step_mode(net, step_mode)` | `step_mode: 's' | 'm'` | Broadcast step mode through a network |
| `set_backend(net, backend, instance=None)` | `backend: str` | Broadcast backend selection to supported modules |
| `detach_net(net)` | `-> None` | Detach all stateful modules in a network |

### Forward helpers

| API | Shape contract | When to use |
| --- | --- | --- |
| `multi_step_forward(x_seq, single_step_module)` | `[T, N, *] -> [T, N, *]` | Python-loop multi-step execution for single-step modules |
| `t_last_multi_step_forward(x_seq, single_step_module)` | `[..., T] -> [..., T]` | Time-last variant of multi-step execution |
| `chunk_multi_step_forward(split_size, x_seq, multi_step_module)` | `[T, *] -> [T, *]` | Memory-friendly inference for large `T` |
| `seq_to_ann_forward(x_seq, stateless_module)` | `[T, N, *] -> [T, N, *]` | Flatten time and batch for stateless layers |
| `t_last_seq_to_ann_forward(x_seq, stateless_module)` | `[..., T] -> [..., T]` | Time-last variant for stateless layers |

### Selected explicit state helpers

| API | State contract | Purpose |
| --- | --- | --- |
| `delay_step(x, queue, delay_steps)` | delay queue | One step of `Delay` |
| `synapse_filter_step(x, out_i, reciprocal_tau)` | output current | One step of `SynapseFilter` |
| `neunorm_step(in_spikes, state, weight, momentum, input_scale)` | normalization state | One step of `NeuNorm` |
| `voltage_reset(v, spike, v_threshold, v_reset, detach_reset)` | voltage tensor | Hard/soft reset helper |
| `if_step`, `lif_step`, `plif_step`, `qif_step`, `eif_step`, `izhikevich_step`, `activation_aware_if_step` | explicit neuron state | Core functional neuron transitions |

### Miscellaneous helpers kept in scope

- `redundant_one_hot(labels, num_classes, n)`
- `first_spike_index(spikes)`
- `kaiming_normal_conv_linear_weight(net)`
- `delay(x_seq, delay_steps)`
- `set_threshold_margin(output_layer, label_one_hot, ...)`

`functional.learning` and `functional.online_learning` exist, but training workflows are intentionally not the main focus of this sub-skill.

## 3) Surrogate gradients

### Module vs functional style

- Module style: `surrogate.Sigmoid(alpha=4.0)`, `surrogate.ATan(alpha=2.0)`, etc.
- Functional style: `surrogate.sigmoid.apply(x, alpha)`, `surrogate.atan.apply(x, alpha)`, etc.
- `spiking=True` uses Heaviside forward and surrogate gradients in backward.
- `spiking=False` uses the primitive function directly.

### Representative classes and signatures

| Class | Live signature summary |
| --- | --- |
| `Sigmoid` | `alpha=4.0, spiking=True` |
| `ATan` | `alpha=2.0, spiking=True` |
| `SoftSign` | `alpha=2.0, spiking=True` |
| `PiecewiseQuadratic` | `alpha=1.0, spiking=True` |
| `PiecewiseExp` | `alpha=1.0, spiking=True` |
| `NonzeroSignLogAbs` | `alpha=1.0, spiking=True` |
| `SuperSpike` | `alpha=1.0, spiking=True` |
| `Erf` | `alpha=2.0, spiking=True` |
| `LeakyKReLU` | `leak, k, spiking=True` |
| `QPseudoSpike` | `alpha=2.0, spiking=True` |
| `S2NN` | `alpha=4.0, beta=1.0, spiking=True` |
| `Rect` | `alpha=1.0, spiking=True` |
| `PoissonPass`, `DeterministicPass` | pass-through style modules |
| `FakeNumericalGradient` | `alpha=0.3` |
| `MultiLevelSpikeCount` | `max_spike_count, spiking=True, grad_window=None` |
| `SquarewaveFourierSeries` | `n=2, T_period=8, spiking=True` |

### Surrogate helpers

- `check_manual_grad(...)` compares a primitive function and a surrogate function.
- `check_cuda_grad(...)` compares PyTorch and CuPy gradient behavior.
- `plot_surrogate_function(...)` draws primitive and gradient curves.

## 4) Neuron objects

### Core object-model split

| Base class | Role |
| --- | --- |
| `SimpleBaseNode` | Pure-PyTorch charge/fire/reset teaching interface |
| `BaseNode` | Production explicit-state neuron base |
| `NonSpikingBaseNode` | Stateful neuron that returns membrane traces / decoded outputs instead of spikes |

### Common `BaseNode` / `SimpleBaseNode` rules

- `v_threshold`, `v_reset`, `surrogate_function`, `detach_reset`, and `step_mode` are the core behavioral knobs.
- `BaseNode` also adds explicit `backend` and `store_v_seq`.
- `reset()` clears membrane state; `store_v_seq=True` keeps a time-major voltage trace in `v_seq` during multi-step execution.
- `SimpleBaseNode` is the right choice when you want to override `neuronal_charge()` only.
- `BaseNode` is the right choice when you want explicit functional state transitions and backend-aware execution.

### Representative core neurons

| Class | Live signature summary | Notes |
| --- | --- | --- |
| `SimpleIFNode` | `v_threshold=1.0, v_reset=0.0, surrogate_function=Sigmoid(), detach_reset=False, step_mode='s'` | Readable IF interface |
| `IFNode` | same + `backend='torch', store_v_seq=False` | Core IF neuron |
| `SimpleLIFNode` | `tau, decay_input, v_threshold, v_reset, surrogate_function, detach_reset, step_mode` | Readable LIF interface |
| `LIFNode` | same + `backend='torch', store_v_seq=False` | Core LIF neuron |
| `ParametricLIFNode` | `init_tau=2.0, decay_input=True, ...` | Learnable time constant |
| `ActivationAwareIFNode` | `v_threshold, v_offset, channel_dim, v_reset, ...` | Channel-aware threshold/offset |
| `NonSpikingIFNode`, `NonSpikingLIFNode` | `decode`-style non-spiking outputs | Stateful, but not spike-emitting |
| `HalfThresholdIFNode` | IF variant with half-threshold behavior | Useful for specialized dynamics |
| `QIFNode`, `EIFNode`, `IzhikevichNode` | non-linear/adaptive families | Same state/reset contract |
| `LIAFNode`, `GatedLIFNode`, `KLIFNode`, `CUBALIFNode` | LIF variants | Same activation-based module model |
| `MPBNLIFNode`, `DSRIFNode`, `DSRLIFNode` | specialized research variants | Same `MemoryModule` / reset rules |
| `OTTTLIFNode`, `SLTTLIFNode`, `FewSpikeNode`, `STBIFNeuron` | specialized / training-oriented variants | Same step/reset discipline |
| `PSN`, `MaskedPSN`, `SlidingPSN`, `FlexSN` | parallel / kernel-oriented families | Follow the same state contracts |

### Verified live backend notes

- `IFNode(step_mode='s')` reports `supported_backends=('torch', 'cupy')`.
- `IFNode(step_mode='m')` and `LIFNode(step_mode='m')` report `supported_backends=('torch', 'cupy', 'triton')`.
- `ParametricLIFNode(step_mode='s')` reports `supported_backends=('torch',)`; `step_mode='m'` expands to `('torch', 'cupy', 'triton')`.
- `ActivationAwareIFNode(step_mode='m')` reports `supported_backends=('torch', 'triton')`.
- `PSN` is multi-step only.
- `SlidingPSN` reports backend choices `('gemm', 'conv')`.

## 5) Layers and wrappers

### Stateless wrappers with `step_mode`

| Class family | Constructor shape | Multi-step behavior |
| --- | --- | --- |
| `Linear`, `Conv1d/2d/3d`, `ConvTranspose1d/2d/3d` | mirrors `torch.nn` plus `step_mode='s'` | `step_mode='m'` flattens time via `seq_to_ann_forward` |
| `Flatten`, `Upsample`, `GroupNorm`, `AvgPool*`, `MaxPool*`, `AdaptiveAvgPool*` | mirrors `torch.nn` plus `step_mode` | same as above |
| `WSConv2d`, `WSLinear` | weight-standardized wrappers | same as above |

### Stateful helpers and recurrent wrappers

| Class | Role |
| --- | --- |
| `SynapseFilter` | Exponentially decaying synaptic current |
| `Delay` | Queue-based timestep delay |
| `NeuNorm` | Normalization with explicit state |
| `VotingLayer` | Average-pooling vote reduction |
| `BatchNormThroughTime1d/2d/3d` | One BN per time step; remember to reset `t` |
| `ThresholdDependentBatchNorm1d/2d/3d` | tdBN with multi-step-only semantics |
| `TemporalEffectiveBatchNorm1d/2d/3d` | TEBN with learnable per-time-step scale |
| `ElementWiseRecurrentContainer` | Recurrent wrapper with element-wise feedback |
| `LinearRecurrentContainer` | Recurrent wrapper with linear feedback |
| `StepModeContainer` | Chooses single-step or sequence forwarding based on `stateful` |
| `MultiStepContainer`, `SeqToANNContainer` | `nn.Sequential` wrappers for multi-step and seq-to-ANN execution |
| `TLastMultiStepContainer`, `TLastSeqToANNContainer` | Time-last variants |

### Important wrapper rules

- `set_step_mode(net, 'm')` intentionally does not rewrite the interior of the container wrappers listed above.
- `SeqToANNContainer` and `MultiStepContainer` expect contained modules to stay single-step inside the container.
- `BatchNormThroughTime*` is stateful and uses an internal time index `t`; reset after each sequence.

## 6) RNN modules

### Core signatures

| API | Live signature summary |
| --- | --- |
| `SpikingRNNCellBase(input_size, hidden_size, bias=True)` | Base cell class |
| `SpikingRNNBase(input_size, hidden_size, num_layers, bias=True, dropout_p=0, invariant_dropout_mask=False, bidirectional=False, *args, **kwargs)` | Stacked RNN wrapper |
| `SpikingVanillaRNNCell(input_size, hidden_size, bias=True, surrogate_function=Erf())` | Vanilla cell |
| `SpikingGRUCell(input_size, hidden_size, bias=True, surrogate_function1=Erf(), surrogate_function2=None)` | GRU cell |
| `SpikingLSTMCell(input_size, hidden_size, bias=True, surrogate_function1=Erf(), surrogate_function2=None)` | LSTM cell |
| `SpikingVanillaRNN(...)`, `SpikingGRU(...)`, `SpikingLSTM(...)` | stacked / optionally bidirectional RNNs |

### RNN state contracts

- Time axis is first: `x.shape = [T, batch_size, input_size]`.
- Output shape is `[T, batch_size, hidden_size * num_directions]`.
- For a single-state RNN, `states` can be a tensor.
- For LSTM, `states` is a tuple of tensors.
- For bidirectional models, the state dimension is ordered as forward layers first, then reverse layers.

## 7) Monitors

| Class | Records |
| --- | --- |
| `OutputMonitor` | Module outputs |
| `InputMonitor` | Module inputs |
| `AttributeMonitor` | A named attribute before or after forward |
| `GradInputMonitor` | Gradient of module inputs (`dL/dX`) |
| `GradOutputMonitor` | Gradient of module outputs (`dL/dY`) |
| `GPUMonitor` | Periodic GPU utilization and memory samples |

### Monitor behavior

- `records` is a list.
- `monitored_layers` stores the dotted names of matched modules.
- `monitor[i]` returns the `i`-th record.
- `monitor['layer_name']` returns the list of records for that layer.
- Use `enable()`, `disable()`, `clear_recorded_data()`, and `remove_hooks()` explicitly.
- `AttributeMonitor('v_seq', False, ...)` only works when the neuron was created with `store_v_seq=True`.
- Gradient monitors require backward to run.

## 8) Timing-based helpers

The `spikingjelly.timing_based` package does not re-export these helpers at the top level; import the submodules directly.

### `GaussianTuning`

- Signature: `GaussianTuning(n, m, x_min, x_max)`.
- `n > 0`, `m > 2`.
- `x_min` and `x_max` must both have shape `[n]`, and every `x_min[i] < x_max[i]`.
- `encode(x, max_spike_time=50)` expects `x.shape = [batch_size, n, samples_count]` and returns `[batch_size, n, samples_count, m]`.
- Returned `-1` entries mark inactive neurons.

### `Tempotron`

- Signature: `Tempotron(in_features, out_features, T, tau=15.0, tau_s=3.75, v_threshold=1.0)`.
- Input spike times have shape `[batch_size, in_features]`.
- `forward(in_spikes, ret_type)` accepts `ret_type` in `{'v', 'v_max', 'spikes'}`.
- `mse_loss(v_max, label)` is the built-in classification loss helper.

## 9) Visualizing helpers

| Function | Input contract | Returns |
| --- | --- | --- |
| `plot_1d_spikes(spikes, ...)` | `spikes.shape = [T, N]` | `(fig, ax)` |
| `plot_one_neuron_v_s(v, s, ...)` | `v.shape = [T]`, `s.shape = [T]` | `(fig, ax_voltage, ax_spike)` |
| `plot_2d_heatmap(array, ...)` | `array.shape = [T, N]` | `(fig, ax)` |
| `plot_2d_bar_in_3d(array, ...)` | `array.shape = [T, N]` | `(fig, ax)` |
| `plot_2d_feature_map(x3d, nrows, ncols, space, ...)` | `x3d.shape = [C, W, H]` and `nrows * ncols == C` | `(fig, ax)` |

## 10) Configure and logger behavior

### `spikingjelly.configure`

The package reads `SJ_*` environment variables at import time. Set them before Python starts.

| Variable | Default | Meaning |
| --- | --- | --- |
| `SJ_MAX_THREADS_NUMBER_FOR_DATASETS_PREPROCESS` | `16` | Dataset preprocessing thread cap |
| `SJ_CUDA_THREADS` | `512` | Default CUDA thread count |
| `SJ_CUDA_COMPILER_OPTIONS` | `-use_fast_math` | CuPy compiler options |
| `SJ_CUDA_COMPILER_BACKEND` | `nvrtc` | CuPy compiler backend |
| `SJ_SAVE_DATASETS_COMPRESSED` | `1` | Whether dataset outputs are compressed |
| `SJ_SAVE_SPIKE_AS_BOOL_IN_NEURON_KERNEL` | `0` | Bool spike storage in CuPy neuron kernels |
| `SJ_SAVE_BOOL_SPIKE_LEVEL` | `0` | Bool spike packing level |
| `SJ_TRITON_NEURON_KERNEL_STATIC_RANGE_MAX_T` | `64` | Triton static-range cutoff |

### `spikingjelly.logger`

- Exports Loguru's global logger as `spikingjelly.logger.logger`.
- The `