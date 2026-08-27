# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `PaddleCV(task_name=...)` fails before inference | The task name is not in the packaged catalog. | Call `PaddleCV.list_all_supported_tasks()` and use the exact task string. |
| OCR or table workflows fail to render text or tables | Missing fonts or dicts in the PaddleCV cache. | Check the `~/.cache/paddlecv/fonts` and `~/.cache/paddlecv/dicts` directories. |
| `paddlenlp` import fails on `aistudio_sdk.hub.download` | The installed `aistudio-sdk` release does not export the helper expected by the NLP stack. | Install a compatible `aistudio-sdk` release and retry. |
| `paddlespeech` import or TTS preset fails | The speech stack is missing a dependency or has a version conflict. | Reinstall the speech stack with compatible `urllib3`, `paddlespeech`, and `ppdiffusers` versions. |
| Retrieval or ShiTu workflow errors around `faiss` | The environment lacks a compatible `faiss` wheel. | Use a Python/platform combination that has a matching `faiss` build. |

## Recovery checklist
1. Run `scripts/smoke_import.py`.
2. Confirm the task name with `PaddleCV.list_all_supported_tasks()`.
3. Recheck the cache directories for configs, fonts, and dicts.
4. Reinstall the dependency that matches the import error.
