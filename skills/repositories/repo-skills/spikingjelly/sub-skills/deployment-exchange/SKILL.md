---
name: deployment-exchange
description: "Teach NIR export/import plus Lava and Lynxi deployment exchange
  for SpikingJelly."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Deployment Exchange

Use this sub-skill when the task is about moving a SpikingJelly model across neuromorphic formats or deployment runtimes.

## Route here for

- NIR export/import, HDF5 graph round-trips, shape metadata, and supported-module checks.
- Lava / Loihi exchange: quantizers, CubaLIFNode, synapse/block conversion, and time-layout transforms.
- Lynxi-oriented compilation: supported-module rewriting, `[TN, *]` flattening rules, tensor conversion, and offline model loading.

## Do not handle here

- Model zoo, training loops, dataset setup, or benchmark-heavy workflows: route to `../training-and-scaleout/`.
- Backend profiling, kernel performance, precision, or memory analysis: route to `../performance-and-analysis/`.
- ANN2SNN recipe selection or converted-model semantics: route to `../ann2snn/`.
- Dataset acquisition or preprocessing: route to `../datasets/`.
- Pure step-mode, reset, or module-composition basics: route to `../core-snn/`.

## Operating workflow

1. Decide whether the user needs NIR, Lava, or Lynxi. If they are still choosing modules or step modes, route to `core-snn` first.
2. For NIR, verify that `example_input` is executable, that the node shapes exclude batch/time axes, and that the installed NIR release matches the exported constructor path before promising a full neuron round-trip.
3. For Lava, separate the always-available quantizer / `CubaLIFNode` notes from the optional Lava-DL conversion helpers.
4. For Lynxi, convert only the supported layer / neuron set, respect the explicit `T` contract, and keep the 4D-or-less tensor and no-inplace constraints visible.
5. If the user is actually debugging kernels or device-specific runtime failures, route to `performance-and-analysis` instead of deepening deployment logic here.

## Read first

- [`references/deployment-workflows.md`](references/deployment-workflows.md)
- [`references/troubleshooting.md`](references/troubleshooting.md)

## Bundled script

- [`scripts/nir_roundtrip_smoke.py`](scripts/nir_roundtrip_smoke.py): no-download CPU smoke for NIR export/import, shape rules, file round-trip, and step-mode import.

## Cross-links

- `../core-snn/` for module composition, reset, and step-mode basics.
- `../ann2snn/` for converted-model semantics when a deployment target is really a converted network.
- `../performance-and-analysis/` for runtime and backend troubleshooting, not deployment-format logic.

## Evidence used

- Source files:
  - `spikingjelly/activation_based/nir_exchange/to_nir.py`
  - `spikingjelly/activation_based/nir_exchange/from_nir.py`
  - `spikingjelly/activation_based/lava_exchange.py`
  - `spikingjelly/activation_based/lynxi_exchange.py`
  - `spikingjelly/activation_based/examples/lava_mnist.py`
  - `spikingjelly/activation_based/examples/lynxi_fmnist_inference.py`
- Tutorials and API docs:
  - `docs/source/tutorials/en/nir_exchange.rst`
  - `docs/source/tutorials/en/lava_exchange.rst`
  - `docs/source/tutorials/cn/inference_on_lynxi.rst`
  - `docs/source/APIs/spikingjelly.activation_based.nir_exchange.rst`
  - `docs/source/APIs/spikingjelly.activation_based.lava_exchange.rst`
  - `docs/source/APIs/spikingjelly.activation_based.lynxi_exchange.rst`
- Tests and behavioral evidence:
  - `test/activation_based/test_functional_neuron.py`
  - integration notes under `skills/tests/spikingjelly/reports/integration/`
- Verified live signatures in the prepared inspection environment:
  - `spikingjelly.activation_based.nir_exchange.export_to_nir(net, example_input, save_path=None, dt=1e-4)`
  - `spikingjelly.activation_based.nir_exchange.import_from_nir(graph, dt=1e-4, device='cpu', dtype=torch.float32, step_mode='s') -> fx.GraphModule`
  - `spikingjelly.activation_based.lava_exchange.CubaLIFNode(current_decay, voltage_decay, v_threshold=1.0, v_reset=0.0, scale=64, requires_grad=False, surrogate_function=..., norm=None, detach_reset=False, step_mode='s', backend='torch', store_v_seq=False, store_i_seq=False)`
  - `spikingjelly.activation_based.lynxi_exchange.IFNode(v_threshold=1.0, v_reset=0.0, step_mode='s', T=None, return_v=False)`
  - `spikingjelly.activation_based.lynxi_exchange.LIFNode(tau=2.0, decay_input=True, v_threshold=1.0, v_reset=0.0, step_mode='s', T=None, return_v=False)`
  - `spikingjelly.activation_based.lynxi_exchange.to_lynxi_supported_module(m_in, T)` / `to_lynxi_supported_modules(net, T)`
- Current environment status:
  - `spikingjelly 2.0.0.dev1` imported successfully.
  - `nir 1.0.8` and `nirtorch 2.6` are installed.
  - The stateless NIR round-trip smoke passes in the prepared env; the neuron-node NIR path remains environment-sensitive because the installed NIR release does not expose the shape-bearing constructor contract expected by the current `to_nir.py` source path.
  - Lava-DL optional helpers and Lynxi vendor compilation helpers were not importable in the prepared env; treat those branches as optional / hardware-dependent.
