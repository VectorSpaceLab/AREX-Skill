# Multilingual coverage

NLP-progress contains about 66 Markdown task pages under language directories. Coverage is intentionally uneven: English has broad historical coverage, while many non-English directories contain a few focused pages or one language-level page with several tasks.

## Observed language-directory patterns

| Language directory | Typical shape | Navigation notes |
| --- | --- | --- |
| `english/` | Broad coverage, about 39 task pages | README links many task files directly. Pages may be large and contain many datasets and tables. |
| `vietnamese/` | One multi-task page | README task links point to anchors inside `vietnamese/vietnamese.md`. H2 headings are tasks; H3/H4 headings are datasets, versions, or directions. |
| `chinese/` | Three pages | Includes a general Chinese NLP page, Chinese word segmentation, and question answering. README also points to an external Chinese NLP website for broader coverage. |
| `hindi/` | One multi-task page | Task anchors cover chunking, POS tagging, and machine translation. |
| `bengali/` | Several small task pages | Includes POS tagging, emotion detection, sentiment analysis, and a question-answering page that may need directory inventory if not surfaced in a README list. |
| `persian/` | Several task pages | Named entity recognition, natural language inference, and summarization. |
| `russian/`, `spanish/`, `french/`, `german/` | A few task-specific pages each | Summarization pages often share MLSUM context and warning text about automatic metrics. |
| `arabic/`, `korean/`, `nepali/`, `portuguese/`, `turkish/` | One focused page each | Some pages are thin or prose-only. Verify whether a local result table actually exists. |

Use `scripts/index_nlp_progress.py <content-root> --pretty` to obtain the current file count and table count for a specific checkout instead of assuming the coverage is unchanged.

## Thin or missing local coverage

A user may ask for a language/task combination that has only a prose description, an external leaderboard pointer, or no local page. Handle this explicitly:

- German and Korean question-answering pages may describe datasets and project pages without local result tables.
- Arabic language modeling may list model/paper/code resources but no numeric metric column.
- Some English pages, such as automatic speech recognition, may be prose-only or lack local SOTA rows.
- The README wish list names tasks still missing from local coverage, such as bilingual dictionary induction, discourse parsing, knowledge base population, more dialogue tasks, semi-supervised learning, and full-sentence FrameNet analysis.
- Chinese coverage is intentionally partial in this repository; the README points readers to a separate Chinese NLP website for more tasks, datasets, and results.

When local coverage is thin, say what NLP-progress contains and what it does not contain. Do not infer current SOTA from outside sources unless the user explicitly asks for live external research.

## Language/task routing examples

- “Vietnamese NER” → `vietnamese/vietnamese.md` with heading trail `Vietnamese NLP tasks > Named entity recognition`; distinguish `PhoNER_COVID19` and `VLSP` sections.
- “Vietnamese machine translation IWSLT” → `vietnamese/vietnamese.md > Machine translation > IWSLT2015 Dataset`; preserve H4 direction headings such as `English-to-Vietnamese` and `Vietnamese-to-English` plus the test-set note.
- “Chinese word segmentation CTB6” → `chinese/chinese_word_segmentation.md > Chinese Word Segmentation > Evaluation > Dataset > Chinese Treebank 6`; note that H2 `Systems` lists input-feature symbols, while H4 dataset headings contain result tables.
- “French summarization OrangeSum” → `french/summarization.md > Summarization > OrangeSum`; distinguish `OrangeSum-abstract` and `OrangeSum-title` H4 tables.
- “Bengali sentiment” → `bengali/sentiment_analysis.md > Sentiment analysis > SentNoB`; expect a small single-result table.
- “German QA” → `german/question_answering.md > Question answering > GermanQuAD`; expect dataset description and project link, not a local result table.
- “English semantic parsing Spider” → `english/semantic_parsing.md > Semantic parsing > SQL parsing > Spider`; this section points to dataset and leaderboard access, while neighboring SQL datasets have local result tables.

## Cross-language caution

Do not transfer claims across languages just because task names match. For example, English summarization rows, French MLSUM rows, and German MLSUM rows are separate contexts with different splits and languages. Cite the language-specific page and heading trail.

When a multilingual dataset appears across several languages, capture both the shared dataset identity and the page-specific language result table. Summarization pages often reuse MLSUM text but report language-specific metric rows.

## Missing-page response pattern

If no local page or no local table exists, answer in this shape:

> I found `<language/task>` coverage at `<relative path and heading>` but NLP-progress lists only `<description/leaderboard/data link>` and no local model-result table. For current SOTA, treat the local catalog as incomplete/stale and check the official leaderboard or current literature if allowed.
