# Single-file acoustic prediction workflow

ASRT single-file prediction loads a Keras acoustic model, extracts spectrogram features from one WAV file, decodes CTC output into pinyin tokens, and optionally passes those pinyin tokens to the language model. This sub-skill covers only the acoustic part.

## Source prediction recipe

The repository `predict_speech_file.py` does the following:

```python
from speech_model import ModelSpeech
from model_zoo.speech_model.keras_backend import SpeechModel251BN
from speech_features import Spectrogram

AUDIO_LENGTH = 1600
AUDIO_FEATURE_LENGTH = 200
CHANNELS = 1
OUTPUT_SIZE = 1428

sm251bn = SpeechModel251BN(
    input_shape=(AUDIO_LENGTH, AUDIO_FEATURE_LENGTH, CHANNELS),
    output_size=OUTPUT_SIZE,
)
feat = Spectrogram()
ms = ModelSpeech(sm251bn, feat, max_label_length=64)
ms.load_model('save_models/' + sm251bn.get_model_name() + '.model.h5')
res = ms.recognize_speech_from_file('filename.wav')
print(res)
```

The original script also instantiates `ModelLanguage` and converts pinyin to Chinese text. Route that part to `language-model`; this acoustic sub-skill stops at pinyin tokens.

## Parameterized bundled template

Use the bundled `scripts/predict_file_template.py` instead of editing a hard-coded source script:

```bash
python scripts/predict_file_template.py \
  --weights /path/to/SpeechModel251bn.model.h5 \
  --wav /path/to/one.wav \
  --model 251bn
```

The template supports model selection, default ASRT dimensions, an optional `--base-weights` path, optional `--cuda-visible-devices`, and a `--dry-run` mode that validates import/setup arguments without loading weights or decoding audio.

## Required runtime pieces

A successful acoustic prediction needs:

- ASRT importable modules: `speech_model`, `model_zoo.speech_model.keras_backend`, `speech_features`, and `utils` helpers.
- A compatible TensorFlow/Keras installation.
- A WAV file readable by ASRT's `read_wav_data` utility.
- A trained acoustic weight file matching the chosen class and dimensions.
- A pinyin dictionary configured through ASRT's config machinery, because `ModelSpeech.recognize_speech` maps decoded indexes to pinyin tokens via `load_pinyin_dict(load_config_file(DEFAULT_CONFIG_FILENAME)['dict_filename'])`.

Dataset training lists are not needed for one-file prediction, but the dictionary/config file still is.

## Weight-file selection

Use `.model.h5` when calling `ms.load_model(...)`, because `ModelSpeech.load_model` forwards to the acoustic model's `load_weights` method:

```python
ms.load_model('save_models/SpeechModel251bn.model.h5')
```

Use `.model.base.h5` only when directly loading the base inference model:

```python
sm251bn.get_eval_model().load_weights('save_models/SpeechModel251bn.model.base.h5')
```

Do not mix model variants. `SpeechModel24`, `SpeechModel25`, `SpeechModel251`, and `SpeechModel251BN` have related but not identical layer layouts and model names.

## Audio and feature constraints

ASRT's default `Spectrogram` extractor expects 16 kHz WAV audio and produces feature arrays with 200 frequency bins. The default acoustic input allows up to 1600 frames, approximately 16 seconds in the README's model description. In evaluation, ASRT explicitly skips samples whose extracted length exceeds `input_shape[0]`; in single-file prediction, check length yourself before calling model forward if you need graceful errors.

For long audio, split into shorter utterances before acoustic prediction. The repository does not provide a diarization or long-form segmentation workflow in the acoustic model code.

## Output contract

`recognize_speech_from_file(filename)` returns a Python list of pinyin-token strings such as `['ni3', 'hao3']` depending on the active dictionary and model output. It does not return Chinese text. Convert pinyin tokens to Chinese text only through the language-model sub-skill.

Without trained weights, a constructed model can still produce outputs from random initialization, but those outputs are not meaningful. Treat missing weights as a setup error for real prediction.
