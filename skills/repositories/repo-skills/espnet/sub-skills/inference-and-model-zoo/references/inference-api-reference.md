# ESPnet Inference API Reference

ESPnet inference entrypoints live under `espnet2.bin` and usually expose a class plus a CLI. Local inference requires a matching training config and model checkpoint. Pretrained inference usually calls `from_pretrained(model_tag=...)`, which may download or read cached models.

| Workflow | Class/module | Key local inputs |
| --- | --- | --- |
| ASR | `espnet2.bin.asr_inference.Speech2Text` | `asr_train_config`, `asr_model_file`, optional LM/ngram, `device`, `beam_size`, `ctc_weight`, `lm_weight`, `nbest` |
| Streaming ASR | `asr_inference_streaming.Speech2TextStreaming` | ASR config/model plus streaming controls |
| ASR transducer | `asr_transducer_inference` | Transducer model/config and decoding options |
| TTS/TTS2 | `tts_inference.Text2Speech`, `tts2_inference.Text2Speech` | `train_config`, `model_file`, optional `vocoder_config`, `vocoder_file`, `vocoder_tag`, `speed_control_alpha`, `seed`, `device` |
| Enhancement/separation | `enh_inference.SeparateSpeech` | `train_config`, `model_file`, optional `inference_config`, segment/hop/ref-channel/output normalization |
| ST/S2T/S2ST | `st_inference.Speech2Text`, `s2t_inference.Speech2Text`, `s2st_inference.Speech2Speech` | task config/model, beam/LM/token options, vocoder for speech-to-speech output |
| SLU | `slu_inference.Speech2Understand` | task config/model and text/audio decoding options |
| Speaker | `spk_inference.Speech2Embedding` | embedding config/model, output format and device |
| Diarization | `diar_inference.DiarizeSpeech` | diar config/model and segmentation options |
| SVS | `svs_inference.SingingGenerate` | singing voice synthesis config/model plus vocoder if needed |

## Safe inspection

Use the bundled inspector to see constructor signatures without loading weights or downloading models:

```bash
python sub-skills/inference-and-model-zoo/scripts/inspect_inference_entrypoints.py --task asr --json
```

## Local file validation

Before loading weights, validate paths with:

```bash
python sub-skills/inference-and-model-zoo/scripts/check_model_files.py --task asr --config train.yaml --model valid.acc.ave.pth
```

This only checks file presence; it does not prove config/model compatibility.
