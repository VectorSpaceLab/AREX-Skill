# Python Pipeline Troubleshooting

## Model loading

| Symptom | Cause | Fix |
| --- | --- | --- |
| `config.json not found in LTP/small` | Cache miss, network failure, wrong model id, or offline mode. | Use a local model path, allow network once to populate cache, or remove `local_files_only=True` only with permission. |
| Local path loads the wrong implementation | `config.json` selects neural vs legacy. | Inspect the model config and route neural tasks or legacy tasks accordingly. |
| Private model fails with authorization error | Missing/invalid Hugging Face token. | Pass `token` from secure runtime configuration; never write it into scripts. |
| Download is slow or blocked | Network/mirror/proxy issue. | Use a pre-downloaded model directory or configure the network outside the skill. |

## Task and input errors

| Symptom | Cause | Fix |
| --- | --- | --- |
| `Unsupported tasks` | The selected model does not support one or more requested tasks. | Use a neural model for full tasks; legacy only supports `cws`, `pos`, `ner`. |
| NER output missing or wrong with legacy | POS was not produced/provided. | Request `['cws', 'pos', 'ner']` or pass words/POS from earlier calls. |
| POS/NER over raw strings is malformed | `cws` omitted from tasks, so input was treated as pretokenized. | Include `cws` or pass `List[List[str]]` words. |
| Tuple unpacking fails | `LTPOutput` is not directly unpackable. | Call `.to_tuple()` or pass `return_dict=False`. |

## CUDA issues

| Symptom | Cause | Fix |
| --- | --- | --- |
| `.to("cuda")` fails | Torch CUDA build, driver, or memory problem. | Run the root `check_ltp_install.py --check-cuda` probe and a tiny allocation before moving the model. |
| CPU results are slower than expected | Model is running on CPU. | Verify `torch.cuda.is_available()`, then call `ltp.to("cuda")` if GPU use is required. |
| Out-of-memory during batch inference | Batch too large or model too large. | Reduce batch size, use a smaller model, split long sentences, or return to CPU only if acceptable. |

## Output conversion issues

| Symptom | Cause | Fix |
| --- | --- | --- |
| CoNLL-U converter complains about missing `cws` | JSON does not contain word segmentation output. | Save pipeline output with at least `cws`; `pos` and `dep` improve rows but can be missing. |
| Dependency head lengths do not match words | Mixed outputs from different sentences/task calls. | Keep each sentence's `cws`, `pos`, `dep`, and `sdpg` together by batch index. |
| Entity offsets do not match original text | Word-index spans were mistaken for character offsets. | Reconstruct character offsets from `cws` and original sentence text. |

## Service integration issues

- If `fastapi` or `uvicorn` imports fail, install service dependencies separately; they are not required for basic LTP inference.
- Validate user-supplied task names and reject arbitrary local model paths in public APIs.
- If startup downloads a model and blocks the service, preload/cache the model during deployment or require a local model directory.
