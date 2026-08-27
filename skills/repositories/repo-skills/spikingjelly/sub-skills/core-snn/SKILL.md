---
name: core-snn
description: "Teach and debug SpikingJelly activation-based core SNN modeling:
  step modes, state reset, surrogate gradients, neurons, layers, recurrent
  wrappers, monitors, and tiny timing/visualization helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Core SNN Modeling

Use this sub-skill when the task is to construct, inspect, or debug the core `spikingjelly.activation_based` object model for activation-based spiking neural networks.

## Route here for

- `base`: step-mode-aware modules, state registration, memory extraction, functional conversion.
- `functional`: network-wide step-mode/reset/backend helpers and explicit forward wrappers.
- `surrogate`: Heaviside-based surrogate-gradient modules and gradient helpers.
- `neuron`: canonical IF/LIF/PLIF/PSN/FlexSN neurons and the main stateful neuron families.
- `layer`: step-aware stateless layers, recurrent wrappers, stateful synapse helpers, batch-norm variants, and attention wrappers.
- `rnn`: stacked spiking RNN cells and bidirectional wrappers.
- `monitor`: output/input/attribute/gradient monitors and GPU sampling.
- `timing_based`: `GaussianTuning` and `Tempotron`.
- `visualizing`: spike, voltage, and feature-map plotting helpers.
- `configure` and `logger`: package-level import-time config and logging behavior.

## Do not handle here

- Neuromorphic datasets, download/build flows, and frame/event preprocessing: route to [datasets](../datasets/).
- ANN-to-SNN conversion, calibration, and recipe selection: route to [ann2snn](../ann2snn/).
- Backend performance, kernels, precision, profiling, and memory optimization: route to [performance-and-analysis](../performance-and-analysis/).
- Model zoo, training loops, distributed scale-out, and benchmark-heavy workflows: route to [training-and-scaleout](../training-and-scaleout/).
- NIR/Lava/Lynxi exchange or deployment paths: route to [deployment-exchange](../deployment-exchange/).

## Operating workflow

1. Prefer stable public imports from the top-level namespaces:
   - `from spikingjelly.activation_based import base, functional, surrogate, neuron, layer, rnn, monitor`
   - `from spikingjelly.timing_based.encoding import GaussianTuning`
   - `from spikingjelly.timing_based.neuron import Tempotron`
   - `from spikingjelly import visualizing`
   - `from spikingjelly import configure`
   - `from spikingjelly.logger import logger`
2. Decide whether the network is single-step (`step_mode='s'`) or multi-step (`step_mode='m'`). Use `[N, *]` for single-step inputs and `[T, N, *]` for time-major sequences.
3. Reset stateful modules between batches with `functional.reset_net(net)`. If the model structure changes, invalidate the reset cache first with `functional.invalidate_reset_cache(net)`.
4. For custom neuron dynamics, use `SimpleBaseNode` when you want the readable charge/fire/reset path, or `BaseNode` when you want explicit functional transitions and backend-aware kernels.
5. Use monitors and plotting helpers only as side-effect-free inspection tools. Remove hooks explicitly when you are done.
6. Keep dataset, ANN2SNN, backend-performance, training, and deployment questions routed out of this sub-skill.

## Bundled references

- [`references/core-api.md`](references/core-api.md)
- [`references/troubleshooting.md`](references/troubleshooting.md)

## Bundled script

- [`scripts/minimal_core_smoke.py`](scripts/minimal_core_smoke.py): tiny no-download smoke for a mixed IF/LIF network, `functional.reset_net`, `functional.set_step_mode`, and monitor/surrogate checks.

## Evidence base

Consulted source files:

- `spikingjelly/activation_based/base.py`
- `spikingjelly/activation_based/functional/net_config.py`
- `spikingjelly/activation_based/functional/forward.py`
- `spikingjelly/activation_based/functional/layer.py`
- `spikingjelly/activation_based/functional/neuron.py`
- `spikingjelly/activation_based/functional/misc.py`
- `spikingjelly/activation_based/surrogate.py`
- `spikingjelly/activation_based/neuron/base_node.py`
- `spikingjelly/activation_based/neuron/integrate_and_fire.py`
- `spikingjelly/activation_based/neuron/lif.py`
- `spikingjelly/activation_based/neuron/plif.py`
- `spikingjelly/activation_based/layer/container.py`
- `spikingjelly/activation_based/layer/stateless_wrapper.py`
- `spikingjelly/activation_based/layer/bn.py`
- `spikingjelly/activation_based/layer/misc.py`
- `spikingjelly/activation_based/rnn.py`
- `spikingjelly/activation_based/monitor.py`
- `spikingjelly/timing_based/encoding.py`
- `spikingjelly/timing_based/neuron.py`
- `spikingjelly/visualizing/*.py`
- `spikingjelly/configure.py`
- `spikingjelly/logger.py`

Consulted docs:

- `docs/source/tutorials/en/basic_concept.rst`
- `docs/source/tutorials/en/neuron.rst`
- `docs/source/tutorials/en/surrogate.rst`
- `docs/source/tutorials/en/monitor.rst`
- `docs/source/tutorials/en/recurrent_connection_and_stateful_synapse.rst`
- `docs/source/APIs/spikingjelly.activation_based.rst`
- `docs/source/APIs/spikingjelly.activation_based.base.rst`
- `docs/source/APIs/spikingjelly.activation_based.functional.rst`
- `docs/source/APIs/spikingjelly.activation_based.neuron.rst`
- `docs/source/APIs/spikingjelly.activation_based.neuron.core.rst`
- `docs/source/APIs/spikingjelly.activation_based.neuron.research.rst`
- `docs/source/APIs/spikingjelly.activation_based.surrogate.rst`
- `docs/source/APIs/spikingjelly.activation_based.monitor.rst`
- `docs/source/APIs/spikingjelly.activation_based.rnn.rst`
- `docs/source/APIs/spikingjelly.timing_based.rst`
- `docs/source/APIs/spikingjelly.visualizing.rst`
- `docs/source/APIs/spikingjelly.configure.rst`
- `docs/source/APIs/spikingjelly.logger.rst`

Consulted tests:

- `test/test_configure.py`
- `test/activation_based/test_functional.py`
- `test/activation_based/test_functional_layer.py`
- `test/activation_based/test_functional_neuron.py`
- `test/activation_based/test_monitor.py`
- `test/activation_based/test_neuron_variants.py`
- `test/activation_based/test_rnn.py`
- `test/test_visualizing.py`
- `test/timing_based/test_encoding.py`
- `test/timing_based/test_neuron.py`
- `test/test_logging_policy.py`

Verified live-signature evidence:

- `skills/tests/spikingjelly/reports/environment/repo_env_report.json` confirms Python 3.11, installed `spikingjelly 2.0.0.dev1`, and required CPU/CUDA/CuPy/Triton/NIR/transformers imports.
- The same report records that the required CUDA/CuPy/Triton smoke passed on the A100 host.
