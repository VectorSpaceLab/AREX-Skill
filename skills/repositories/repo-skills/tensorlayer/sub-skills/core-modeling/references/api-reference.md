# API Reference

## Verified core signatures

These package facts were checked against the installed TensorLayer distribution:

- `Input(shape, dtype=tf.float32, name=None)`
- `Dense(n_units, act=None, W_init=<...>, b_init=<...>, in_channels=None, name=None)`
- `Conv2d(n_filter=32, filter_size=(3, 3), strides=(1, 1), act=None, padding='SAME', data_format='channels_last', dilation_rate=(1, 1), W_init=<...>, b_init=<...>, in_channels=None, name=None)`
- `Model(inputs=None, outputs=None, name=None)`
- `Model.save(self, filepath, save_weights=True, customized_data=None)`
- `Model.load(filepath, load_weights=True)`
- `Model.save_weights(self, filepath, format=None)`
- `Model.load_weights(self, filepath, format=None, in_order=True, skip=False)`
- `vgg16(pretrained=False, end_with='outputs', mode='dynamic', name=None)`
- `MobileNetV1(pretrained=False, end_with='out', name=None)`
- `ResNet50(pretrained=False, end_with='fc1000', n_classes=1000, name=None)`
- `SqueezeNetV1(pretrained=False, end_with='out', name=None)`
- `Seq2seq(decoder_seq_length, cell_enc, cell_dec, n_units=256, n_layer=3, embedding_layer=None, name=None)`
- `Seq2seqLuongAttention(hidden_size, embedding_layer, cell, method, name=None)`

## Usage notes

- Use `Input(...)` to build static graphs.
- Use `Model` subclasses when the architecture needs a `forward(...)` method.
- Prefer `save_weights` / `load_weights` for tiny round-trips; use `save` / `load` when the full model object must be persisted.
- Leave pretrained constructors on `pretrained=False` for bundled smoke checks.
- `Model` names must be unique across the process; reused names can trigger a `ValueError`.

## Evidence summary

This page distills TensorLayer's layer, model, activation, initializer, naming, and save/load tests plus the pretrained-constructor examples into the verified signatures above. Runtime instructions do not require opening the source checkout.
