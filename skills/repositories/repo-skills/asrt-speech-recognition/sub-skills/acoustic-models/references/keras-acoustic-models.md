# Keras acoustic model classes

ASRT's primary acoustic backend is TensorFlow/Keras. The source defines a small interface base class plus four CNN+CTC acoustic model variants. Use these facts when selecting, constructing, loading, or saving acoustic models.

## Public model interface

`BaseModel` is the acoustic model interface used by `ModelSpeech`:

- State attributes: `input_shape`, `output_shape`, `model`, `model_base`, `_model_name`.
- `get_model() -> (model, model_base)`: returns the training model with CTC loss inputs and the base inference model that maps acoustic features to class probabilities.
- `get_train_model()` and `get_eval_model()`: return `model` and `model_base` respectively.
- `summary()`: prints the training model summary.
- `get_model_name() -> str`: returns the ASRT model name used in save paths.
- `load_weights(filename)`: loads weights into the training model via Keras `load_weights(filename)`.
- `save_weights(filename)`: writes both `filename + '.model.h5'` and `filename + '.model.base.h5'`, and writes an `epoch_<model_name>.txt` marker containing `filename`.
- `get_loss_function()` and `forward(data_input)`: implemented by subclasses.

`ModelSpeech` calls `speech_model.get_model()` during construction, then uses the training model for CTC training and the base model inside each subclass `forward` method for decoding.

## Keras variants

All four Keras variants are defined as convolutional acoustic models with CTC loss and greedy CTC decoding. Their constructor defaults are:

```python
SpeechModel24(input_shape=(1600, 200, 1), output_size=1428)
SpeechModel25(input_shape=(1600, 200, 1), output_size=1428)
SpeechModel251(input_shape=(1600, 200, 1), output_size=1428)
SpeechModel251BN(input_shape=(1600, 200, 1), output_size=1428)
```

Important default dimensions:

- `input_shape=(1600, 200, 1)` means at most 1600 acoustic frames, 200 frequency bins, one channel. The README describes this as approximately a 16 second maximum input.
- Every listed Keras variant uses `_pool_size = 8`.
- Default `output_shape=(input_shape[0] // 8, output_size)`, therefore `(200, 1428)` for the default input.
- The default output size is `1428`, documented in the training/evaluation scripts as 1427 pinyin symbols plus one CTC blank.
- The CTC label input length is fixed at `label_max_string_length = 64` in the model definitions, and `ModelSpeech` defaults `max_label_length=64`.

Model names returned by `get_model_name()`:

| Class | Model name |
| --- | --- |
| `SpeechModel24` | `SpeechModel24` |
| `SpeechModel25` | `SpeechModel25` |
| `SpeechModel251` | `SpeechModel251` |
| `SpeechModel251BN` | `SpeechModel251bn` |

Use the exact `SpeechModel251bn` casing when deriving default weight paths.

## Training model versus base model

Each Keras variant builds two Keras `Model` objects:

- `model_base`: inference graph, `inputs=the_input`, `outputs=y_pred`, where `y_pred` is a softmax over output classes for each output frame.
- `model`: training graph, `inputs=[the_input, the_labels, input_length, label_length]`, `outputs=ctc`, where the `ctc` `Lambda` layer computes `K.ctc_batch_cost(labels, y_pred, input_length, label_length)`.

`get_loss_function()` returns `{'ctc': lambda y_true, y_pred: y_pred}` because the training graph's output is already the computed CTC loss.

## Forward decoding behavior

Each Keras subclass `forward(data_input)`:

1. Allocates a batch of shape `(1,) + input_shape` filled with zeros.
2. Copies the provided feature array into the beginning of that batch.
3. Runs `model_base.predict`.
4. Decodes with `K.ctc_decode(..., greedy=True, beam_width=100, top_paths=1)`.
5. Converts TensorFlow 1.x or 2.x tensor output to a NumPy array.
6. Calls ASRT's `ctc_decode_delete_tail_blank` helper and returns the decoded pinyin-symbol indexes.

The subclass does not itself check that `len(data_input) <= input_shape[0]`; evaluation checks and skips overlong samples, while single-file recognition does not guard this before calling `forward`. A caller should validate the feature length before prediction to avoid NumPy broadcasting errors or bad CTC lengths.

## Minimal construction smoke

A CPU-only construction smoke is useful before expensive training or GPU setup:

```bash
python scripts/inspect_keras_model.py --model 251bn --summary-base
```

Expected default facts include model name `SpeechModel251bn`, input shape `(1600, 200, 1)`, and output shape `(200, 1428)`. This proves the Keras graph can be instantiated in the current Python environment, but it does not prove CUDA training, dataset correctness, or weight compatibility.

## Version and package expectations

Repository documentation states Python 3.9+ and TensorFlow 2.5 through 2.11+ for ASRT operation. The checked `requirements.txt` pins `tensorflow-gpu==2.8.4`, while the Dockerfile uses `tensorflow-cpu==2.5.3` for CPU-only inference service. A separate not-import build verified that TensorFlow CPU 2.11 can instantiate `SpeechModel251BN`; do not treat that CPU smoke as proof of GPU training readiness.
