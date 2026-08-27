# Loading Workflows

This reference is the operating guide for loading the HFL Chinese BERT-wwm family through Hugging Face Transformers or PaddleHub, and for recognizing when a downloaded zip is a TensorFlow checkpoint rather than a ready Hugging Face/PyTorch directory.

## Non-negotiable class choice

All models in this repository's quick-load contract are loaded as BERT-family models:

```python
from transformers import BertTokenizer, BertModel

tokenizer = BertTokenizer.from_pretrained("hfl/chinese-roberta-wwm-ext")
model = BertModel.from_pretrained("hfl/chinese-roberta-wwm-ext")
```

`AutoTokenizer` and `AutoModel` are also acceptable when you want Transformers to read the config and choose the class:

```python
from transformers import AutoTokenizer, AutoModel

tokenizer = AutoTokenizer.from_pretrained("hfl/chinese-roberta-wwm-ext")
model = AutoModel.from_pretrained("hfl/chinese-roberta-wwm-ext")
```

Do **not** use `RobertaTokenizer` or `RobertaModel` for `hfl/chinese-roberta-wwm-ext` or `hfl/chinese-roberta-wwm-ext-large`. The public names are RoBERTa-like, but the repository explicitly says every listed model uses `BertTokenizer` and `BertModel`.

## Hugging Face model ids

| Human name | Hugging Face `MODEL_NAME` | README source | Notes |
| --- | --- | --- | --- |
| RoBERTa-wwm-ext-large | `hfl/chinese-roberta-wwm-ext-large` | Download table and quick-load table | Large model; use BERT classes. |
| RoBERTa-wwm-ext | `hfl/chinese-roberta-wwm-ext` | Download table and quick-load table | Base-size RoBERTa-wwm-ext; use BERT classes. |
| BERT-wwm-ext | `hfl/chinese-bert-wwm-ext` | Download table and quick-load table | Extended-data BERT-wwm. |
| BERT-wwm | `hfl/chinese-bert-wwm` | Download table and quick-load table | Chinese Wikipedia BERT-wwm. |
| RBT3 | `hfl/rbt3` | Download table and quick-load table | Small 3-layer model. |
| RBT4 | `hfl/rbt4` | Chinese and English download tables | The quick-load tables omit this id; it is still present in the download tables. |
| RBT6 | `hfl/rbt6` | Chinese and English download tables | The quick-load tables omit this id; it is still present in the download tables. |
| RBTL3 | `hfl/rbtl3` | Download table and quick-load table | 3-layer large-family distilled/truncated small model. |

Use the exact lowercase `hfl/...` id when calling `from_pretrained`.

## Transformers loading modes

### 1. Offline-safe validation only

Use this when you need to check a model id, verify that Transformers is importable, or probe an existing cache without starting a download:

```bash
python scripts/check_transformers_model.py hfl/rbt3 --try-load-tokenizer --offline-only
```

Equivalent code pattern:

```python
from transformers import BertTokenizer

tokenizer = BertTokenizer.from_pretrained(
    "hfl/rbt3",
    local_files_only=True,
)
```

A cache miss in this mode is not proof that the id is wrong. It only means the required files are not already present in the local Hugging Face cache or the supplied `cache_dir`.

### 2. Explicit online Hugging Face download

Use this only after deciding that network access and checkpoint downloads are acceptable:

```bash
python scripts/check_transformers_model.py hfl/chinese-bert-wwm --try-load-tokenizer --allow-download
```

Equivalent code pattern:

```python
from transformers import BertTokenizer, BertModel

tokenizer = BertTokenizer.from_pretrained("hfl/chinese-bert-wwm")
model = BertModel.from_pretrained("hfl/chinese-bert-wwm")
```

Online model materialization may need Hugging Face Hub access, proxy configuration, disk space for checkpoint files, and optional credentials if the user has customized Hub settings. These public HFL ids are normally public, but local network policy can still block them.

### 3. Explicit cache directory

Use `cache_dir` when a workflow is tied to a shared cache or a pre-populated offline cache:

```bash
python scripts/check_transformers_model.py hfl/chinese-roberta-wwm-ext \
  --cache-dir HF_CACHE_DIR \
  --try-load-config \
  --try-load-tokenizer \
  --offline-only
```

Equivalent code pattern:

