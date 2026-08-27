# Text and wordcloud troubleshooting

## NLTK downloads

AutoViz can call:

```python
nltk.download('popular')
```

when discrete string variables are present. In offline environments, either prepare the required NLTK data in advance or avoid triggering the wordcloud branch during automated checks.

## Missing packages

- `ModuleNotFoundError: wordcloud`: install the `wordcloud` package.
- `ModuleNotFoundError: nltk`: install `nltk`.
- `ModuleNotFoundError: textblob` or `emoji`: install AutoViz runtime dependencies.

## Column not classified as text

AutoViz's heuristics distinguish categorical, ID, discrete string, and NLP-like columns. If a string column has only a few short values, it may become categorical rather than text. Use longer and more varied strings when validating wordcloud behavior.

## Wordcloud generation failures

- Confirm the column has nonempty text after cleaning.
- Confirm stopword removal did not remove all tokens.
- Use static `png` or `svg` output for headless execution.
- Use a writable `save_plot_dir` when saving plots.

## Classification target behavior

For classification problems, wordclouds may be generated per target class. Ensure the target column has a small, meaningful set of classes and no misspelled `depVar`.
