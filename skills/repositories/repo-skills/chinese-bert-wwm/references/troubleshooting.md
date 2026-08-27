# Root Troubleshooting

## Purpose

Use this cross-cutting troubleshooting guide when a Chinese-BERT-wwm task fails before a specific sub-skill owns it, or when the issue spans loading, model selection, datasets, and reproducibility. Route workflow-specific details to the nearest sub-skill.

## Quick routing table

| Symptom or question | Route first | Why |
| --- | --- | --- |
| `RobertaTokenizer`/`RobertaModel` errors for `hfl/chinese-roberta-wwm-ext` | `sub-skills/model-loading/references/troubleshooting.md` | These are BERT-family checkpoints despite RoBERTa-like names. |
| Hugging Face cache miss, Hub timeout, model-id alias, TensorFlow zip confusion | `sub-skills/model-loading/references/troubleshooting.md` | Loading surface and cache/network policy need to be resolved. |
| Low fine-tuning score, learning-rate choice, CWS misconception, domain shift | `sub-skills/task-selection-and-finetuning/references/troubleshooting.md` | The issue is about task adaptation and reproduction expectations. |
| Missing LCQMC/BQ/THUCNews data, local archive schema failure, CJRC test caveat | `sub-skills/data-and-benchmarks/references/troubleshooting.md` | Dataset availability and schema constraints are data-specific. |
| Python environment does not have Transformers/Torch | This root reference, then `model-loading` | Install/import health is shared setup. |

## Environment and import checks

The repository itself is not installed as a Python package. For Transformers workflows, the user's environment needs `transformers` and a supported backend such as PyTorch, TensorFlow, or Flax for model materialization. Tokenizer/config checks may need less than full model loading, but `BertModel` requires a framework backend.

Run the bundled root checker from this skill directory:

```bash
python scripts/check_chinese_bert_wwm_setup.py --require-transformers
python scripts/check_chinese_bert_wwm_setup.py --json
```

Expected successful setup signals:

- `transformers` imports.
- `BertTokenizer`, `BertModel`, `AutoTokenizer`, `AutoModel`, and `BertConfig` are available.
- A framework backend such as `torch` is installed when the user needs to instantiate `BertModel` weights.

If `transformers` is missing, install it in the user's selected environment. If backend packages are missing, either install a backend appropriate for the user's framework or limit the action to tokenizer/config validation.

## Network, cache, and large artifacts

Hugging Face and PaddleHub model materialization can download hundreds of megabytes of checkpoint files. Decide the mode before running loading code:

- Offline/cache-only: use `local_files_only=True` and optionally a user-supplied cache directory. Treat cache misses as cache-state problems, not invalid ids.
- Online: make the network and disk-space side effects explicit before calling `from_pretrained` or `hub.Module`.
- Local directory: verify whether the directory is a Hugging Face/PyTorch model directory or a TensorFlow checkpoint extraction.

Do not delete shared caches, force re-downloads, or pass credentials without a user decision.

## Model class and checkpoint-format pitfalls

- All listed HFL Chinese BERT-wwm family models should load through BERT classes or `Auto*` classes, not RoBERTa classes.
- A TensorFlow checkpoint extraction with `bert_model.ckpt`, `bert_model.meta`, `bert_model.index`, `bert_config.json`, and `vocab.txt` is not the same as a PyTorch/Hugging Face directory with weight files for `BertModel.from_pretrained`.
- PaddleHub module names such as `chinese-bert-wwm` are not Hugging Face ids. Transformers ids use the `hfl/...` form.

## Dataset availability and schema pitfalls

Some dataset folders contain only public source pointers because the data is external, copyright-restricted, or too large. Do not create downloaders that bypass these constraints. When the user supplies an included-style archive, use the data sub-skill validator instead of guessing column names:

```bash
python sub-skills/data-and-benchmarks/scripts/validate_dataset_schema.py --task chnsenticorp --archive ARCHIVE.zip --max-rows 100
```

Only ChnSentiCorp, Weibo, and PeopleDaily included-style archives are supported by the bundled validator. Other datasets need task-specific inspection after the user provides a local copy.

## Reproducibility and benchmark expectations

The README reports maximum and average results over 10 runs for many tasks. Maximum values are not guaranteed targets. If a reproduced score is low, investigate:

- Data split and schema mismatch.
- Initial learning rate and batch size.
- Random seed variance.
- Sequence length, truncation, and preprocessing.
- Domain mismatch between pretraining data and the user's task.
- Framework or model-class mismatch during loading.

For model-specific recommendations, route to `sub-skills/task-selection-and-finetuning/SKILL.md`.

## Stop conditions

Stop and ask for a concrete user decision when the next action would:

- Download large checkpoints or datasets.
- Install broad optional stacks such as PaddleHub/PaddlePaddle into an existing user environment.
- Use credentials, private caches, or proxy settings.
- Delete or rewrite a shared model cache.
- Redistribute or scrape copyright-restricted datasets.
- Claim reproduction failure solely because a single run did not reach the README maximum.
