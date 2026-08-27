# HanLP Troubleshooting

## Import and Install Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'hanlp'` | Native package not installed in the active Python | Install `hanlp`, then run `python scripts/check_hanlp_environment.py`. |
| `ModuleNotFoundError: No module named 'hanlp_restful'` | RESTful client package missing | Install `hanlp-restful` for RESTful workflows; native `hanlp` alone is not the RESTful client package. |
| `ModuleNotFoundError: No module named 'hanlp_common'` or `hanlp_trie` | Plugin/common package missing or broken environment | Reinstall HanLP packages; for editable checkouts install plugin packages before main `hanlp`. |
| Optional TensorFlow, fastText, AMR, or `penman` import errors | Optional extras not installed | Install only the needed extra: `hanlp[tf]`, `hanlp[amr]`, or `hanlp[full]`. |

## Model Download and Cache Failures

Symptoms include connection errors during `hanlp.load`, missing zip files, partial archives, Hugging Face cache errors, or repeated download retries.

1. Confirm whether the task can use RESTful API instead of native local models.
2. If local models are required, set or inspect `HANLP_HOME` and make sure the process can write there.
3. Retry transient downloads.
4. Use `HANLP_URL` only for a compatible HanLP model mirror.
5. For Hugging Face model errors, use `TRANSFORMERS_OFFLINE=1` only when the needed files already exist in the local Hugging Face cache.
6. For offline servers, copy both the HanLP model cache and Hugging Face cache from a machine where the same model loaded successfully.

Do not mark a local inference workflow verified if the model archive has not been downloaded or otherwise made available.

## GPU and Backend Confusion

- `torch.cuda.is_available()` false on a GPU host usually means CPU-only PyTorch, missing driver passthrough, or incompatible wheel.
- Use `CUDA_VISIBLE_DEVICES` or pass `devices=` to `hanlp.load` where the component supports it.
- Use fewer tasks, smaller models, RESTful API, or CPU checks when memory is tight.
- Treat GPU as unverified until an actual GPU-enabled model or framework smoke passes.

## RESTful Service Failures

- `401 Unauthorized`: auth missing, invalid, or not loaded from `HANLP_AUTH`.
- `429 Too Many Requests`: quota/rate limit; retry later or use an authorized service.
- `400 Bad Request`: unsupported language, unsupported tasks, text too long, or invalid input shape.
- `422 Unprocessable Entity`: JSON payload shape or content type is wrong.
- SSL/timeout/network errors: service is unreachable from the current environment.

Use `sub-skills/restful-clients/scripts/restful_payload_preview.py` to inspect payload shape without sending a request.

## Task Key and Output Shape Failures

- RESTful raw text goes under `text`; tokenized sentences go under `tokens` as `list[list[str]]`.
- Native MTL models operate at sentence level; split documents before passing them to local MTL models.
- Task keys may have suffixes such as `tok/fine`, `tok/coarse`, `ner/msra`, or `pos/ctb`.
- `Document.get_by_prefix('ner')` returns the first matching annotation family when exact suffixes vary.
- `Document.to_conll()` requires compatible token and dependency-like fields.

Route detailed output issues to `sub-skills/document-and-data/SKILL.md`.

## Dictionary and Rule Failures

- `Trie.parse` can return overlapping matches; `Trie.parse_longest` and `TrieDict.tokenize` use non-overlapping longest-prefix behavior.
- `dict_force` has higher priority and can force bad tokenization if overused.
- `dict_combine` merges model-predicted tokens and cannot create matches absent from the model output unless the component has enough token pieces.
- For words with spaces or tokenizer-stripped characters, tuple-style dictionary entries can be necessary.
