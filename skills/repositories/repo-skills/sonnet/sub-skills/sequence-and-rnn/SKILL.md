---
name: sequence-and-rnn
description: "Use Sonnet RNN cores, sequence unroll helpers, trainable recurrent
  state, and convolutional LSTMs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Sequence and RNN

Use this sub-skill for `snt.RNNCore`, `VanillaRNN`, `LSTM`, `GRU`, `DeepRNN`, skip/residual helpers, `static_unroll`, `dynamic_unroll`, `TrainableState`, `UnrolledLSTM`, recurrent dropout, and ConvLSTM modules.

## Start here

- [references/api-reference.md](references/api-reference.md): signatures, state structures, and shape conventions.
- [references/workflows.md](references/workflows.md): LSTM/GRU unrolls, `DeepRNN`, trainable state, recurrent dropout, and ConvLSTM recipes.
- [references/troubleshooting.md](references/troubleshooting.md): time-major, state, skip/residual, ConvLSTM, and backend-specialization errors.
- [scripts/rnn_unroll_smoke.py](scripts/rnn_unroll_smoke.py): safe LSTM/GRU unroll shape smoke.

## Boundaries

- Generic `snt.Module` authoring: [../module-authoring/SKILL.md](../module-authoring/SKILL.md).
- Feed-forward layers/nets: [../layers-and-nets/SKILL.md](../layers-and-nets/SKILL.md).
- Optimizer loops: [../training-and-optimization/SKILL.md](../training-and-optimization/SKILL.md).
- XLA/distribution/backend policy: [../serialization-and-distribution/SKILL.md](../serialization-and-distribution/SKILL.md).
