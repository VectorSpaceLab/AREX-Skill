# API Reference

This reference records the public loading APIs and installed-package facts verified for the generated repo skill. Use it to write precise loading code and to avoid class-name mistakes.

## Verified environment facts

The inspection environment used during skill construction verified:

- `transformers` version: `5.15.0`.
- `torch` version: `2.13.0`.
- `torch.cuda` smoke passed on the construction host, but GPU is optional and not required for tokenization or CPU model loading.
- Imports succeeded for:
  - `transformers.BertTokenizer`
  - `transformers.BertModel`
  - `transformers.AutoTokenizer`
  - `transformers.AutoModel`
  - `transformers.BertConfig`

Do not assume PaddleHub/PaddlePaddle is installed from these facts; PaddleHub is documented as an optional alternate loading path.

## Recommended Transformers classes

### Explicit BERT classes

Use these when following the repository's quick-load instructions exactly:

```python
from transformers import BertTokenizer, BertModel

tokenizer = BertTokenizer.from_pretrained("hfl/chinese-bert-wwm")
model = BertModel.from_pretrained("hfl/chinese-bert-wwm")
```

The repository explicitly states that all listed models, including names containing `RoBERTa`, should use `BertTokenizer` and `BertModel`, not `RobertaTokenizer` or `RobertaModel`.

### Auto classes

Use these when you want Transformers to select the implementation from the downloaded config:

```python
from transformers import AutoTokenizer, AutoModel

tokenizer = AutoTokenizer.from_pretrained("hfl/chinese-roberta-wwm-ext")
model = AutoModel.from_pretrained("hfl/chinese-roberta-wwm-ext")
```

Auto classes are useful in generalized code, but they still rely on the same cache/network/local-directory decisions as explicit BERT classes.

## Verified signatures

The installed-package inspection verified these signatures for the two core APIs.

### `BertTokenizer.from_pretrained`

```text
(pretrained_model_name_or_path: 'str | os.PathLike', *init_inputs, cache_dir: 'str | os.PathLike | None' = None, force_download: 'bool' = False, local_files_only: 'bool' = False, token: 'str | bool | None' = None, revision: 'str' = 'main', trust_remote_code=False, **kwargs)
```

Important parameters for this repo skill:

| Parameter | Use |
| --- | --- |
| `pretrained_model_name_or_path` | Exact `hfl/...` id or a local Hugging Face-format directory. |
| `cache_dir` | Optional explicit Hugging Face cache directory. Do not hard-code a local path in reusable instructions. |
| `force_download` | Leave `False` unless deliberately refreshing a cache. |
| `local_files_only` | Set `True` for offline/cache-only operation. This is the safest default for validation. |
| `token` | Optional Hugging Face token; normally unnecessary for public HFL ids, but local Hub policy may require it. |
| `revision` | Usually `main`; set only when the user needs a specific model revision. |
| `trust_remote_code` | Keep `False` for these standard BERT-family models unless the user has a separate reason. |

### `BertModel.from_pretrained`

```text
(pretrained_model_name_or_path: str | os.PathLike | None, *model_args, config: transformers.configuration_utils.PreTrainedConfig | str | os.PathLike | None = None, cache_dir: str | os.PathLike | None = None, ignore_mismatched_sizes: bool = False, force_download: bool = False, local_files_only: bool = False, token: str | bool | None = None, revision: str = 'main', use_safetensors: bool | None = None, weights_only: bool = True, fusion_config: dict[str, bool | dict[str, typing.Any]] | None = None, disable_mmap: bool | None = None, **kwargs) -> ~SpecificPreTrainedModelType
```

Important parameters for this repo skill:

| Parameter | Use |
| --- | --- |
| `pretrained_model_name_or_path` | Exact `hfl/...` id or local Hugging Face-format directory. |
| `config` | Optional explicit config; not needed for normal `hfl/...` loads. |
| `cache_dir` | Same cache-control role as tokenizer loading. |
| `ignore_mismatched_sizes` | Keep `False` unless intentionally adapting heads or architectures; not needed for base encoder loading. |
| `force_download` | Leave `False` unless deliberately re-downloading. |
| `local_files_only` | Set `True` for offline/cache-only operation. |
| `token` | Optional Hugging Face token; normally unnecessary for public HFL ids. |
| `revision` | Usually `main`. |
| `use_safetensors` | Optional format preference depending on files available in the model repo/cache. |
| `weights_only` | Verified default is `True` in the inspected Transformers build. |

## Local/offline helper API

The bundled helper exposes a command-line interface rather than an import contract:

```bash
python scripts/check_transformers_model.py --help
```

Core arguments:

| Argument | Effect |
| --- | --- |
| positional `MODEL_ID` | Optional model id, e.g. `hfl/rbt3`. |
| `--model-id MODEL_ID` | Alternative named model-id argument; useful in scripts. |
| `--offline-only` | Forces `local_files_only=True`; this is the default. |
| `--allow-download` | Allows network access in requested `from_pretrained` calls. |
| `--cache-dir PATH` | Passes an explicit cache directory into `from_pretrained`. |
| `--try-load-config` | Attempts `AutoConfig.from_pretrained`. |
| `--try-load-tokenizer` | Attempts `BertTokenizer.from_pretrained`. |
| `--try-load-model` | Attempts `BertModel.from_pretrained`; may require substantial memory and cached/downloaded weights. |
| `--use-auto` | Uses `AutoTokenizer`/`AutoModel` for requested tokenizer/model loads instead of explicit BERT classes. |
| `--list-models` | Prints the bundled model map and exits. |

Default behavior validates the model id and imports Transformers classes without downloading or loading checkpoint files. Add `--try-load-*` flags for cache/materialization checks.

## PaddleHub public surface

The README quick-load pattern is:

```python
import paddlehub as hub
module = hub.Module(name="MODULE_NAME")
```

Use the module-name table in `loading-workflows.md`. PaddleHub/PaddlePaddle were not installed in the verified minimum environment, so treat PaddleHub loading as optional and potentially network/cache dependent.

## Public API choices by task

| User intent | Preferred API |
| --- | --- |
| Follow README exactly for encoder loading | `BertTokenizer.from_pretrained`, `BertModel.from_pretrained`. |
| Generic Transformers code | `AutoTokenizer.from_pretrained`, `AutoModel.from_pretrained`. |
| Offline id/import validation | `scripts/check_transformers_model.py MODEL_ID` with no `--allow-download`. |
| Offline cache check | `scripts/check_transformers_model.py MODEL_ID --try-load-tokenizer --offline-only [--cache-dir PATH]`. |
| Full checkpoint materialization | Explicit online/cache-approved `from_pretrained`; consider memory and disk needs. |
| PaddleHub module loading | `paddlehub.Module(name=MODULE_NAME)` after confirming optional dependencies/network/cache. |
| Fine-tuning classifier/QA/NER heads | Route to `../task-selection-and-finetuning/SKILL.md`; this sub-skill covers base loading choices only. |
