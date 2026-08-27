---
name: core-neurons
description: "Build and debug snnTorch neuron, recurrent layer, state lifecycle,
  and batchnorm-through-time workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# core-neurons

Use this sub-skill when the task is to construct, combine, or debug snnTorch neuron and neuron-layer workflows.

## Route here for

- Core neuron construction and calls for `Leaky`, `Synaptic`, `RLeaky`, `RSynaptic`, `Lapicque`, `Alpha`, and `DeltaLeaky`.
- Time-parallel or state-only neuron layers: `LinearLeaky`, `StateLeaky`, and `LeakyParallel`.
- Recurrent and LSTM-like spiking layers: `SConv2dLSTM`, `SLSTM`, and `AssociativeLeaky`.
- Hidden-state lifecycle choices: manual state tuples, `init_hidden=True`, `reset_mem`, class-level `reset_hidden`/`detach_hidden`, and `snntorch.utils.reset`.
- Reset semantics, learnable decay/threshold flags, recurrent wiring choices, `BatchNormTT1d`/`BatchNormTT2d`, and `GradedSpikes`.

## Do not handle here

- Spike encodings, surrogate-gradient selection depth, loss functions, metrics, STDP, quantization recipes, or full training-loop design: route to `encoding-training`.
- NIR export/import or NIR graph round trips: route to `nir-interoperability`.
- Spike raster/count/trace/animation plotting: route to `plotting`.
- Legacy neuromorphic dataset wrappers or dataset downloads: route to `spikevision`.

## Operating workflow

1. Identify whether the user needs a stepwise neuron cell, a time-major sequence layer, a recurrent cell, or a helper layer.
2. Check the exact constructor, state tuple, and return contract in [API reference](references/api-reference.md).
3. Pick the state-management pattern in [workflows](references/workflows.md): manual states, `init_hidden=True`, stateless time-major layers, or `LeakyParallel`.
4. Before changing model logic, triage state-count, reset, learnable-parameter, device, and shape failures with [troubleshooting](references/troubleshooting.md).
5. For a safe local smoke check, run one of the bundled scripts below; they use synthetic tensors only and require no downloads.

## Bundled scripts

- [`scripts/leakyparallel_forward_smoke.py`](scripts/leakyparallel_forward_smoke.py): synthetic `LeakyParallel` forward/gradient smoke, including diagonal recurrent-gradient behavior.
- [`scripts/leakyparallel_train_smoke.py`](scripts/leakyparallel_train_smoke.py): tiny synthetic `LeakyParallel` optimization smoke adapted from the example training pattern without external data.
- [`scripts/mixed_state_chain_smoke.py`](scripts/mixed_state_chain_smoke.py): difficult mixed `Leaky` + `LinearLeaky` + `StateLeaky` state-reset case, with BNTT and `GradedSpikes` sanity checks.
- [`scripts/associative_leaky_smoke.py`](scripts/associative_leaky_smoke.py): `AssociativeLeaky.from_num_spiking_neurons` q-projection toggle plus chunked-batch gradient equivalence.
- [`scripts/spiking_lstm_smoke.py`](scripts/spiking_lstm_smoke.py): `SLSTM` and `SConv2dLSTM` state-tuple and shape smoke.

Start with [workflows](references/workflows.md) for recipes and [API reference](references/api-reference.md) for argument-level constraints.
