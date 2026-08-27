# Synonyms Workflows

## Purpose

Use this for task-oriented recipes with the Synonyms package. For exact signatures, read [api-reference.md](api-reference.md). For model setup, read [model-and-environment.md](model-and-environment.md).

## Workflow 1: verify install and model readiness

Start with the bundled probe:

```bash
python scripts/synonyms_smoke_probe.py --use-tiny-fixture --word 人脸
```

Interpretation:

- Success means the installed package and API mechanics work.
- It does **not** mean the full Synonyms semantic model is available.
- If real semantic quality matters, rerun with a real model path:

```bash
python scripts/synonyms_smoke_probe.py --model-path /path/to/words.vector.gz --word 飞机
```

If the task is in a notebook/service process, set model env vars before the process imports `synonyms`.

## Workflow 2: Chinese synonym lookup

```python
import synonyms

words, scores = synonyms.nearby("人脸", size=10)
if not words:
    print("OOV or model unavailable for this word")
for word, score in zip(words, scores):
    print(f"{word}\t{score:.3f}")
```

Use this for synonym expansion, query expansion, lightweight retrieval features, or debugging vocabulary coverage. Validate that the queried words exist in the loaded model before treating empty results as a semantic signal.

## Workflow 3: sentence similarity

```python
import synonyms

pairs = [
    ("旗帜引领方向", "道路决定命运"),
    ("旗帜引领方向", "旗帜指引道路"),
]
for a, b in pairs:
    print(a, b, synonyms.compare(a, b, seg=True))
```

Use `seg=True` for raw Chinese strings. Use `seg=False` only when each string is already whitespace-tokenized:

```python
synonyms.compare("你们 好 呀", "大家 好", seg=False)
```

The score is package-specific and combines vectors with character-distance smoothing. Do not compare it directly with scores from unrelated embedding packages without calibration.

## Workflow 4: segmentation and keywords

```python
import synonyms

words, tags = synonyms.seg("中文近义词工具包")
keywords = synonyms.keywords("华为芯片供应出现变化", topK=3)
```

Use this when you need the package's jieba dictionary configuration alongside Synonyms workflows. If you need a custom segmentation dictionary, set `SYNONYMS_WORDSEG_DICT` before import.

## Workflow 5: vector probing

```python
import synonyms

try:
    vector = synonyms.v("飞机")
    print(vector.shape)
except KeyError:
    print("word not in the loaded model")
```

For sentence-level vector features:

```python
tokens = "中文 近义词 工具包".split()
features = synonyms.bow(tokens, ignore=True)
```

Prefer `ignore=True` in workflows where dropping OOV tokens is safer than injecting deterministic random vectors.

## Evaluation and benchmark caveats

The source repository includes evaluation examples and a benchmark intent, but they are not bundled as runtime commands because they either mutate files or run a long microbenchmark. If you need evaluation-quality scores:

1. Verify the real full/equivalent model is loaded.
2. Use a fixed word-pair or sentence-pair fixture owned by your task.
3. Record model version/path privately; do not publish local file paths.
4. Compare trends within the same Synonyms model, not across unrelated scoring libraries without normalization.

For a quick performance smoke, adapt the bundled probe around a small fixed word list rather than running large-loop benchmarks by default.

## RAG/retrieval usage notes

Synonyms can support query expansion or lightweight Chinese similarity features in RAG/search systems, but it is not a vector database, embedding service, or neural retriever framework by itself. Use it when the task specifically needs Chinese synonym expansion, word-level similarity, or quick sentence similarity. For dense retrieval model training/serving, route to a package specialized for embeddings/retrieval.
