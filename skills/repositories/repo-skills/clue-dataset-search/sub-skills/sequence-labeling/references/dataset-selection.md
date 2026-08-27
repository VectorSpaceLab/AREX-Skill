# NER / Sequence-labeling Dataset Selection

## When to use this reference

Use this when the user asks for named entity recognition, entity extraction,
sequence labels, BIO/BMEO-style annotations, or entity datasets in Chinese,
English, medical, news, or social-media domains.

## Representative catalogue rows

| Need | Candidate rows | Notes |
|---|---|---|
| Chinese medical NER | CCKS2017 Chinese EMR NER; CCKS2018 Chinese EMR NER | Medical records are sensitive; catalogue license fields are blank. Verify access and de-identification. |
| General Chinese NER | MSRA NER; People's Daily 1998; Boson | Description includes BIO/BMEO hints for some rows; verify current upstream format before preprocessing. |
| CLUE benchmark-style NER | CLUE Fine-Grain NER / CLUENER | Catalogue links a public CLUE ZIP and describes 10 fine-grained entity labels. |
| English NER benchmark | CoNLL-2003 | Catalogue includes a paper URL and English note. |
| Social media / segmentation-adjacent NER | Weibo entity recognition; SIGHAN Bakeoff 2005 | Rows have sparse descriptions; treat as search clues. |

## Selection workflow

1. Identify language, domain, and entity granularity.
2. Search the bundled index with the exact task signal or known acronym.
3. Compare `description`, `keywords`, `task_type`, `license`, and `note`.
4. Warn when the licence field is blank or the source is a competition portal.
5. Do not describe data files or label maps as locally available unless the
   user separately provides the downloaded dataset.

## Useful helper commands

```bash
python ../../scripts/search_dataset_index.py --category ner --query CCKS
python ../../scripts/search_dataset_index.py --category ner --query CLUENER --json
python ../../scripts/search_dataset_index.py --category ner --language English --limit 0
```

## Validation checklist

- The answer names the category `ner` or source category `NER`.
- The candidate's language/domain is supported by the row, not inferred from the title alone.
- Medical or personal-data resources include privacy and license cautions.
- BIO/BMEO or entity-type claims are limited to what the catalogue row states.
