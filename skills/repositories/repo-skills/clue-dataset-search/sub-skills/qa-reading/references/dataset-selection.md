# QA and Reading-comprehension Dataset Selection

## When to use this reference

Use this when the user asks for QA datasets, answer selection, reading
comprehension, cloze tasks, yes/no questions, search-log QA, conversational QA,
legal RC, medical QA, or English benchmark QA.

## QA vs reading-comprehension routing

- Use `qa` rows for broad question-answer datasets and answer-selection
  resources such as NewsQA, SQuAD, SimpleQuestions, WikiQA, cMedQA, cMedQA2,
  webMedQA, XQA, and AmazonQA.
- Use `reading-comprehension` rows when the task requires passages, documents,
  answer spans, cloze insertion, yes/no/robustness variants, legal RC, or
  multi-document reading. Examples include DuReader, CMRC, CJRC, CAIL, CoQA,
  RACE, Quasar, MS MARCO, and SQuAD1.0/2.0.
- Route pairwise QA relevance or question similarity to `matching-nli` when the
  user is building a matching/ranking model instead of an answer-extraction or
  reading task.

## Representative choices

| Need | Candidate rows | What to verify |
|---|---|---|
| Chinese search-engine RC | DuReader, DuReader2.0, DuReader-Robust, DuReader-checklist, DuReader-YesNo | Variant definitions, Apache license text, current Baidu pages. |
| Chinese exam/cloze RC | CMRC 2017/2018/2019, Chinese Cloze RC | Task type: span extraction, sentence insertion, or cloze. |
| Chinese legal RC | CJRC, CAIL2020, CAIL2021 | Legal data access, document type, answer type, competition terms. |
| Medical QA | cMedQA, cMedQA2, webMedQA | Forum origin, anonymization, license, QA-vs-matching use. |
| English span/open QA | SQuAD, SQuAD2.0, NewsQA, WikiQA, MS MARCO | Version, answerability, license, current download page. |
| Conversational or multiple-choice QA | CoQA, RACE, HEAD-QA, Frames | Dialogue/multiple-choice schema and language. |

## Useful helper commands

```bash
python ../../scripts/search_dataset_index.py --query dureader --limit 0
python ../../scripts/search_dataset_index.py --category reading-comprehension --query legal
python ../../scripts/search_dataset_index.py --query SQuAD --json
python ../../scripts/search_dataset_index.py --query medical --category qa
```

## Validation checklist

- Name the category row source (`qa` vs `reading-comprehension`) for ambiguous titles.
- Distinguish answer extraction, answer selection, cloze, yes/no, and conversational tasks.
- Warn about accounts, competition pages, or paid/permissioned sources.
- Do not promise that model-ready train/dev/test files are bundled here.
