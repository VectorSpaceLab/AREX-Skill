# ColBERT Data Formats

ColBERT relies on small, explicit text formats for most repository workflows. Treat these files as contracts: validate row shape, ID domains, and rank ordering before indexing, retrieval, training, or evaluation.

## Core TSV Files

### Collection TSV

Each row represents one passage:

```text
pid<TAB>passage text
0<TAB>late interaction stores token embeddings
1<TAB>ColBERT searches over passages
```

Rules:

- Standard ColBERT collection files have exactly two tab-separated columns.
- `pid` should parse as an integer for ranking and evaluation compatibility.
- Passage text must not contain raw newlines; replace tabs/newlines inside text before writing.
- Avoid duplicate PIDs. Duplicate PIDs make ranking PID checks ambiguous.
- `Collection(data=[...]).save(...)` enumerates passages from `0`; preserve external PID mappings separately if you start from in-memory text only.

### Queries TSV

Each row maps a query id to text:

```text
qid<TAB>query text
0<TAB>what is late interaction
1<TAB>how does ColBERT rank passages
```

Rules:

- Use exactly two columns.
- Query IDs may be strings in some loader paths, but evaluation and ranking utilities generally parse qids as integers.
- Avoid duplicate qids; `Queries`, split helpers, and evaluation expect one query text per qid.
- Keep qids aligned with qrels, ranking rows, and LoTTE QA JSONL.

### Ranking TSV

ColBERT ranking rows are tab-separated:

```text
qid<TAB>pid<TAB>rank[<TAB>score]
0<TAB>1<TAB>1<TAB>12.5
0<TAB>0<TAB>2<TAB>9.1
```

Rules:

- `qid`, `pid`, and `rank` should parse as integers.
- Rank is 1-indexed within each qid.
- Basic MSMARCO-style evaluation accepts three or four columns.
- Score-aware workflows require a numeric fourth column.
- LoTTE rankings conventionally require four columns: `qid<TAB>pid<TAB>rank<TAB>score`.
- Ranks should be sequential for each qid. Non-sequential ranks often indicate a partial merge or a zero-indexing bug.

### Qrels TSV

MSMARCO-style passage qrels use whitespace-separated columns:

```text
qid 0 pid label
0 0 1 1
1 0 4 1
```

Rules:

- The second column is an unused placeholder in the ColBERT MSMARCO utility.
- Labels are expected to be `1` by the native evaluator.
- A qid can have multiple positive pids.
- Evaluation expects ranked qids to be a subset of judged qids; missing ranked qids should be fixed or explicitly treated as warnings in custom scripts.

## JSONL QA Files

Each line is an independent JSON object. Do not wrap a JSONL file in a top-level list.

### LoTTE QA JSONL

```json
{"qid": 0, "query": "how to sharpen a pencil", "answer_pids": [10, 11]}
```

Rules:

- File names are typically `qas.search.jsonl` or `qas.forum.jsonl`.
- `qid` must align with matching `questions.search.tsv` or `questions.forum.tsv` rows and ranking qids.
- `answer_pids` contains collection passage IDs considered successful hits.
- LoTTE Success@k is positive when any retrieved top-k pid intersects `answer_pids`.

### `Queries` QA JSON

The `Queries` wrapper treats paths ending in `.json` as JSON-lines QA input with a `question` field:

```json
{"qid": 0, "question": "what is late interaction", "answers": ["token-level scoring"]}
```

Rules:

- The loader asserts qids are unique.
- `Queries.qas()` is available only when QA dictionaries were loaded.
- The wrapper checks the `.json` suffix, not `.jsonl`, for this branch; use TSV for generic query lists unless a QA-specific caller expects this behavior.

## LoTTE Directory Layout

A LoTTE data root contains domains, splits, collection files, question files, and QA JSONL files:

```text
lotte/
  writing/
    dev/
      collection.tsv
      metadata.jsonl
      questions.search.tsv
      qas.search.jsonl
      questions.forum.tsv
      qas.forum.jsonl
    test/
      collection.tsv
      ...
```

Ranking files live in a separate rankings root:

```text
rankings/
  dev/
    writing.search.ranking.tsv
    writing.forum.ranking.tsv
    recreation.search.ranking.tsv
    recreation.forum.ranking.tsv
    science.search.ranking.tsv
    science.forum.ranking.tsv
    technology.search.ranking.tsv
    technology.forum.ranking.tsv
    lifestyle.search.ranking.tsv
    lifestyle.forum.ranking.tsv
    pooled.search.ranking.tsv
    pooled.forum.ranking.tsv
```

Exact names matter for the native LoTTE evaluator. Missing ranking files may produce partial `???` output, but missing QA files, malformed JSONL, or rank assertion failures should be treated as hard errors.

## Tiny Fixture Pattern

Use tiny fixtures to debug format issues before large runs.

`collection.tsv`:

```text
0<TAB>alpha answer passage
1<TAB>beta distractor passage
2<TAB>gamma answer passage
```

`queries.tsv`:

```text
0<TAB>alpha question
1<TAB>gamma question
```

`qrels.tsv`:

```text
0 0 0 1
1 0 2 1
```

`ranking.tsv`:

```text
0<TAB>1<TAB>1<TAB>3.0
0<TAB>0<TAB>2<TAB>2.0
1<TAB>2<TAB>1<TAB>4.0
```

Expected MSMARCO-style metrics:

- `MRR@10 = (1/2 + 1/1) / 2 = 0.75`
- `Recall@1 = (0 + 1) / 2 = 0.5`
- `Recall@10 = 1.0`

Tiny LoTTE-style QA for the same ranking can be:

```json
{"qid": 0, "query": "alpha question", "answer_pids": [0]}
{"qid": 1, "query": "gamma question", "answer_pids": [2]}
```

Expected `Success@1 = 50.0` and `Success@2 = 100.0`.
