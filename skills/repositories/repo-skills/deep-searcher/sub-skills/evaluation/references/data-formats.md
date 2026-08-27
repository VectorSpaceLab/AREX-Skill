# Evaluation data and report formats

This reference defines the local file shapes expected by the DeepSearcher 2WikiMultiHopQA evaluation workflow and by the bundled validator. The full benchmark is strict about title metadata: retrieved result metadata must include `title`, and gold titles are read from `supporting_facts`.

## Dataset naming convention

For `dataset = 2wikimultihopqa`, the standard runner expects two JSON files with matching stems:

| Logical file | Typical filename | Purpose |
| --- | --- | --- |
| Corpus | `2wikimultihopqa_corpus.json` | Passages/articles to load into the vector DB. |
| Questions and ground truth | `2wikimultihopqa.json` | Multi-hop questions and supporting-fact gold titles used for recall. |

If you use a custom runner or custom paths, keep the same record shapes unless you also adapt the scoring code.

## Corpus JSON shape

The corpus file must be a JSON array of objects. Each object should include at least:

```json
{
  "title": "Ermengarde of Tours",
  "text": "Ermengarde of Tours (d. 20 March 851) was ..."
}
```

Required fields:

- `title`: non-empty string. This becomes metadata and is later compared with gold titles.
- `text`: non-empty string. With `JsonFileLoader` and `text_key: text`, this is the embedded document content.

Recommended properties:

- Titles should be stable, exact article titles. Recall matching is exact string membership.
- The file should already be passage/article sized. The benchmark load path uses a very large chunk size and zero overlap to avoid splitting records again.
- Avoid duplicate titles unless the benchmark intentionally contains multiple passages with the same title; duplicates can make title-level recall ambiguous.

## Question and ground-truth JSON shape

The questions file must be a JSON array of objects. The recall loop requires at least:

```json
{
  "_id": "83bf3b5a0bd911eba7f7acde48001122",
  "question": "When did Lothair II's mother die?",
  "supporting_facts": [
    ["Lothair II", 1],
    ["Ermengarde of Tours", 0]
  ],
  "answer": "20 March 851"
}
```

Required fields:

- `question`: non-empty string. This is passed to DeepSearcher retrieval and naive retrieval.
- `supporting_facts`: non-empty list of two-item pairs. The first item in each pair must be a non-empty title string. The second item is usually a sentence index and is accepted as integer, string, or null by the validator because the recall scorer only uses the title.

Common 2Wiki-style optional fields include `_id`, `type`, `context`, `entity_ids`, `evidences`, `answer`, `evidences_id`, and `answer_id`. These are not required by the recall scorer, but preserving them helps audit samples.

## Title matching contract

Recall is title-based. For the standard scorer:

```text
gold_titles = {pair[0] for pair in sample["supporting_facts"]}
retrieved_titles = [result.metadata["title"] for result in retrieved_results]
Recall@K = count(gold title in retrieved_titles[:K]) / len(gold_titles)
```

Implications:

- `supporting_facts` titles must exactly match corpus `title` values after JSON decoding.
- Retrieved result metadata must include a `title` key. The standard corpus + `JsonFileLoader(text_key="text")` preserves the corpus object's remaining fields, including `title`, as metadata.
- Case, punctuation, whitespace, and Unicode normalization differences can reduce recall even if the intended article is retrieved.
- If a sample has duplicate supporting-fact titles, the scorer effectively de-duplicates them by using a set.

## YAML configuration shape

The validator checks that the YAML file has these sections:

```yaml
provide_settings:
  llm:
    provider: "..."
    config: {}
  embedding:
    provider: "..."
    config: {}
  file_loader:
    provider: "JsonFileLoader"
    config:
      text_key: "text"
  web_crawler:
    provider: "..."
    config: {}
  vector_db:
    provider: "..."
    config: {}
query_settings:
  max_iter: 3
load_settings:
  chunk_size: 1500
  chunk_overlap: 100
```

The `web_crawler` section is still part of normal DeepSearcher configuration even though the 2Wiki retrieval benchmark does not crawl websites. Provider construction may initialize configured modules before any benchmark logic runs.

## Output directory layout

For `output_dir=/path/eval-output` and `flag=result`, outputs live in:

```text
/path/eval-output/result/details.csv
/path/eval-output/result/statistics.json
```

Use one `flag` per logical run. If you change provider/model, `max_iter`, corpus, embedding, vector DB, or `pre_num` target, prefer a new `flag` or archive the old report files.

## `details.csv` row schema

The CSV contains these columns:

| Column | Meaning |
| --- | --- |
| `idx` | Zero-based dataset index. |
| `question` | Question text. |
| `recall` | DeepSearcher recall dictionary, typically with keys `2` and `5`. |
| `recall_naive` | Naive RAG recall dictionary. |
| `gold_titles` | List of supporting-fact titles. |
| `retrieved_titles` | Titles returned by DeepSearcher retrieval. |
| `retrieved_titles_naive` | Titles returned by naive RAG retrieval. |

When pandas reloads the CSV, list and dictionary columns may be strings. Use a safe parser such as `ast.literal_eval` for trusted local outputs; do not use `eval`.

## `statistics.json` shape

A typical aggregate report has this structure:

```json
{
  "deepsearcher": {
    "average_recall": {"2": 0.5, "5": 1.0},
    "token_usage": 12345,
    "error_num": 0,
    "sample_num": 5,
    "token_usage_per_sample": 2469.0
  },
  "naive_rag": {
    "average_recall": {"2": 0.3, "5": 0.6}
  }
}
```

JSON object keys may be strings even when in-memory recall dictionaries used integer keys. Handle both `2` and `"2"` in downstream summaries.

## Tiny custom-fixture checklist

Before running a credentialed benchmark on custom data:

1. Create a tiny corpus of 3-10 records with exact `title` and `text` fields.
2. Create 1-3 questions with `question` and `supporting_facts` title pairs that reference titles in the corpus.
3. Validate with `scripts/check_evaluation_inputs.py --sample-limit 3`.
4. Confirm every supporting title appears in the corpus title set, or intentionally allow missing titles and document why.
5. Run with `pre_num` equal to the tiny question count, then inspect both CSV and JSON outputs before scaling.
