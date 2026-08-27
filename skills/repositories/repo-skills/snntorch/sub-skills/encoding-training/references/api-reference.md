# API reference

This page summarizes the public surfaces used by the encoding-training route. Keep public files router-like and prefer the bundled workflows for step-by-step usage.

## Public import map

| Import | What it gives you | Notes |
| --- | --- | --- |
| `from snntorch import spikegen` | spike encodings and target coding | Use for rate, latency, delta, and target transforms. |
| `from snntorch import surrogate` | surrogate-gradient factories | Pass closures to neuron `spike_grad=` arguments. |
| `import snntorch.functional as SF` | accuracy, losses, regularization, monitors | Re-exported from `acc`, `loss`, `reg`, and `probe`. |
| `from snntorch import backprop` | wrapper training loops | Legacy compatibility helper; deprecated. |
| `from snntorch import utils` | reset and dataset helpers | Includes `reset`, `data_subset`, and `valid_split`. |
| `from snntorch.functional import quant` | state quantization helpers | Separate submodule; not a `SF` re-export in this release. |
| `from snntorch.functional.stdp_learner import STDPLearner` | STDP learner | Separate submodule; not a `SF` re-export in this release. |

> There is no standalone `snntorch.functional.metrics` module in this package version. Use `SF.accuracy_rate` and `SF.accuracy_temporal`.

## Spike encoders

### Input encoders

| API | Signature | What it does |
| --- | --- | --- |
| `spikegen.rate` | `rate(data, num_steps=False, gain=1, offset=0, first_spike_time=0, time_var_input=False)` | Rate-codes batch-first data into time-first spikes. If `time_var_input=True`, the input already has a time axis and `num_steps` must stay unset. |
| `spikegen.latency` | `latency(data, num_steps=False, threshold=0.01, tau=1, first_spike_time=0, on_target=1, off_target=0, clip=False, normalize=False, linear=False, interpolate=False, bypass=False, epsilon=1e-07)` | Latency-codes data in `[0,1]`. Use `normalize=True` when you need a fixed number of steps. |
| `spikegen.delta` | `delta(data, threshold=0.1, padding=False, off_spike=False)` | Fires on changes between adjacent time steps. Can emit negative off-spikes. |

### Target encoders

| API | Signature | What it does |
| --- | --- | --- |
| `spikegen.targets_convert` | `targets_convert(targets, num_classes, code='rate', num_steps=False, first_spike_time=0, correct_rate=1, incorrect_rate=0, on_target=1, off_target=0, firing_pattern='regular', interpolate=False, epsilon=1e-07, threshold=0.01, tau=1, clip=False, normalize=False, linear=False, bypass=False)` | Converts 1-D class labels into rate- or latency-coded targets. Time-varying output is used when the chosen code requires it. |
| `spikegen.targets_rate` | `targets_rate(targets, num_classes, num_steps=False, first_spike_time=0, correct_rate=1, incorrect_rate=0, on_target=1, off_target=0, firing_pattern='regular', interpolate=False, epsilon=1e-07)` | Target rate coding with optional time variation. |
| `spikegen.targets_latency` | `targets_latency(targets, num_classes, num_steps=False, first_spike_time=0, on_target=1, off_target=0, interpolate=False, threshold=0.01, tau=1, clip=False, normalize=False, linear=False, epsilon=1e-07, bypass=False)` | Target latency coding. Use `bypass=True` when you want the helper to infer the step count from spike times. |
| `spikegen.target_rate_code` | `target_rate_code(num_steps, first_spike_time=0, rate=1, firing_pattern='regular')` | Builds a single-neuron rate code and the corresponding spike-time index list. |

### Lower-level helpers

| API | Signature | Notes |
| --- | --- | --- |
| `spikegen.rate_conv` | `rate_conv(data)` | Converts a time-first tensor into Poisson-like spike trains. |
| `spikegen.latency_code` | `latency_code(data, num_steps=False, threshold=0.01, tau=1, first_spike_time=0, normalize=False, linear=False, epsilon=1e-07)` | Returns spike-time values and the companion mask used by the latency encoder. |
| `spikegen.latency_code_linear` | `latency_code_linear(data, num_steps=False, threshold=0.01, tau=1, first_spike_time=0, normalize=False)` | Linear latency helper. |
| `spikegen.latency_code_log` | `latency_code_log(data, num_steps=False, threshold=0.01, tau=1, first_spike_time=0, normalize=False, epsilon=1e-07)` | Logarithmic latency helper. |
| `spikegen.rate_interpolate` | `rate_interpolate(spike_time, num_steps, on_target=1, off_target=0, epsilon=1e-07)` | Converts spike times into graded targets. |
| `spikegen.latency_interpolate` | `latency_interpolate(spike_time, num_steps, on_target=1, off_target=0)` | Converts latency codes into graded targets. |
| `spikegen.to_one_hot` | `to_one_hot(targets, num_classes)` | One-hot labels. |
| `spikegen.to_one_hot_inverse` | `to_one_hot_inverse(one_hot_targets)` | Inverts a one-hot matrix. |
| `spikegen.from_one_hot` | `from_one_hot(one_hot_label)` | Converts one-hot labels back to integer class indices. |

