# Sequence and RNN Troubleshooting

| Symptom | Cause | Recovery |
| --- | --- | --- |
| Output shape swaps time and batch | `dynamic_unroll` time-major default was misunderstood. | Use `[time, batch, features]`, pass `time_major=False`, or transpose. |
| Initial state batch mismatch | `core.initial_state` was called with the wrong batch size. | Derive batch from the sequence layout. |
| LSTM state attribute error | LSTM state is an `LSTMState(hidden, cell)`, not one tensor. | Inspect `state.hidden` and `state.cell`. |
| DeepRNN skip/residual shape failure | Adjacent cores have incompatible output sizes. | Disable skip/residual or add projection modules. |
| ConvLSTM shape error | Missing spatial/channel dimensions or wrong layout. | Use `[time, batch, height, width, channels]` unless explicitly configured otherwise. |
| XLA/distribution-specific failure | Backend constraints are outside ordinary CPU RNN use. | Verify backend runtime and read serialization/distribution guidance. |
