---
name: gedi_posterior
description: Compute GeDi generative-discriminator class posteriors from control and anti-control log probabilities using stable Bayes-rule normalization.
---

# GeDi Posterior

## When to use
Use this skill when implementing or checking GeDi-style controlled generation or training and you have class-conditional sequence log probabilities for desired and undesired control codes. Do not use it for ordinary discriminative classifiers that do not compare generative likelihoods.

## Inputs
- Per-class sequence or token log probabilities.
- Sequence length for length normalization.
- Optional class biases/log priors.
- `alpha` normalization scale.

## Outputs
- Stable posterior probabilities over classes.
- Desired-class probability and diagnostic logits.

## Workflow
1. Sum token log probabilities per class if token-level values are provided.
2. Normalize each class log-likelihood by `alpha / length`.
3. Add class bias terms.
4. Apply stable log-softmax; for binary cases, sigmoid of the logit difference is equivalent.
5. Use the returned posterior as input to decoding or discriminative training.

## Validation
Run:

```bash
python tests/test_posterior.py
```

## Limitations
This skill computes the GeDi posterior only. It does not run a language model, tokenize text, or select next tokens.