### Shape reminders

- Static inputs are usually batch-first `[B, ...]` on entry and time-first `[T, B, ...]` on exit.
- Time-varying inputs should use `time_var_input=True` for `rate` and should not also pass `num_steps`.
- `targets_convert`, `targets_rate`, and `targets_latency` expect 1-D integer labels unless you are using temporal loss targets.
- `targets_rate` returns a batch-first one-hot tensor when `correct_rate=1` and `incorrect_rate=0`; non-default rates or `first_spike_time>0` make the output time-varying.

## Surrogate gradients

Use the closure factories for neuron `spike_grad=` arguments. The `torch.autograd.Function` classes also exist, but the closure factories are the easiest route for routing guidance.

| Factory | Signature | Typical use |
| --- | --- | --- |
| `surrogate.fast_sigmoid` | `fast_sigmoid(slope=25)` | Default-style choice for many training loops. |
| `surrogate.atan` | `atan(alpha=2.0)` | Default package choice if you do not override `spike_grad`. |
| `surrogate.sigmoid` | `sigmoid(slope=25)` | Smooth alternative. |
| `surrogate.triangular` | `triangular(threshold=1)` | Piecewise-linear surrogate. |
| `surrogate.straight_through_estimator` | `straight_through_estimator()` | Straight-through gradient. |
| `surrogate.spike_rate_escape` | `spike_rate_escape(beta=1, slope=25)` | Rate-escape surrogate. |
| `surrogate.custom_surrogate` | `custom_surrogate(custom_surrogate_function)` | Wrap a custom backward rule. |
| `surrogate.SFS`, `surrogate.LSO`, `surrogate.SSO` | `SFS(slope=25, B=1)`, `LSO(slope=0.1)`, `SSO(mean=0, variance=0.2)` | Specialized stochastic or sparse variants. |

## Accuracy, losses, and regularization

`snntorch.functional` re-exports the common accuracy, loss, regularization, and probe helpers.

### Accuracy helpers

| API | Signature | Notes |
| --- | --- | --- |
| `SF.accuracy_rate` | `accuracy_rate(spk_out, targets, population_code=False, num_classes=False)` | Compares spike counts to label indices. Set `population_code=True` when outputs are grouped by class. |
| `SF.accuracy_temporal` | `accuracy_temporal(spk_out, targets)` | Compares spike timing to label indices. |

### Loss constructors

| API | Signature | Notes |
| --- | --- | --- |
| `SF.ce_rate_loss` | `ce_rate_loss(population_code=False, num_classes=False, reduction='mean', weight=None)` | Cross-entropy applied at each time step. |
| `SF.ce_count_loss` | `ce_count_loss(population_code=False, num_classes=False, reduction='mean', weight=None)` | Cross-entropy applied to accumulated spike counts. |
| `SF.ce_max_membrane_loss` | `ce_max_membrane_loss(reduction='mean', weight=None)` | Cross-entropy on the maximum membrane over time. |
| `SF.mse_count_loss` | `mse_count_loss(correct_rate=1, incorrect_rate=0, population_code=False, num_classes=False, reduction='mean', weight=None)` | Mean-square error on spike counts. |
| `SF.mse_membrane_loss` | `mse_membrane_loss(time_var_targets=False, on_target=1, off_target=0, reduction='mean', weight=None)` | Mean-square error on membrane targets. |
| `SF.mse_temporal_loss` | `mse_temporal_loss(target_is_time=False, on_target=0, off_target=-1, tolerance=0, multi_spike=False, reduction='mean', weight=None)` | Mean-square error on spike times. |
| `SF.ce_temporal_loss` | `ce_temporal_loss(inverse='negate', reduction='mean', weight=None)` | Cross-entropy on inverted spike times. |

### Regularization

| API | Signature | Notes |
| --- | --- | --- |
| `SF.l1_rate_sparsity` | `l1_rate_sparsity(Lambda=1e-5)` | L1 penalty on total spike count. This is the only regularizer wired into the legacy backprop wrappers. |

### Shared loss rules

- Instantiate the loss and call it on spike or membrane recordings.
- `spk_out` is usually `[T, B, N]` and `targets` is usually `[B]`.
- `population_code=True` requires `num_classes` and a class count that divides `num_outputs`.
- `reduction='none'` returns unreduced losses for custom weighting or inspection.

## Monitors

All monitor classes expose `records`, `monitored_layers`, `clear_recorded_data()`, `enable()`, `disable()`, and `remove_hooks()`.

| Monitor | Signature | What it records |
| --- | --- | --- |
| `probe.OutputMonitor` | `OutputMonitor(net, instance=None, function_on_output=lambda x: x)` | Layer outputs / spikes. |
| `probe.InputMonitor` | `InputMonitor(net, instance=None, function_on_input=lambda x: x)` | Layer inputs. |
| `probe.AttributeMonitor` | `AttributeMonitor(attribute_name, pre_forward, net, instance=None, function_on_attribute=lambda x: x)` | A named attribute such as membrane potential. |
| `probe.GradInputMonitor` | `GradInputMonitor(net, instance=None, function_on_grad_input=lambda x: x)` | Input gradients during backpropagation. |
| `probe.GradOutputMonitor` | `GradOutputMonitor(net, instance=None, function_on_grad_output=lambda x: x)` | Output gradients during backpropagation. |

