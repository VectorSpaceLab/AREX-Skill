# ESPnet Model Zoo and Packaging

ESPnet integrates with `espnet_model_zoo`, Hugging Face-hosted ESPnet models, and task-specific `from_pretrained` constructors.

## Pretrained model use

Typical pattern:

```python
from espnet2.bin.asr_inference import Speech2Text
speech2text = Speech2Text.from_pretrained(model_tag="<model-tag>", device="cpu")
```

Do not call `from_pretrained` until the user allows network/cache access or confirms the model is already cached. If offline, ask for local `train_config` and model checkpoint files instead.

## Local model use

Local inference requires task-matched config and model files. Examples:

```python
from espnet2.bin.asr_inference import Speech2Text
speech2text = Speech2Text(asr_train_config="train.yaml", asr_model_file="valid.acc.ave.pth", device="cpu")
```

```python
from espnet2.bin.tts_inference import Text2Speech
text2speech = Text2Speech(train_config="train.yaml", model_file="valid.loss.ave.pth", vocoder_tag=None, device="cpu")
```

## Packaging

`python -m espnet2.bin.pack <task>` creates portable artifacts. Use task-specific config/model flags:

- ASR: `--asr_train_config`, `--asr_model_file`, optional `--lm_train_config`, `--lm_file`.
- ST: `--st_train_config`, `--st_model_file`.
- S2T: `--s2t_train_config`, `--s2t_model_file`.
- TTS, enhancement, diarization, SVS, speaker: usually `--train_config`, `--model_file`.
- S2ST: `--s2st_train_config`, `--s2st_model_file`.

Uploading packed models requires credentials and publication decisions; ask before running upload stages or Hugging Face commands.
