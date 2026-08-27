# Training, resuming, saving, and evaluation

This reference covers ASRT's Keras acoustic training wrapper and the default repository recipes. It intentionally leaves dataset schema and feature-extractor details to the `data-and-features` sub-skill.

## `ModelSpeech` Keras wrapper

`ModelSpeech` is the main Keras acoustic operation wrapper:

```python
ModelSpeech(speech_model, speech_features, max_label_length=64)
```

Construction stores:

- `speech_model`: an instance such as `SpeechModel251BN`.
- `trained_model` and `base_model`: the pair returned by `speech_model.get_model()`.
- `speech_features`: an object with `run(wavsignal, fs)` such as `Spectrogram` for evaluation/prediction or `SpecAugment` for training.
- `max_label_length`: defaults to `64`.

Key methods:

| Method | Purpose |
| --- | --- |
| `train_model(self, optimizer, data_loader, epochs=1, save_step=1, batch_size=16, last_epoch=0, call_back=None)` | Compile the CTC model, iterate ASRT data batches, and save periodic weights. |
| `evaluate_model(self, data_loader, data_count=-1, out_report=False, show_ratio=True, show_per_step=100)` | Decode dataset samples and print a word error ratio over pinyin-symbol labels. |
| `recognize_speech(self, wavsignal, fs)` | Extract features from an in-memory WAV signal and return decoded pinyin tokens. |
| `recognize_speech_from_file(self, filename)` | Read one WAV file and return decoded pinyin tokens. |
| `load_model(self, filename)` | Load Keras acoustic weights. |
| `save_model(self, filename)` | Save Keras acoustic weights. |
| `model` property | Return the training Keras model. |

The verified source signature for training is:

```python
ModelSpeech.train_model(self, optimizer, data_loader, epochs=1, save_step=1, batch_size=16, last_epoch=0, call_back=None)
```

## Default Keras training recipe

The repository training script sets `CUDA_VISIBLE_DEVICES="0"`, constructs `SpeechModel251BN` with default ASRT dimensions, uses `SpecAugment`, loads `DataLoader('train')`, and trains with Adam:

```python
from tensorflow.keras.optimizers import Adam
from speech_model import ModelSpeech
from model_zoo.speech_model.keras_backend import SpeechModel251BN
from data_loader import DataLoader
from speech_features import SpecAugment

AUDIO_LENGTH = 1600
AUDIO_FEATURE_LENGTH = 200
CHANNELS = 1
OUTPUT_SIZE = 1428

sm251bn = SpeechModel251BN(
    input_shape=(AUDIO_LENGTH, AUDIO_FEATURE_LENGTH, CHANNELS),
    output_size=OUTPUT_SIZE,
)
feat = SpecAugment()
train_data = DataLoader('train')
opt = Adam(learning_rate=0.0001, beta_1=0.9, beta_2=0.999, decay=0.0, epsilon=10e-8)
ms = ModelSpeech(sm251bn, feat, max_label_length=64)
ms.train_model(optimizer=opt, data_loader=train_data,
               epochs=50, save_step=1, batch_size=16, last_epoch=0)
ms.save_model('save_models/' + sm251bn.get_model_name())
```

Operational notes:

- Dataset availability, `asrt_config.json`, pinyin dictionary, and datalist correctness must be handled before training.
- The README's minimum training guidance is Linux, 16 GB+ RAM, NVIDIA GPU with around 11 GB+ graphics memory, large dataset storage, Python 3.9+, and TensorFlow 2.5-2.11+. Treat GPU as expected for normal training; CUDA training is optional/unverified in this not-import build.
- The repository code uses `fit_generator`, which is deprecated in modern Keras but remains the source implementation. If a target TensorFlow version removes it, try `model.fit(generator, steps_per_epoch=...)` in a local adaptation rather than changing the runtime skill.

## Save layout and weight filenames

`ModelSpeech.train_model` builds a default save prefix:

```python
save_filename = os.path.join('save_models', model_name, model_name)
```

