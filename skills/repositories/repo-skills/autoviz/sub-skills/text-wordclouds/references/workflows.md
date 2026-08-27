# Text and wordcloud workflows

## How text reaches the wordcloud branch

During an `AutoViz` run, columns are classified first. AutoViz combines NLP-like variables and discrete string variables into `discrete_string_vars`. If that list is nonempty, AutoViz downloads NLTK's `popular` bundle and calls `draw_word_clouds` for each selected string column.

## Text-cleaning helpers

`autoviz.AutoViz_NLP` includes helpers for:

- contraction expansion
- URL removal
- HTML removal
- emoji conversion/removal
- punctuation removal
- stopword removal
- lemmatization
- word frequency counting
- wordcloud generation

## Wordcloud workflow shape

```python
from autoviz import AutoViz_Class

AV = AutoViz_Class()
dft = AV.AutoViz(
    "",
    dfte=df_with_text,
    depVar="",
    chart_format="png",
    verbose=2,
    save_plot_dir="autoviz-text-output",
)
```

For classification targets, `draw_word_clouds` can generate target-specific wordclouds. For regression or no-target workflows, it produces a single wordcloud for the text column.

## Testing text behavior

Use a DataFrame with longer, varied strings. Very short or low-cardinality strings may be classified as categorical or boolean instead of text.

## Output behavior

Wordcloud plots use matplotlib and the `wordcloud` package. Static chart formats are the most reliable for automated runs.