```python
from transformers import AutoTokenizer, AutoModel

tokenizer = AutoTokenizer.from_pretrained(
    "hfl/chinese-roberta-wwm-ext",
    cache_dir="HF_CACHE_DIR",
    local_files_only=True,
)
model = AutoModel.from_pretrained(
    "hfl/chinese-roberta-wwm-ext",
    cache_dir="HF_CACHE_DIR",
    local_files_only=True,
)
```

Do not hard-code local cache paths in reusable runtime instructions. Ask the user for the cache path or use the active environment's default cache.

### 4. Local directory loading

If the user already has a directory containing Hugging Face files, call `from_pretrained` on that directory. The directory must match the framework path:

- Hugging Face/PyTorch path: typically includes config/tokenizer files and PyTorch weights such as `pytorch_model.bin` or supported safer weight files.
- TensorFlow checkpoint zip path: contains TensorFlow checkpoint files and is not the same as a ready PyTorch/Hugging Face directory unless converted or loaded with an appropriate TensorFlow-aware workflow.

Prefer a model id plus cache settings unless the user has a known local checkpoint directory.

## TensorFlow zip versus Hugging Face/PyTorch files

The repository's download notes describe TensorFlow zip packages. A TensorFlow zip extraction for `BERT-wwm, Chinese` is shown with this layout:

```text
chinese_wwm_L-12_H-768_A-12.zip
  |- bert_model.ckpt
  |- bert_model.meta
  |- bert_model.index
  |- bert_config.json
  |- vocab.txt
```

The repository notes that `bert_config.json` and `vocab.txt` match the original Google `BERT-base, Chinese` files. It also distinguishes this from PyTorch/Hugging Face files: PyTorch versions include `pytorch_model.bin`, `bert_config.json`, and `vocab.txt`, or can be obtained from the HFL Hugging Face model pages.

Implications:

- Do not point `BertModel.from_pretrained` at an arbitrary zip file.
- Do not expect a TensorFlow checkpoint zip to contain `pytorch_model.bin`.
- If the user needs PyTorch weights from the TensorFlow checkpoint, use a Transformers conversion workflow or obtain the Hugging Face files directly.
- If the user needs TensorFlow 2, the README says all models support TensorFlow 2 through Transformers or download from the HFL Hugging Face organization, but this sub-skill's verified environment only inspected Transformers/PyTorch imports.

## PaddleHub module mapping

PaddleHub loading uses a module name, not the Hugging Face `hfl/...` id:

```python
import paddlehub as hub
module = hub.Module(name="chinese-bert-wwm")
```

| Human name | PaddleHub `MODULE_NAME` | Notes |
| --- | --- | --- |
| RoBERTa-wwm-ext-large | `chinese-roberta-wwm-ext-large` | Quick-load table entry. |
| RoBERTa-wwm-ext | `chinese-roberta-wwm-ext` | Quick-load table entry. |
| BERT-wwm-ext | `chinese-bert-wwm-ext` | Quick-load table entry. |
| BERT-wwm | `chinese-bert-wwm` | Quick-load table entry. |
| RBT3 | `rbt3` | Quick-load table entry. |
| RBTL3 | `rbtl3` | Quick-load table entry. |
| RBT4 | not listed in the quick-load PaddleHub table | The README download table lists `hfl/rbt4` for Hugging Face, but does not provide a PaddleHub quick-load module name. |
| RBT6 | not listed in the quick-load PaddleHub table | The README download table lists `hfl/rbt6` for Hugging Face, but does not provide a PaddleHub quick-load module name. |

PaddleHub caveats:

- `paddlehub` and `paddlepaddle` are optional dependencies for this repo skill and were not part of the minimum verified environment.
- `hub.Module(name=...)` may download module assets unless the PaddleHub cache already contains them.
- Network, proxy, and disk-space constraints should be decided before running PaddleHub loading.
- If the user only needs to choose a model id or use Transformers, do not install the Paddle stack just to validate this sub-skill.

## Decision checklist

Before writing loading code, answer these questions:

1. Which surface is required: Transformers, PaddleHub, TensorFlow checkpoint files, or already-downloaded Hugging Face directory?
2. Which exact model id/module name maps to the user's intended model?
3. Is the run offline-only, cache-only, or allowed to download?
4. If using Transformers, are BERT classes or `Auto*` classes used instead of RoBERTa classes?
5. Is the user trying to fine-tune or select a model for a task? If so, route to `../task-selection-and-finetuning/SKILL.md` after the loading surface is resolved.
