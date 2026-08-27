# Troubleshooting

Use this page when the encoding-training route fails on shapes, imports, wrappers, or local learning.

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `rate()` or `backprop()` complains about the time axis | Time-first vs time-invariant confusion | For static input, pass `num_steps` and keep `time_var_input=False` / `time_var=False`. For existing time series, set `time_var_input=True` or `time_var=True` and do not also pass `num_steps`. |
| `rate(..., time_var_input=True)` rejects `num_steps` | You supplied both a time-varying tensor and an explicit step count | Remove `num_steps`; the time axis already defines the run length. |
| `latency()` raises a value-range or threshold error | Inputs are not normalized to `[0, 1]`, or the threshold is out of range | Normalize features first and keep `threshold` inside `[0, 1]`. Use `normalize=True` and `bypass=True` when you need the helper to infer a step count. |
| `targets_convert` or a population-code loss says `num_outputs` must be a factor of `num_classes` | The output layer size does not divide evenly into class groups | Make `num_outputs` an integer multiple of `num_classes` and pass the same `num_classes` to the loss or accuracy helper. |
| `mse_count_loss` / `ce_count_loss` raises a size or broadcast error | Targets are one-hot, the batch length is wrong, or the target vector is not 1-D | Pass integer class labels with length `batch_size`. Use the synthetic mismatch script to see the failure and the corrected target shape. |
| `backprop.BPTT` raises a criterion lookup error | The wrapper matches criteria by `criterion.__name__`, and raw `torch.nn` losses are not the expected shape | Use snnTorch functional losses such as `SF.mse_count_loss()` or `SF.ce_count_loss()`. If you write a custom callable, make sure the wrapper can see a matching `__name__`. |
| `backprop` prints a deprecation warning | The wrapper is a legacy compatibility path | Prefer a manual training loop for new code. Keep the wrapper only when you need its legacy behavior. |
| `utils.reset(net)` appears to do nothing | The built-in neuron layer is hidden inside custom nesting, or the state lives outside the supported built-ins | Keep built-in spiking layers in the top-level module list, or reset custom modules manually. |
| `SF.quant` or `SF.stdp_learner` import fails | Those helpers are not re-exported by `snntorch.functional` in this release | Import them from their submodules: `from snntorch.functional import quant` and `from snntorch.functional.stdp_learner import STDPLearner`. |
| `STDPLearner.step()` errors with a tuple / spike mismatch | The wrapped neuron returns `(spk, mem)` but the learner needs a spike tensor | Wrap the neuron so its forward returns only the spike tensor before handing it to the learner. |
| `STDPLearner.reset()` raises `AttributeError` | The method is broken in this release | Recreate the learner for a fresh episode instead of calling `reset()`. |
| `STDPLearner.step()` or the single-step STDP helper raises `NotImplementedError` | Unsupported synapse configuration | Stick to `nn.Linear`, `nn.Conv1d`, or `nn.Conv2d` with dilation 1 and, for the conv helpers, groups 1. |
| STDP updates look zero even though spikes are flowing | The learner consumed only one synchronous pre/post event, or the traces were not separated in time | Use a short synthetic sequence where the pre- and post-synaptic spikes occur at different steps. |
| `monitor.records` keeps growing between runs | Hooks were left attached or the records were not cleared | Call `clear_recorded_data()` between runs and `remove_hooks()` when you are done. |
| `spikeplot.spike_count` fails or labels look wrong when you cross-link to plotting | Labels were passed as a tensor instead of a Python list | Pass a list such as `['0', '1', ...]` when you later route output into plotting. |
| `mse_temporal_loss` seems to ignore your time targets | `target_is_time` or `multi_spike` is not set correctly | Use `target_is_time=True` when targets already are spike times, and set `multi_spike=True` only when you supply multiple spike times per class. |

## Fast fixes by workflow

- **Encoding failure**: check input normalization, `num_steps`, and whether the tensor already has a time dimension.
- **Loss failure**: check `[T, B, N]` vs `[B]` shape assumptions and whether population coding is enabled.
- **Wrapper failure**: check `init_hidden=True`, the `time_var` / `time_first` flags, and the `criterion.__name__` rule.
- **Monitor failure**: check that you attached the monitor before the forward pass and that you called `remove_hooks()` afterwards.
- **STDP failure**: check the spike-only output wrapper, the synapse type, and whether you are trying to reuse a stale learner.
