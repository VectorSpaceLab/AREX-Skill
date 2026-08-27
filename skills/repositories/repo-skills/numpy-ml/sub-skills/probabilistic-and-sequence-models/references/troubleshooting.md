# Troubleshooting

## HMM input shape errors

**Symptom:** `log_likelihood` or a decode method raises an attribute error about
`.ndim` or similar.

**Likely cause:** the sequence was passed as a plain Python list or an invalid
array-like object.

**Recovery:** convert the observation sequence to a NumPy array with the correct
integer state IDs.

## GMM or LDA convergence concerns

These models are iterative and small-sample examples can vary by seed.
Keep the smoke data tiny, set a seed when the constructor supports one, and look
at learned parameters instead of expecting exact numerical equality to another
library.

## n-gram training failures

**Symptoms:** file path errors, empty vocabulary, or probability lookups that
raise missing-count assertions.

**Likely causes:** the corpus file is missing, empty, or tokenized into no usable
words after filtering.

**Recovery:** verify the corpus path, disable stop-word/punctuation filtering for
smoke tests if appropriate, or route tokenization to the preprocessing
sub-skill first.

## Zero probabilities or bad corpus assumptions

If a likelihood is `-inf` or unexpectedly tiny, check whether the model was
trained with the right order `N`, smoothing choice, and vocabulary. For HMMs,
validate that the rows of `A` and `B` are stochastic before training or scoring.

## When to stop and inspect source

If a method name or return contract seems different from the examples here,
inspect the installed API facts or the source file rather than guessing. This
legacy package has multiple model families with similar names but different
calling conventions.
