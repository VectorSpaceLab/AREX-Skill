---
name: sequence-labeling
description: "Guides named-entity-recognition and sequence-labeling dataset
  discovery in CLUEDatasetSearch, including CLUENER, CCKS medical NER, MSRA,
  People Daily, Boson, and CoNLL resources."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# Sequence Labeling Dataset Route

Use this sub-skill when the user intent matches one of these signals:

- NER, named entity recognition, entity spans, BIO or BMEO labels
- Chinese medical or news entity extraction datasets
- CLUENER, CCKS, MSRA, Boson, CoNLL-2003, SIGHAN Bakeoff

Read references/dataset-selection.md for NER candidate comparison and references/troubleshooting.md for entity-task caveats.

## Fast workflow

1. Restate the user's requested task, language, domain, and output need.
2. Search the bundled root index before recommending a row:

```bash
python ../../scripts/search_dataset_index.py --category ner --query cluener
python ../../scripts/search_dataset_index.py --category ner --query medical
python ../../scripts/search_dataset_index.py --category ner --language English
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
