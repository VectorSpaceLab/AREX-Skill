# Troubleshooting

## Input shape errors

- `StandardDeepLSTM` expects a 2D tensor.
- `CoordinateWiseDeepLSTM` reshapes any tensor to `[-1, 1]`, so the original
  shape must still be statically known well enough for reshape recovery.
- `KernelDeepLSTM` expects a rank-4 convolution-kernel tensor:
  `[kernel_w, kernel_h, in_channels, out_channels]`.
- `Adam` and the LSTM-based nets derive state size from static shapes, so a
  tensor with unknown dimensions can fail before the graph is built.

Fix: choose the right network for the tensor rank, and make sure the shape is
concrete before you call `initial_state_for_inputs`.

## Initializer dict or name issues

- String initializers are TensorFlow initializer names such as `"zeros"`.
- NumPy arrays become constant initializers.
- Dict initializers are matched by layer name first (`lstm_1`, `linear`) and
  then by field name (`w`, `b`, `w_gates`, `b_gates`).
- Typos in dict keys are easy to miss because unrelated keys are ignored.

Fix: inspect the generated config and compare the keys against the layer names
that actually exist in the network.

## `net_path` pickle loading

- `networks.factory(..., net_path=...)` loads a `dill` pickle and uses it as the
  initializer spec.
- The file must come from `networks.save` or `meta.MetaOptimizer.save`.
- Stateless nets produce an empty mapping, which is valid.
- A wrong file path, a corrupted pickle, or a file saved from a mismatched layer
  layout can all lead to load failures or partial initialization.

Fix: re-save the network with the current layout and confirm the file was
written by this repo's save helper.

## `LogAndSign` dtype or shape problems

- The module uses `np.finfo(gradients.dtype.as_numpy_dtype).eps`, so integer
  tensors are not appropriate.
- The rank must be known because the code concatenates along the last axis.
- The output doubles the last dimension, so downstream shapes must account for
  the wider feature width.

Fix: cast gradients to a floating dtype and keep the rank static before you
apply the preprocess module.

## TensorFlow while-loop rejects LSTM state structures

A `MetaOptimizer` graph can fail with `The two structures don't have the same nested structure` when a deep LSTM network's initial state is represented as tuples but the next state is represented as Sonnet `LSTMState` objects. This is an environment/version compatibility issue at the TF1/Sonnet state boundary, not proof that the high-level network choice is wrong.

Fix: confirm a simpler stateless or zero-layer network smoke first, record TensorFlow/Sonnet versions, try an older compatible TF1/Sonnet runtime for historical reproduction, or normalize the state structure in a maintained fork.

## TensorFlow / Sonnet version mismatches

This code base is written for TensorFlow 1.x graph mode and Sonnet 1.x.
It depends on APIs such as `tf.flags`, `tf.app`, `tf.variable_scope`,
`tf.contrib.learn`, `snt.AbstractModule`, `snt.RNNCore`, `snt.DeepRNN`,
and `snt.get_variables_in_module`.

If you see import errors in a newer runtime:

- verify that you are using a TF1-compatible environment
- keep Sonnet on the 1.x line
- keep protobuf on a TF1-compatible version if imports fail before graph build

The verified inspection environment for this repository used TensorFlow 1.15.5,
Sonnet 1.36, and protobuf below 3.20.
