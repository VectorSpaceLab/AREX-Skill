# Flair Troubleshooting

Use this root troubleshooting guide before moving to a narrower sub-skill when a Flair package workflow fails at installation, import, cache/model resolution, device selection, optional dependencies, or cross-workflow routing.

## Install and import failures

Symptoms:

- `ModuleNotFoundError: No module named 'flair'`.
- Importing `flair` fails inside an environment that appears to have PyTorch or Transformers installed.
- `pip check` reports broken requirements.
- A script works in one shell but not another.

Recovery:

```bash
python -m pip install flair
python -m pip check
python - <<'PY'
import flair, torch, transformers
print("flair", flair.__version__)
print("torch", torch.__version__)
print("transformers", transformers.__version__)
print("device", flair.device)
PY
```

If optional static embeddings are required, install only the needed optional packages. Do not install development or documentation dependency stacks unless maintaining the repository rather than using the package.

## Device surprises

Flair chooses its global device when `flair` is imported. If CUDA is available and `FLAIR_DEVICE` is not `cpu`, Flair can default to `cuda:0`.

Fixes:

- For reproducible CPU behavior, set `FLAIR_DEVICE=cpu` before importing `flair`.
- For a selected GPU, set `FLAIR_DEVICE=0` or another CUDA index before import.
- Do not treat a CPU import as proof that CUDA, multi-GPU, ONNX, or provider runtimes work.
- For multi-GPU training, route to [`../sub-skills/training-and-datasets/references/multi-gpu.md`](../sub-skills/training-and-datasets/references/multi-gpu.md) and verify a CUDA-capable PyTorch install plus at least two visible devices.

## Cache and downloads

Named Flair models, embeddings, public datasets, BPEmb resources, Hugging Face transformer resources, and biomedical dictionaries may download if not cached.

Fixes:

```bash
export FLAIR_CACHE_ROOT="./flair-cache"
export TRANSFORMERS_OFFLINE=1   # only when resources are already cached
export HF_HUB_OFFLINE=1
```

Set cache variables before importing `flair`. Use local model/resource paths only when the user supplies them or they are stable project artifacts. Do not bake machine-specific cache paths into reusable scripts or documentation.

If a workflow must be no-download:

- Use `RegexpTagger` and manual labels for annotation checks.
- Use `OneHotEmbeddings` and tiny in-memory dictionaries for embedding checks.
- Use local `ColumnCorpus`/JSONL fixtures instead of public dataset constructors.
- Use the biomedical exact-match in-memory linker instead of built-in biomedical linker/dictionary downloads.

## Optional dependency matrix

| Surface | Optional dependency/resource | Failure symptom | Recovery |
| --- | --- | --- | --- |
| spaCy tokenization | `spacy` plus a named model such as `en_core_web_sm` | `SpacyTokenizer` or `SpacySentenceSplitter` fails | Install/check spaCy model or use SegTok fallback when exact spaCy alignment is not required. |
| biomedical tokenization | `scispacy` plus `en_core_sci_sm` | `SciSpacyTokenizer` / splitter fails | Treat as optional; use SegTok or install compatible SciSpaCy stack. |
| abbreviation resolution | `pyab3p` | HunFlair linker warns and switches to `-no-ab3p`, or `Ab3PEntityPreprocessor` fails | Install `pyab3p` if abbreviation-aware behavior is required; otherwise use `BioSynEntityPreprocessor`. |
| static word vectors | `gensim`, cached vector files | `WordEmbeddings(...)` cannot load/download vectors | Use local vectors, install the extra, or switch to no-download one-hot smoke. |
| byte-pair embeddings | `bpemb` / sentencepiece resources | `BytePairEmbeddings` download/path errors | Provide local model/embedding files or permit BPEmb cache download. |
| transformer optimization | `onnxruntime`, `onnx`, provider packages | export/provider import errors | Keep PyTorch baseline or install exact provider runtime and compare outputs. |
| Japanese tokenization | `konoha` plus selected backend/system packages | tokenizer import/runtime failure | Install backend or treat Japanese tokenization as a blocker, not a silent fallback. |
| OCR/layout models | token `bbox` and sentence `image` metadata, plus upstream OCR/image pipeline | embedding errors about boxes/images | Add required metadata or route OCR/image extraction to another workflow. |

## Label-layer confusion

Symptoms:

- `get_labels()` returns too much.
- NER labels disappear after another prediction.
- Biomedical links overwrite NER spans or appear mixed with NER labels.
- `get_spans("ner")` is empty while `get_labels("ner")` is not.

Fixes:

- Always name the layer: `get_labels("ner")`, `get_spans("ner")`, `get_relations("relation")`.
- Use `label_name="pred_ner"` for prediction when preserving gold/manual labels.
- Use `pred_label_type="gene-link"` / `"disease-link"` for biomedical linkers when outputs must stay separate.
- Remember that `get_labels(layer)` returns labels attached to sentence, token, span, and relation data points. Use `get_spans(layer)` only for span objects.

## Corpus and training errors

Symptoms:

- Empty or unexpected label dictionary.
- Missing split files or sampled splits were not intended.
- `JsonlCorpus` import fails.
- Trainer writes outputs to an unexpected location.
- Training runs out of memory.

Fixes:

- Print the corpus and split lengths before training.
- Call `corpus.make_label_dictionary(label_type=..., add_unk=...)` and inspect items before model construction.
- If `from flair.datasets import JsonlCorpus` fails, use `from flair.datasets.sequence_labeling import JsonlCorpus, MultiFileJsonlCorpus`.
- Set `sample_missing_splits=False` when exact dev/test provenance matters.
- Use a user-chosen `base_path`/output directory, not package defaults.
- For transformer fine-tuning, start with `embeddings_storage_mode="none"`, smaller `mini_batch_size`, and `mini_batch_chunk_size` before increasing memory use.

## Which sub-skill should handle this?

- Prediction output, tokenization, serialization, regex, labels, visualization: [`tagging-and-annotations`](../sub-skills/tagging-and-annotations/SKILL.md).
- Embedding selection, vector shapes, stale embeddings, language models, ONNX/JIT/provider details: [`embeddings-and-optimization`](../sub-skills/embeddings-and-optimization/SKILL.md).
- Corpus formats, label dictionaries, training/fine-tuning, checkpoints, TARS, relation/span models, multi-GPU: [`training-and-datasets`](../sub-skills/training-and-datasets/SKILL.md).
- HunFlair/HunFlair2, biomedical dictionaries/linking, SciSpaCy biomedical tokenization, pyab3p: [`biomedical-nlp`](../sub-skills/biomedical-nlp/SKILL.md).

## Safe diagnostic

Run the bundled root diagnostic from any working directory with a public Flair environment active:

```bash
python scripts/collect_env.py --check-imports --json
```

It imports common modules and reports versions, device, cache root, CUDA visibility, optional dependency availability, and ONNX Runtime providers without loading models, datasets, or dictionaries.
