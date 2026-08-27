# ESPnet Task Surface

## Purpose

Read this to classify an ESPnet request before selecting a sub-skill.

## Major workflows

- **ASR / S2T / UASR / transducer**: recognition, streaming recognition, CTC/attention/transducer decoding, Whisper/OWSM-style variants, language modeling, tokenization, and alignment.
- **TTS / TTS2 / SVS / S2ST**: text-to-speech, text-to-wave, singing voice synthesis, vocoders, speaker/language/style controls, and speech-to-speech translation.
- **Enhancement / separation / diarization / speaker**: denoising, dereverberation, multi-speaker separation, target-speaker enhancement, diarization, embeddings, speaker verification/classification.
- **ST / MT / SLU / LID / CLS / codec / SpeechLM**: translation, spoken language understanding, language identification, classification, codec/semantic units, self-supervised and speech language modeling.
- **ESPnet2 recipes**: Kaldi-style `data/`, `run.sh`, task scripts, stages, feature/audio formatting, tokenization, stats, training, inference, packing, optional upload.
- **ESPnet3 systems**: Hydra/System stages for dataset creation, tokenizer training, stats, training, inference, measurement, publication, and demo packaging.

## Fast routing signals

| Signal | Route |
| --- | --- |
| `pip install`, `ModuleNotFoundError`, `flash_attn`, `pyworld`, `sox`, CUDA availability | `installation-and-diagnostics` |
| `wav.scp`, `segments`, `utt2spk`, `spk2utt`, `run.sh --stage`, `tokenize_text` | `recipes-and-data` |
| `asr_train`, `--print_config`, `--dry_run`, `--optim_conf`, `--init_param`, `--ngpu` | `espnet2-training` |
| `Speech2Text`, `Text2Speech`, `SeparateSpeech`, `from_pretrained`, `model_tag`, `pack.py` | `inference-and-model-zoo` |
| `egs3`, `--stages`, `training_config`, `publication_config`, `demo_config` | `espnet3-workflows` |
| `pytest`, `ci/test_...`, `CONTRIBUTING`, recipe PR, shellcheck, pycodestyle | `development-and-testing` |

## Questions to resolve

Ask about task family, inputs/outputs, backend, model source, safety limits, downloads, data availability, and whether the user is using ESPnet as a package or editing a checkout.
