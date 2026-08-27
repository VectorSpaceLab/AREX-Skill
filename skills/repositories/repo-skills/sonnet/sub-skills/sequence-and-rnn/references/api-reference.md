# Sequence and RNN API Reference

## Cores and state

- `snt.RNNCore`: base class for recurrent cores. A core maps `(input_t, state_t)` to `(output_t, state_{t+1})` and provides `initial_state(batch_size)`.
- `snt.LSTM(hidden_size)`: state is an `LSTMState(hidden, cell)` named tuple.
- `snt.GRU(hidden_size)`, `snt.VanillaRNN(hidden_size)`: state is typically a tensor with shape `[batch, hidden_size]`.
- `snt.DeepRNN(cores_or_layers, skip_connections=False)`: stacks cores and optional non-recurrent callables.
- `snt.dynamic_unroll(core, input_sequence, initial_state, sequence_length=None, time_major=True)`: unrolls a sequence tensor. Default layout is time-major `[time, batch, ...]`.
- `snt.static_unroll(core, input_sequence, initial_state)`: unrolls Python lists/tuples of per-time tensors.
- `snt.TrainableState(batch_size, state_size)` and `snt.UnrolledLSTM`: specialized stateful/unrolled helpers.

## Shape rules

Default `dynamic_unroll` expects time-major input. If your data is batch-major `[batch, time, features]`, pass `time_major=False` or transpose. Initial state batch size must match the sequence batch dimension.
