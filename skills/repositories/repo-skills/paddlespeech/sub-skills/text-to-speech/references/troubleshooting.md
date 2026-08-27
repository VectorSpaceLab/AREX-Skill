# TTS Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Resource lookup fails for AM/VOC | Incompatible `--am`, `--voc`, or `--lang` tag. | Check model combinations and use matching dataset/language families. |
| Missing `phones_dict`, `tones_dict`, `speaker_dict`, or stats | Custom model run omitted required resources. | Provide the full config/checkpoint/stat/dictionary set, or use pretrained defaults. |
| English text in `.job` fails to parse | Shared job parser splits on whitespace. | Use direct quoted `--input`, or only use job files for whitespace-free text values. |
| Output file missing or unreadable | Invalid output path, permission issue, or synthesis failed before write. | Use a writable `.wav` path and inspect CLI stderr/logs. |
| ONNX run fails | Unsupported model combo, missing ONNX model, or onnxruntime mismatch. | Use supported ONNX tags/files and verify `onnxruntime` import. |
| Multi-speaker result wrong voice | Missing or wrong `--spk_id` / speaker map. | Verify model is multi-speaker and select a valid speaker id. |
| Cantonese or mixed text fails | Wrong `--lang` or frontend assets missing. | Use `--lang canton` for Cantonese FastSpeech2, `--lang mix` for mixed Chinese-English model, and ensure tone/phone resources exist. |
