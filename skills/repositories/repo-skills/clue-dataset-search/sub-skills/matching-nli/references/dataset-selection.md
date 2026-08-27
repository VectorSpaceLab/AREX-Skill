# Matching, Similarity, and NLI Dataset Selection

## When to use this reference

Use this when the user needs question pairs, sentence pairs, semantic
similarity, NLI/entailment, DBQA answer relevance, search result ranking,
query-title matching, or legal case similarity.

## Representative choices

| Need | Candidate rows | Key task distinction |
|---|---|---|
| Chinese question/paraphrase matching | LCQMC, BQ Corpus, AFQMC, CCKS banking matching | Pair labels usually indicate same intent or semantic equivalence. |
| Finance/banking matching | AFQMC, BQ Corpus, Paipaidai, CCKS banking | Verify domain and data portal availability. |
| Legal similarity | CAIL2019 SCM | The row describes triplets `(A,B,C)` and relative similarity, not ordinary binary pairs. |
| Chinese NLI / textual inference | ChineseTextualInference, CNSD / CLUE-CMNLI | Check whether labels are entailment/neutral/contradiction or translated NLI. |
| QA relevance / DBQA | NLPCC-DBQA, cMedQA matching rows | Use when the task is matching a question-answer pair, not reading comprehension. |
| Word/sentence similarity | ChineseSTS, COS960 | Scores or word-pair similarity rather than classification. |
| Search ranking / query-title | OPPO query-title, SogouE | May involve CTR/search-query semantics and special fields. |

## Selection workflow

1. Identify data unit: sentence pair, question pair, question-answer pair,
   document triplet, word pair, or query-title record.
2. Search for domain and acronym signals.
3. Compare label semantics before recommending model heads or metrics.
4. If the user asks for answer extraction or passage RC, route to `qa-reading`.
5. If the user asks for topic/sentiment labels, route to `classification-sentiment`.

## Useful helper commands

```bash
python ../../scripts/search_dataset_index.py --category text-matching --query LCQMC
python ../../scripts/search_dataset_index.py --category text-matching --query finance
python ../../scripts/search_dataset_index.py --category text-matching --query CAIL --json
python ../../scripts/search_dataset_index.py --query CMNLI --limit 0
```

## Validation checklist

- The answer names the record shape: pair, triplet, score, or query-title.
- Domain-specific datasets include domain caveats (finance, legal, medical).
- NLI rows are not described as generic classification unless label semantics
  are clear.
- QA relevance rows are not confused with reading-comprehension datasets.
