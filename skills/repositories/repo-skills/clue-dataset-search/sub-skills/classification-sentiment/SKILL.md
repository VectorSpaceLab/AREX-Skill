---
name: classification-sentiment
description: "Guides text classification, topic classification, sentiment,
  emotion, aspect sentiment, and entity-sentiment dataset discovery in
  CLUEDatasetSearch."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# Classification and Sentiment Dataset Route

Use this sub-skill when the user intent matches one of these signals:

- text classification, topic labels, short or long Chinese text
- sentiment, emotion, polarity, aspect-level or entity sentiment
- THUCNews, IFLYTEK, ChnSentiCorp, NLPCC emotion, weibo_senti_100k

Read references/dataset-selection.md for classification/sentiment choices and references/troubleshooting.md for label and corpus ambiguity.

## Fast workflow

1. Restate the user's requested task, language, domain, and output need.
2. Search the bundled root index before recommending a row:

```bash
python ../../scripts/search_dataset_index.py --category text-classification --query IFLYTEK
python ../../scripts/search_dataset_index.py --category sentiment-analysis --query aspect
python ../../scripts/search_dataset_index.py --query weibo_senti_100k
```

3. Compare title, category, description, keywords, provider, license, paper, and note fields.
4. Warn that CLUEDatasetSearch is a catalogue: no dataset files are bundled and external access must be verified.
5. If the request belongs to another family, route to the sibling sub-skill named below instead of forcing a weak match.

## Boundary routes

- Root overview and cross-category search: [../../SKILL.md](../../SKILL.md).
- Shared table schema and duplicate handling: [../../references/catalogue-overview.md](../../references/catalogue-overview.md).
- Access, license, privacy, and link caveats: [../../references/access-and-license-caveats.md](../../references/access-and-license-caveats.md).
- Full bundled index: [../../references/dataset-index.json](../../references/dataset-index.json).
- Cross-cutting troubleshooting: [../../references/troubleshooting.md](../../references/troubleshooting.md).

## Output pattern

When answering, include:

- candidate dataset title and category;
- why it fits the task;
- language/domain/scale hints from the catalogue;
- provider and source URL when present in the bundled index;
- license/access caveat, especially if blank or competition-hosted;
- what the user must verify upstream before download, redistribution, or benchmark use.

Do not tell future agents to open or run files from the original repository checkout.
