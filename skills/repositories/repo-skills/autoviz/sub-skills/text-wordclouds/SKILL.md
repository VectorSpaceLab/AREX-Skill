---
name: text-wordclouds
description: "Use AutoViz text-column cleaning and wordcloud behavior for
  NLP-style tabular fields."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Text Wordclouds

Use this sub-skill when the user asks about AutoViz behavior for string columns, discrete text columns, NLP variables, wordcloud plots, text cleanup, emoji handling, stopwords, or NLTK downloads.

## Use this when

- The prompt names `wordcloud`, `AutoViz_NLP`, `draw_word_clouds`, `nltk`, `textblob`, `emoji`, stopwords, contractions, or text cleanup.
- AutoViz detects string variables and attempts to generate wordclouds.
- The user needs to understand why a text column did or did not get a wordcloud.
- The user is debugging missing NLTK data, missing `wordcloud`, or text preprocessing side effects.
- The user wants to know how AutoViz distinguishes categorical strings from NLP-style strings.

## Core flow

1. Start from the DataFrame and identify candidate string columns.
2. Let AutoViz classify variables first; only discrete/NLP string variables reach the wordcloud branch.
3. For each selected string column, AutoViz cleans text and calls wordcloud generation.
4. If a target column is present and the problem type is classification, wordclouds may be drawn per target class.
5. Use static chart formats for deterministic automated runs; interactive behavior is covered by the EDA sub-skill.
6. When the user only needs text preprocessing, explain the cleanup helpers without forcing a full AutoViz run.

## Read these references

- [`references/workflows.md`](references/workflows.md): text-cleaning and wordcloud-generation behavior.
- [`references/troubleshooting.md`](references/troubleshooting.md): NLTK, wordcloud, and string-column classification issues.
- [`../../references/api-reference.md`](../../references/api-reference.md): signatures for text helper functions and `draw_word_clouds`.
- [`../eda-visualization/references/workflows.md`](../eda-visualization/references/workflows.md): how text columns fit into the full AutoViz run.
- [`../../references/install-and-compatibility.md`](../../references/install-and-compatibility.md): package-version checks if the text branch breaks at import time.

## Use these scripts

- Run [`scripts/wordcloud_smoke.py`](scripts/wordcloud_smoke.py) to verify that the `wordcloud` package and AutoViz text helper path can run on a safe in-memory DataFrame.
- If the text branch is failing inside a larger EDA run, use the EDA smoke script first and then return here.

## Important behavior

- AutoViz may call `nltk.download('popular')` when discrete string variables are present.
- Short or low-cardinality strings may be classified as categorical/boolean rather than NLP.
- Very high-cardinality or long free-text columns are more likely to trigger wordcloud behavior.
- `draw_word_clouds` depends on matplotlib plus the `wordcloud` package.
- The text helpers also perform cleanup such as URL, HTML, emoji, contraction, and punctuation handling.

## Common text helpers

- `clean_steps`
- `clean_text`
- `remove_URL`
- `remove_html`
- `remove_emoji`
- `expandContractions`
- `remove_stopwords`
- `split_into_lemmas`
- `draw_wordcloud_from_dataframe`

## Cross-routing

- If the user primarily wants full-table EDA plots, route to [`../eda-visualization/SKILL.md`](../eda-visualization/SKILL.md).
- If the user asks whether a text column should be cleaned or repaired before modeling, route to [`../data-quality-fixes/SKILL.md`](../data-quality-fixes/SKILL.md) and return here for visualization-specific text behavior.
- Do not rely on source notebooks or the original checkout; use the bundled references and script.
- If the user needs to know whether NLTK data will be downloaded, mention it explicitly before running the workflow.

## Troubleshooting reminders

- If the column never reaches the wordcloud branch, the classifier likely treated it as categorical or boolean.
- If `nltk.download('popular')` is a problem, prepare the corpora or choose a static EDA path that does not trigger text plotting.
- If the output is empty or tiny, the text may have been over-cleaned or reduced to stopwords.
- Use a writable `save_plot_dir` when saving images so the generated wordcloud is easy to find.

## Escalation

If the user really wants a full EDA view of the same dataframe, route back to the EDA sub-skill after handling the text question.
If the data-quality question is about missingness or cleaning rather than visualization, route to the data-quality sub-skill instead of over-focusing on wordclouds.
