# Troubleshooting

This page covers the common failure modes for core activation-based SNN modeling. If the issue is really about datasets, ANN2SNN conversion, backend performance/precision, training scale-out, or deployment exchange, route it to the sibling sub-skill instead of debugging it here.

## Route out first

- Dataset acquisition, preprocessing, and builder layout: [datasets](../../datasets/)
- ANN-to-SNN calibration/conversion: [ann2snn](../../ann2snn/)
- Kernel, precision, profiling, and backend tuning: [performance-and-analysis](../../performance-and-analysis/)
- Model zoo, training, and distributed scale-out: [training-and-scaleout](../../training-and-scaleout/)
- NIR/Lava/Lynxi exchange: [deployment-exchange](../../deployment-exchange/)

## Common failure modes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `spikingjelly` imports the wrong module or a local checkout shadows the package | Python is running from the wrong cwd or the editable install is not the one you expect | Check `spikingjelly.__file__`, run from outside the source tree when sanity-checking the install, and keep the inspection environment aligned with the package in the repo |
| Import-time `ValueError` from `configure` | Invalid `SJ_*` value or the variable was set after Python already imported `spikingjelly.configure` | Set environment variables before Python starts; keep boolean envs as `0` or `1`, and integers as valid positive integers |
| Logs are silent even though code uses `spikingjelly.logger.logger` | The `spikingjelly` Loguru namespace is disabled by default and no sink was enabled | Add a sink in application code, then call `logger.enable("spikingjelly")` before importing the modules that emit diagnostics |
| `RuntimeError: Trying to backward through the graph a second time...` after one batch | Stateful modules were not reset between batches | Call `functional.reset_net(net)` after each batch; if the module tree changed, call `functional.invalidate_reset_cache(net)` first |
| `step_mode` or input-shape errors (`[N, *]` vs `[T, N, *]`) | A single-step module received a time-major tensor, or the network was left in the wrong mode | Use `functional.set_step_mode(net, 'm')` for time-major sequences, or wrap the loop with `functional.multi_step_forward(...)` |
| A custom neuron subclass behaves like a teaching example but does not support native functional execution | `SimpleBaseNode` was used when the implementation really needed `BaseNode` functional transitions | Use `SimpleBaseNode` only for readable charge/fire/reset overrides; use `BaseNode` and implement `single_step_functional_forward` for production explicit-state behavior |
| `set_backend` warns that a module does not support the chosen backend | The neuron class or its current `step_mode` does not expose that backend | This is a backend-capability issue, not a core modeling bug; route the deeper investigation to [performance-and-analysis](../../performance-and-analysis/) |
| `AttributeMonitor('v_seq', ...)` records nothing | `store_v_seq=True` was not set before the forward pass, or the monitor was disabled | Set `store_v_seq=True` when constructing the neuron, keep the monitor enabled, and remember that `reset()` clears `v_seq` |
| Monitor records keep growing even after the object was deleted | Python does not guarantee `__del__()` timing, so hooks may still be attached | Call `remove_hooks()` explicitly when you are done with the monitor |
| Gradient monitors return empty records | No backward pass ran, or the monitored tensors did not require gradients | Call `backward()` on a scalar loss and make sure the relevant inputs/parameters have `requires_grad=True` |
| `BatchNormThroughTime*` behaves as if it is stuck on one time step | Its internal time index `t` was not reset after a sequence | Call `reset()` after each full `T`-step run so the next sequence starts at time step 0 |
| `GaussianTuning` or `Tempotron` rejects the input shape | The timing-based helper expects a different layout from the activation-based SNN stack | Use `GaussianTuning(x)` with `x.shape=[batch_size, n, samples_count]` and `Tempotron(in_spikes)` with `shape=[batch_size, in_features]` |
| Visualizing helpers raise rank or grid-size errors | The input tensor rank is wrong, or `nrows * ncols != C` for feature maps | Match the helper’s expected rank exactly; for `plot_2d_feature_map`, ensure the number of tiles equals `C` |
| A module keeps stale state after the input shape changes | A stateful module cached tensor memories that no longer match the new input shape | Reset the network before switching batch/layout shapes, or re-run the first forward so the module can materialize new tensor states |

## Quick checks

### Confirm the package and config

```bash
python - <<'PY'
import spikingjelly
from spikingjelly import configure
print(spikingjelly.__file__)
print(configure.cuda_threads)
print(configure.cuda_compiler_backend)
print(configure.triton_neuron_kernel_static_range_max_T)
PY
```

### Confirm step mode and memories

```bash
python - <<'PY'
from spikingjelly.activation_based import base, functional, layer, neuron
import torch
net = torch.nn.Sequential(layer.Linear(3, 4), neuron.IFNode(), layer.Linear(4, 2), neuron.LIFNode())
functional.set_step_mode(net, 'm')
print(net)
print(list(base.named_memories(net)))
PY
```

### Confirm logger activation

```bash
python - <<'PY'
import sys
from spikingjelly.logger import logger
logger.remove()
logger.add(sys.stderr, level='INFO')
logger.enable('spikingjelly')
logger.info('core-snn logger is enabled')
PY
```

## Evidence anchors

Primary evidence used for these troubleshooting rules:

- `spikingjelly/activation_based/base.py`
- `spikingjelly/activation_based/functional/net_config.py`
- `spikingjelly/activation_based/functional/forward.py`
- `spikingjelly/activation_based/functional/layer.py`
- `spikingjelly/activation_based/functional/neuron.py`
- `spikingjelly/activation_based/layer/container.py`
- `spikingjelly/activation_based/layer/misc.py`
- `spikingjelly/activation_based/monitor.py`
- `spikingjelly/timing_based/encoding.py`
- `spikingjelly/timing_based/neuron.py`
- `spikingjelly/visualizing/*.py`
- `spikingjelly/configure.py`
- `spikingjelly/logger.py`
- `docs/source/tutorials/en/basic_concept.rst`
- `docs/source/tutorials/en/neuron.rst`
- `docs/source/tutorials/en/surrogate.rst`
- `docs/source/tutorials/en/monitor.rst`
- `docs/source/tutorials/en/recurrent_connection_and_stateful_synapse.rst`
- `test/test_configure.py`
- `test/test_logging_policy.py`
- `test/activation_based/test_functional.py`
- `test/activation_based/test_monitor.py`
- `test/activation_based/test_rnn.py`
- `test/test_visualizing.py`
- `test/timing_based/test_encoding.py`
- `test/timing_based/test_neuron.py`
- `skills/tests/spikingjelly/reports/environment/repo_env_report.json`

## Known limits

- This page intentionally does not cover backend kernel internals, precision tuning, or throughput profiling; that belongs in [performance-and-analysis](../../performance-and-analysis/).
- It also does not cover dataset layout or ANN2SNN conversion details.
- If a failure message mentions an optional backend or accelerator, treat it as a capability question first, not a core-modeling question.