At each `save_step`, it calls:

```python
self.save_model(save_filename + '_epoch' + str(epoch))
```

`BaseModel.save_weights(prefix)` then writes:

- `prefix + '.model.h5'`: training model weights.
- `prefix + '.model.base.h5'`: base/inference model weights.
- `epoch_<model_name>.txt`: a marker file containing the prefix string.

For `SpeechModel251BN` epoch 1, default files are therefore similar to:

- `save_models/SpeechModel251bn/SpeechModel251bn_epoch1.model.h5`
- `save_models/SpeechModel251bn/SpeechModel251bn_epoch1.model.base.h5`

A final `ms.save_model('save_models/' + sm251bn.get_model_name())` writes:

- `save_models/SpeechModel251bn.model.h5`
- `save_models/SpeechModel251bn.model.base.h5`

## Resume from weights

The source training script includes a commented resume line:

```python
ms.load_model('save_models/' + sm251bn.get_model_name() + '.model.h5')
```

For a specific epoch checkpoint, load the `.model.h5` training-model file and set `last_epoch` so saved epoch numbers continue monotonically:

```python
ms.load_model('save_models/SpeechModel251bn/SpeechModel251bn_epoch10.model.h5')
ms.train_model(optimizer=opt, data_loader=train_data,
               epochs=10, save_step=1, batch_size=16, last_epoch=10)
```

Do not pass a prefix without `.model.h5` to `load_model`; `load_model` directly forwards the filename to Keras `load_weights`.

## Evaluate with weights

The default evaluation script constructs the same `SpeechModel251BN`, uses `Spectrogram`, creates `DataLoader('dev')`, loads `save_models/<model_name>.model.h5`, and calls:

```python
ms.evaluate_model(data_loader=evalue_data, data_count=-1,
                  out_report=True, show_ratio=True, show_per_step=100)
```

Evaluation behavior to account for:

- `data_count <= 0` means evaluate the whole selected split.
- With `out_report=True`, a `Test_Report_<dataset_type>_<timestamp>.txt` file is written in the current working directory.
- Samples whose extracted feature length exceeds `speech_model.input_shape[0]` are printed as too long and skipped.
- The printed ratio is over pinyin-symbol labels, not the final pinyin-to-Chinese text conversion.
- No accuracy or benchmark number should be claimed unless the active run supplies the exact weights, dataset split, and report.

## Source script inventory

- `train_speech_model.py`: reference/adapt only. It hard-codes GPU selection, default dimensions, `DataLoader('train')`, a long 50-epoch run, and default save paths.
- `evaluate_speech_model.py`: reference/adapt only. It hard-codes GPU selection, `DataLoader('dev')`, default `SpeechModel251BN`, and `save_models/<model_name>.model.h5`.
- `predict_speech_file.py`: adapted into `scripts/predict_file_template.py` for the acoustic half only. The source script hard-codes `filename.wav`, default weights, GPU selection, and then routes into the language model.
- `scripts/inspect_keras_model.py`: new safe inspection helper; it constructs a selected Keras model without data or weights.

## Resume/evaluate with only base weights

The repository's `load_model` targets the training model (`.model.h5`), even though inference and `evaluate_model` predictions use the base graph. If only a `.model.base.h5` file is available:

1. Construct the same Keras acoustic class and feature extractor.
2. Construct `ModelSpeech` as usual so evaluation/prediction helpers are available.
3. Load the base model directly through the acoustic instance:
   ```python
   sm251bn.get_eval_model().load_weights('SpeechModel251bn.model.base.h5')
   ```
4. Use `ms.evaluate_model(...)`, `ms.recognize_speech(...)`, or `ms.recognize_speech_from_file(...)` for evaluation/prediction.
5. Do not expect `train_model` resume to work from a base-only weight file; it lacks the training graph's CTC input/loss weight layout.

This is a useful hard usability case because released inference bundles may include base weights while training-resume code expects `.model.h5`.