Usage reminders:

- `monitor[0]` returns the first recorded item.
- `monitor['layer_name']` returns all records for that layer.
- `AttributeMonitor` can record before or after the forward pass with `pre_forward`.
- Grad monitors stay empty until you run backward.
- Call `remove_hooks()` when the monitor is no longer needed.

## Training helpers

| API | Signature | Notes |
| --- | --- | --- |
| `utils.data_subset` | `data_subset(dataset, subset, idx=0)` | Keeps a 1/`subset` slice of a dataset. Mutates `.data` and `.targets` in place. |
| `utils.valid_split` | `valid_split(ds_train, ds_val, split, seed=0)` | Randomly splits paired datasets. Mutates both datasets in place. |
| `utils.reset` | `reset(net)` | Resets and detaches supported built-in neuron state. |
| `backprop.TBPTT` | `TBPTT(net, dataloader, optimizer, criterion, num_steps=False, time_var=True, time_first=True, regularization=False, device='cpu', K=1)` | Truncated BPTT wrapper. |
| `backprop.BPTT` | `BPTT(net, dataloader, optimizer, criterion, num_steps=False, time_var=True, time_first=True, regularization=False, device='cpu')` | Full BPTT wrapper. Equivalent to `TBPTT(..., K=num_steps)`. |
| `backprop.RTRL` | `RTRL(net, dataloader, optimizer, criterion, num_steps=False, time_var=True, time_first=True, regularization=False, device='cpu')` | Real-time recurrent learning wrapper. Equivalent to `TBPTT(..., K=1)`. |

Wrapper rules:

- Set `init_hidden=True` on spiking layers when you use the legacy wrappers.
- `time_var=True` means the first dimension of each batch is time.
- For time-static data, set `time_var=False` and pass `num_steps`.
- For `[B, T, ...]` inputs, set `time_first=False` so the wrapper can transpose to time-first layout.
- The wrapper matches built-in criteria and regularizers by `__name__`, so use snnTorch functional callables instead of raw `torch.nn` losses when possible.
- The wrapper only wires in `SF.l1_rate_sparsity()` as its built-in regularizer.

## State quantization and STDP

| API | Signature | Notes |
| --- | --- | --- |
| `quant.state_quant` | `state_quant(num_bits=8, uniform=True, thr_centered=True, threshold=1, lower_limit=0, upper_limit=0.2, multiplier=None)` | Returns a quantization closure with a straight-through backward pass. Pass the closure to neuron `state_quant=` arguments. |
| `quant.StateQuant` | `StateQuant(*args, **kwargs)` | Backing autograd function. Usually import the `state_quant` factory instead. |
| `STDPLearner` | `STDPLearner(synapse, sn, tau_pre, tau_post, f_pre=lambda x: x, f_post=lambda x: x)` | Records pre/post spikes and generates local STDP updates. |
| `stdp_linear_single_step` | `stdp_linear_single_step(fc, in_spike, out_spike, trace_pre, trace_post, tau_pre, tau_post, f_pre=lambda x: x, f_post=lambda x: x)` | Lower-level linear STDP update. |
| `mstdp_linear_single_step` | `mstdp_linear_single_step(fc, in_spike, out_spike, trace_pre, trace_post, tau_pre, tau_post, f_pre=lambda x: x, f_post=lambda x: x)` | Eligibility-trace variant for linear layers. |
| `mstdpet_linear_single_step` | `mstdpet_linear_single_step(fc, in_spike, out_spike, trace_pre, trace_post, tau_pre, tau_post, tau_trace, f_pre=lambda x: x, f_post=lambda x: x)` | Eligibility-trace variant with temporal decay. |
| `stdp_conv1d_single_step` | `stdp_conv1d_single_step(conv, in_spike, out_spike, trace_pre, trace_post, tau_pre, tau_post, f_pre=lambda x: x, f_post=lambda x: x)` | Lower-level Conv1d STDP helper. |
| `stdp_conv2d_single_step` | `stdp_conv2d_single_step(conv, in_spike, out_spike, trace_pre, trace_post, tau_pre, tau_post, f_pre=lambda x: x, f_post=lambda x: x)` | Lower-level Conv2d STDP helper. |

STDP usage notes:

- `STDPLearner.step(on_grad=True, scale=1.0)` writes into `synapse.weight.grad`.
- `STDPLearner.step(on_grad=False)` returns the raw delta weight tensor.
- `step()` consumes the monitor records it reads, so record what you need before calling it.
- The built-in learner supports `nn.Linear`, `nn.Conv1d`, and `nn.Conv2d` synapses only.
- The conv helpers reject dilation values other than 1 and grouped convolutions.
- If the wrapped neuron returns `(spk, mem)`, wrap it so the learner sees a spike-only tensor.
