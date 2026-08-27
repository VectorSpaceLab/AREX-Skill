# Model-Loading Troubleshooting

Use this matrix for failures that are specific to HFL Chinese BERT-wwm family loading. For broad package installation, proxy, disk, and shared cache policy issues, also consult the root troubleshooting reference.

## Quick triage

1. Confirm the exact id is in the bundled map: `hfl/chinese-roberta-wwm-ext-large`, `hfl/chinese-roberta-wwm-ext`, `hfl/chinese-bert-wwm-ext`, `hfl/chinese-bert-wwm`, `hfl/rbt3`, `hfl/rbt4`, `hfl/rbt6`, or `hfl/rbtl3`.
2. Confirm the loading surface: Transformers, PaddleHub, TensorFlow checkpoint files, or local Hugging Face directory.
3. Confirm whether downloads are allowed. If not, use `local_files_only=True` or the bundled checker default.
4. Confirm the class choice. For Transformers, use BERT classes or `Auto*`, not RoBERTa classes.

## `RobertaTokenizer` or `RobertaModel` misuse

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| User code uses `RobertaTokenizer.from_pretrained("hfl/chinese-roberta-wwm-ext")`. | The model name contains `RoBERTa`, but the repository's quick-load contract says all listed Chinese models use `BertTokenizer` and `BertModel`. | Replace with `BertTokenizer.from_pretrained(...)` and `BertModel.from_pretrained(...)`, or use `AutoTokenizer`/`AutoModel`. |
| Tokenizer complains about missing RoBERTa vocab/merges files. | RoBERTa tokenizer classes expect a different tokenization asset layout than the BERT vocab used by these models. | Use BERT tokenizer classes. Do not try to fabricate RoBERTa merges files. |
| Model config/class mismatch warnings after forcing RoBERTa classes. | The checkpoint/config is BERT-compatible despite a RoBERTa-like display name. | Recreate the model with `BertModel` or `AutoModel`; avoid class override. |

Minimal corrected code:

```python
from transformers import BertTokenizer, BertModel

tokenizer = BertTokenizer.from_pretrained("hfl/chinese-roberta-wwm-ext")
model = BertModel.from_pretrained("hfl/chinese-roberta-wwm-ext")
```

