# Catalog navigation

This reference explains how to find and cite NLP-progress task, dataset, and benchmark material from a caller-supplied NLP-progress content root.

## Content-root assumptions

A valid content root is a static Markdown site checkout with:

- `README.md` at the root.
- Language directories containing Markdown pages, for example `english/`, `vietnamese/`, `chinese/`, `french/`, or `bengali/`.
- Support files for the static site may exist, but benchmark lookup normally needs only Markdown pages under language directories.

Do not treat NLP-progress as a Python package. It has no runtime model backend. Catalog lookup is read-only and CPU/any.

## First-pass inventory

From this sub-skill directory, run the standard-library helper against the content root:

```bash
python3 scripts/index_nlp_progress.py <content-root> --pretty
python3 scripts/index_nlp_progress.py <content-root> --language english --pretty
python3 scripts/index_nlp_progress.py <content-root> --language vietnamese --pretty
```

The JSON output lists language directories, Markdown file paths relative to the content root, headings with line numbers, and result-like table counts. Use it to pick candidate pages before opening large Markdown files.

## README table-of-contents route

The root `README.md` is the primary human navigation map. Its table of contents groups links by language. English usually links one task per file, while several non-English sections link anchors inside one language-level page.

Common patterns:

- English: many task files such as `english/question_answering.md`, `english/language_modeling.md`, `english/semantic_parsing.md`, and `english/sentiment_analysis.md`.
- Vietnamese: one multi-task page, `vietnamese/vietnamese.md`, with README anchors for dependency parsing, machine translation, named entity recognition, part-of-speech tagging, semantic parsing, and word segmentation.
- Hindi and Nepali: one language-level page with task anchors.
- Chinese: a small set of pages, including a general page, a word segmentation page, and a question answering page. The README also points readers to an external Chinese NLP website for broader Chinese coverage.
- French, German, Russian, Spanish, Bengali, Persian, and other directories: a few task-specific pages each.

If a user names a language and task, first search the README TOC for that language. If it is not listed, inventory the language directory directly; some files may be present even when not surfaced in the README TOC.

## Heading hierarchy semantics

Interpret headings as structural context, not just as anchors.

Typical semantics:

- H1 (`#`): the page-level task or catalog scope. Examples include `Question answering`, `Language modeling`, `Semantic parsing`, `Vietnamese NLP tasks`, and `Chinese Word Segmentation`.
- H2 (`##`): a subtask family or task group, such as `Reading comprehension`, `Open-domain Question Answering`, `AMR parsing`, `SQL parsing`, `Word Level Models`, or a language-level task in a multi-task page.
- H3 (`###`): commonly a dataset/benchmark under the current H1/H2 context, such as `SQuAD`, `NewsQA`, `Penn Treebank`, `PhoATIS`, or `MLSUM`.
- H4 (`####`): often a subdataset, release, partition, language direction, evaluation setting, or dataset version, such as `PMB-2.2.0`, `English-to-Vietnamese`, `MWC English in the single text, large setting`, or `Chinese Treebank 6`.

Important exceptions:

- Some H3 headings are not datasets. Treat headings such as `Table of contents`, `Warning: Evaluation Metrics`, `Task`, `Systems`, `Evaluation`, `Metrics`, `Datasets`, and `References` as structural notes unless nearby text clearly defines a benchmark.
- Some pages use H4 directly below an H2 task. Vietnamese dependency parsing, for example, uses H4 dataset versions under the H2 task.
- Some pages introduce a new peer task with a later H1. English sentiment analysis later uses `# Subjectivity analysis`; cite that as a separate H1-level task, not as a sentiment-analysis dataset.
- Repeated names need their full heading trail. `Penn Treebank` appears in language modeling under both word-level and character-level sections, so cite the H2 context.
- Heading anchors may be stale or manually mistyped in old README lists. If an anchor link fails, search for the visible heading text in the target page.

## Page-reading workflow

1. Identify the candidate language directory and page from README or the inventory JSON.
2. Read the H1 and the local table of contents if present.
3. Follow the heading trail down to the requested task, dataset, subdataset, split, or evaluation setting.
4. Extract the descriptive paragraphs immediately under that heading until the next peer heading or first result table. These paragraphs usually contain dataset size, splits, task definition, metric, official leaderboard, and data/download links.
5. Use only tables inside the same heading trail. Do not combine rows across peer datasets or across separate H4 partitions unless the user asks for a cross-dataset comparison and you preserve separate metrics.
6. Cite the page path relative to the content root and the heading trail, for example: `english/question_answering.md > Question answering > Reading comprehension > NewsQA`.

## Data to preserve when citing

For each benchmark fact, preserve:

- Language and content-root-relative page path.
- Heading trail, including repeated or nested headings.
- Dataset/task description and any explicit evaluation metric text.
- Public data, official leaderboard, and code links if present in nearby prose or table columns.
- Table columns, row values, paper/source link, and code link classification.
- Any local caveat text, such as warning sections, notes about preprocessing, dynamic evaluation, preprint status, or split differences.
