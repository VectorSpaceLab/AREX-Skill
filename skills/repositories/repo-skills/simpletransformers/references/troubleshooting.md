# Cross-cutting Troubleshooting

## Import/version failures

If `import simpletransformers` works but task model imports fail, check package versions first:

```bash
python -m pip show simpletransformers transformers torch
python scripts/check_simpletransformers_env.py --modules classification ner qa generation seq2seq t5 retrieval representation convai
```

Known Simple Transformers 0.70.8 hazards include missing `SequenceSummary` aliases, removed `TransfoXLConfig`, and removed top-level `cached_path` in modern Transformers. Resolve dependency compatibility or refresh the repository skill before treating user data as invalid.

## Missing PyTorch

The source imports `torch` in model modules, while package metadata does not list `torch` directly. Install a CPU or CUDA PyTorch build suitable for the user's platform before importing task models.

## CUDA errors

Constructors default to `use_cuda=True`. For CPU environments, pass `use_cuda=False`. For GPU runs, verify:

```python
import torch
print(torch.cuda.is_available())
```

Do not count a CPU-only PyTorch import as GPU verification.

## Downloads and offline environments

Public model names such as `bert-base-uncased` download from Hugging Face unless cached. In offline tasks, require local model paths or pre-populated cache and avoid examples that silently download datasets.

## Output/cache side effects

Training can create `outputs/`, `cache_dir/`, `runs/`, and WandB artifacts. Use `no_save=True` for smoke runs and explicit output/cache directories for production.

## Multiprocessing hangs

If preprocessing hangs or fails on constrained hosts, disable multiprocessing with `use_multiprocessing=False` and `use_multiprocessing_for_evaluation=False`.

## Optional dependencies

ONNX export, FAISS indexes, BEIR evaluation, pytrec metrics, Streamlit serving, and WandB tracking each need additional runtime permissions or packages. Install them only when the selected workflow needs them.
