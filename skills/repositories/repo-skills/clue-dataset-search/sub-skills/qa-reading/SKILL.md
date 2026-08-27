---
name: qa-reading
description: "Guides question-answering and reading-comprehension dataset
  discovery in CLUEDatasetSearch, including DuReader, SQuAD, NewsQA, CMRC, CAIL,
  cMedQA, CoQA, and search-log QA resources."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# QA and Reading Dataset Route

Use this sub-skill when the user intent matches one of these signals:

- question answering, open-domain QA, answer selection
- reading comprehension, cloze, yes/no, multi-document or legal RC
- DuReader, SQuAD, CMRC, CAIL, NewsQA, WikiQA, MS MARCO

Read references/dataset-selection.md for QA/RC comparisons and references/troubleshooting.md for duplicate names and access issues.

## Fast workflow

1. Restate the user's requested task, language, domain, and output need.
2. Search the bundled root index before recommending a row:

```bash
python ../../scripts/search_dataset_index.py --query dureader
python ../../scripts/search_dataset_index.py --category reading-comprehension --query legal
python ../../scripts/search_dataset_index.py --query SQuAD --limit 0
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