## Missing Transformers or backend framework

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'transformers'`. | Transformers is not installed in the active Python environment. | Install/activate an environment containing `transformers`, then run `python -c "import transformers; print(transformers.__version__)"`. |
| Transformers imports but model loading fails with no PyTorch/TensorFlow/Flax backend. | Tokenizer/config can work without a model backend, but `BertModel` materialization needs a supported framework. | Install a suitable backend such as PyTorch for `BertModel`, or limit the operation to tokenizer/config validation. |
| CUDA is unavailable. | GPU is optional for this repo skill. | Use CPU for validation/tokenization/small inference; only pursue GPU setup for user-requested acceleration or fine-tuning. |

The construction environment verified `transformers 5.15.0` and `torch 2.13.0`; those are facts, not strict minimum version pins for every user workflow.

## Offline/cache miss with `local_files_only=True`

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Error says files cannot be found locally and outgoing traffic is disabled. | Offline mode is working, but the requested model files are not present in the default cache or provided `cache_dir`. | If downloads are allowed, rerun with explicit online loading. If offline must remain, point `--cache-dir` to a pre-populated Hugging Face cache or copy the correct model directory into the environment. |
| Bundled checker returns nonzero for `--try-load-tokenizer --offline-only`. | Requested load was attempted and the cache lacks tokenizer files. | Treat as cache-miss unless the id is also invalid. Run `python scripts/check_transformers_model.py --list-models` to confirm id validity. |
| User expects validation to download. | The helper is intentionally offline-safe by default. | Add `--allow-download` only when network/checkpoint downloads are approved. |

Recommended cache check:

```bash
python scripts/check_transformers_model.py hfl/rbt3 --try-load-tokenizer --offline-only --cache-dir HF_CACHE_DIR
```

Interpretation:

- Exit 0: id is valid, imports succeeded, and requested cached files loaded.
- Exit 2: id is not in the supported bundled map.
- Other nonzero exit: imports or requested load failed; inspect stderr for cache miss, backend, credentials, or network details.

## Hugging Face Hub credentials, proxy, or network failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Timeout, connection refused, DNS, SSL, or proxy error during `from_pretrained`. | The operation is trying to reach Hugging Face Hub but network/proxy policy is blocking it. | Decide whether online download is allowed. Configure the user's network/proxy outside the skill, or switch to offline cache/local directory mode. |
| Authentication/token-related error. | Local Hugging Face Hub settings or organization policy require a token, even though HFL ids are public. | Pass `token=...` through `from_pretrained` only via the user's secure environment handling; never hard-code credentials. |
| Repeated download or partial-cache corruption. | Interrupted download or forced refresh. | Use a clean cache directory or a deliberate cache refresh. Do not delete shared caches without user approval. |

The bundled helper never sends credentials by default and never downloads unless `--allow-download` is provided.

## TensorFlow checkpoint versus PyTorch/Hugging Face confusion

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Local directory contains `bert_model.ckpt`, `bert_model.meta`, `bert_model.index`, `bert_config.json`, and `vocab.txt`, but no `pytorch_model.bin`. | The user has the TensorFlow checkpoint zip layout from the README. | Use a TensorFlow-aware load/conversion workflow, or obtain Hugging Face/PyTorch files directly. Do not assume this is a PyTorch `from_pretrained` directory. |
| User passes the `.zip` file itself to `from_pretrained`. | `from_pretrained` expects a model id or an extracted model directory, not an arbitrary README zip archive. | Extract and inspect the format first; choose TF conversion or HF direct download. |
| User downloaded from a Baidu/Google TensorFlow link but wants PyTorch. | README distinguishes TensorFlow zip downloads from PyTorch/HF direct files. | Convert with Transformers tooling or download the PyTorch/HF files from the HFL model page/cache. |

## PaddleHub/PaddlePaddle missing or cache issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'paddlehub'` or `paddle`. | PaddleHub/PaddlePaddle are optional and were not installed in the minimum verified environment. | Install PaddleHub/PaddlePaddle only if the user chooses the PaddleHub workflow. Otherwise use Transformers. |
| `hub.Module(name=...)` tries to download. | PaddleHub may need to fetch module assets if not cached. | Confirm network/cache policy before running; use an existing PaddleHub cache if offline. |
| User asks for `rbt4` or `rbt6` PaddleHub module name. | README quick-load PaddleHub table omits RBT4/RBT6. | Use Hugging Face ids `hfl/rbt4` or `hfl/rbt6` if those models are required, or ask the user for an externally verified PaddleHub module if they have one. |

## Invalid id or alias confusion

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `hfl/chinese-roberta-wwm-large` or similar fails validation. | Alias is not one of the README-supported ids. | Use `hfl/chinese-roberta-wwm-ext-large`. |
| Uppercase or display-name string passed to `from_pretrained`, e.g. `RBT3`. | Display names and model ids are different. | Use exact id `hfl/rbt3`. |
| PaddleHub module name passed to Transformers, e.g. `chinese-bert-wwm`. | Transformers expects Hugging Face id or local directory. | Use `hfl/chinese-bert-wwm` for Transformers; use `chinese-bert-wwm` only with PaddleHub. |

## Stop conditions

Stop and ask for a concrete user decision before proceeding when:

- A command would start a network download but the user requested offline/cache-only work.
- A command would install the broad Paddle/PaddleHub stack into an existing user environment.
- A command would delete or rewrite a shared model cache.
- A local checkpoint directory's format is ambiguous and the user has not chosen TensorFlow conversion, Hugging Face direct files, or PaddleHub.
