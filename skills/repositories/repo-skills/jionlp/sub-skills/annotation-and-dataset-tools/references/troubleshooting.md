# Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `word2tag` fails with `np.unicode` | NumPy is too new | Use NumPy `1.23.5` or another 1.x release older than 1.24.
| `tag2word` / `tag2entity` returns partial data | The tag sequence does not follow the expected BI or BIOES scheme | Check the label schema and keep the `chars` length identical to the tag length.
| `TokenSplitSentence` or `TokenBreakLongSentence` produces confusing offsets | The wrapper and model function use different length limits | Keep `max_sen_len` aligned across the full pipeline.
| `analyse_dataset` gives empty valid/test splits | The corpus is tiny or highly imbalanced | Use a larger corpus or relax the split ratio for smoke tests.
| `LexiconNER` misses an entity | The text does not match the trie exactly | Normalize the input string or expand the entity dictionary.
| `check_person_name` misclassifies an obvious non-name | The helper is heuristic, not a full name model | Treat it as a quick filter only.
