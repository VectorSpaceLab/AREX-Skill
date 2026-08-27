---
name: clue-dataset-search
description: "Routes tasks for discovering NLP datasets in the CLUEDatasetSearch
  catalogue, including Chinese NLP classification, QA, matching, NER,
  generation, translation, corpus, and reading-comprehension resources."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# CLUEDatasetSearch Operating Skill

Use this skill when a task asks for NLP dataset discovery, dataset-catalogue
search, or choosing Chinese/English NLP resources from the CLUEDatasetSearch
catalogue. The skill is a self-contained guide to the repository's Markdown
catalogue; it does **not** bundle the original datasets.

## First checks

1. Decide whether the user wants a dataset recommendation, a catalogue lookup,
   a task-family comparison, or troubleshooting for a link/license/download.
2. Read [references/catalogue-overview.md](references/catalogue-overview.md)
   for category names, table fields, duplicate handling, and search strategy.
3. Read [references/access-and-license-caveats.md](references/access-and-license-caveats.md)
   before suggesting a download, publication, benchmark comparison, or training
   run that depends on an external dataset.
4. If the user names this repo, CLUE, CLUEDatasetSearch, or a dataset title,
   use the bundled helper:

```bash
python scripts/search_dataset_index.py --query dureader --limit 5
python scripts/search_dataset_index.py --category text-matching --query lcqmc
python scripts/search_dataset_index.py --language Chinese --query sentiment --json
```

The helper reads [references/dataset-index.json](references/dataset-index.json),
a bundled index distilled from the catalogue tables.

## Route by task family

| User intent | Read next | Typical signals |
|---|---|---|
| Named entity recognition, entity spans, sequence labels, BIO/BMEO labels | [sequence-labeling](sub-skills/sequence-labeling/SKILL.md) | NER, CLUENER, CCKS medical entity extraction, MSRA, CoNLL-2003, People's Daily, Boson |
| Question answering or reading comprehension | [qa-reading](sub-skills/qa-reading/SKILL.md) | QA, RC, DuReader, SQuAD, NewsQA, CMRC, CAIL, cloze, yes/no, conversational QA |
| Classification, topic labels, sentiment, emotion, aspect sentiment | [classification-sentiment](sub-skills/classification-sentiment/SKILL.md) | THUCNews, IFLYTEK, ChnSentiCorp, weibo_senti, NLPCC emotion, aspect sentiment, entity sentiment |
| Text matching, semantic similarity, NLI, entailment, DBQA relevance | [matching-nli](sub-skills/matching-nli/SKILL.md) | LCQMC, BQ, AFQMC, CMNLI, ChineseSTS, CHIP, CAIL SCM, query-title matching |
| Summarization, machine translation, broad corpora, pretraining corpora, knowledge graph/social graph data | [generation-corpora](sub-skills/generation-corpora/SKILL.md) | LCSTS, WMT, translation2019zh, wiki2019zh, webtext2019zh, NLPIR corpus, knowledge graph |

When a request spans multiple task families, route through each owning sub-skill
and use the root helper to collect candidate rows before comparing license,
language, domain, scale, and access constraints.

## What this skill can and cannot claim

- It can summarize catalogue metadata: dataset title, provider, update date,
  license field when present, task label, keywords, paper URL, notes, and
  external access URL.
- It can suggest candidate datasets for a task and explain why another category
  may be a better fit.
- It can warn about blank license fields, link rot, Baidu Pan/password links,
  paid LDC resources, privacy-sensitive social data, and large downloads.
- It cannot certify that an external download still exists, that a license is
  sufficient for commercial use, or that benchmark results are comparable.
- It cannot train, evaluate, or preprocess any dataset because no dataset files
  are bundled with this skill.

## Validation workflow

For a dataset-discovery answer, validate the final recommendation with this
checklist:

1. The task family is routed to the right sub-skill.
2. At least one bundled-index query supports the dataset title or task signal.
3. The answer distinguishes catalogue metadata from verified downloaded data.
4. License/access caveats are explicit when the licence field is blank, paid,
   password-protected, or externally hosted.
5. For duplicate or overlapping dataset names, the category and task reason are
   named, not just the title.

## Maintenance and staleness

Read [references/repo-provenance.md](references/repo-provenance.md) before
refreshing this skill for a newer checkout. If the catalogue categories,
Markdown table schema, source commit, or generated dataset index changed, run a
repo-skill refresh rather than editing the bundled index by hand.

For cross-cutting failure modes, read
[references/troubleshooting.md](references/troubleshooting.md).
