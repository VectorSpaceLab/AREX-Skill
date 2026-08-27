# Sequence Workflows

## LSTM unroll

```python
core = snt.LSTM(16)
sequence = tf.ones([time, batch, features])
initial_state = core.initial_state(batch)
outputs, final_state = snt.dynamic_unroll(core, sequence, initial_state)
assert outputs.shape.as_list() == [time, batch, 16]
```

## GRU or VanillaRNN

Swap the core constructor and keep the same unroll protocol. The state is a tensor, not an `LSTMState` pair.

## DeepRNN

```python
core = snt.DeepRNN([snt.LSTM(32), snt.LSTM(32)])
outputs, state = snt.dynamic_unroll(core, sequence, core.initial_state(batch))
```

Use skip/residual options only after confirming compatible output sizes.

## Trainable state

Use `snt.TrainableState` when the initial state itself is learned. It owns variables, so build/call before checkpointing and include it with the model.

## ConvLSTM

ConvLSTM cores expect image-like spatial input at each time step. Validate `[time, batch, height, width, channels]` layout and channel dimension before unrolling.
