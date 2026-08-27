# Speech-to-Text Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| ASR raises invalid sample rate | Input sample rate does not match model. | Resample intentionally, use `--yes`, or choose a matching model. |
| ASR fails on long audio | Model max duration limit or memory. | Split audio into shorter segments before recognition. |
| `codeswitch is true only in zh_en model` | `--codeswitch True` with non-`zh_en` language. | Use TALCS code-switch tags with `--lang zh_en`, or disable code-switch. |
| ST cannot find `compute-fbank-feats` or `compute-kaldi-pitch-feats` | Kaldi bins not downloaded or not on runtime path. | Let ST fetch its bins or install/provide compatible Kaldi tools explicitly. |
| Whisper model is slow or huge | Large model size chosen. | Start with `tiny` or `base`; confirm cache/disk before `large` or `medium`. |
| `stats --task ssl/whisper` fails | Registry display caveat in this checkout. | Use `paddlespeech ssl --help`, `paddlespeech whisper --help`, and direct command references. |
| Piped ASR-to-punctuation fails | ASR emitted logs/errors or punctuation input cleaned to empty string. | Run ASR and text punctuation as separate steps and inspect raw transcript. |
