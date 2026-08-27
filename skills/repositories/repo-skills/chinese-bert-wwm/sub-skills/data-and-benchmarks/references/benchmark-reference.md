# Benchmark Reference

The repository reports partial downstream baselines for Chinese BERT-family models. Use these tables to interpret task/metric expectations and relative model behavior, not as guaranteed reproduction targets.

## Global interpretation rules

- Reading-comprehension tasks report `EM / F1`.
- Classification, natural language inference, sentence-pair matching, and document classification tasks report `Accuracy`.
- Values outside parentheses are the maximum score over 10 runs; values in parentheses are the average score over 10 runs.
- The README warns that exact results vary with random seed, compute device, implementation details, and especially batch size. Maximum scores are not guaranteed reproduction targets.
- For model choice and fine-tuning hyperparameters, route to `../task-selection-and-finetuning/SKILL.md`; this reference only explains benchmark data and metrics.

## Best learning rates used in the baseline table

| Task | BERT | ERNIE | BERT-wwm family |
| --- | ---: | ---: | ---: |
| CMRC 2018 | 3e-5 | 8e-5 | 3e-5 |
| DRCD | 3e-5 | 8e-5 | 3e-5 |
| CJRC | 4e-5 | 8e-5 | 4e-5 |
| XNLI | 3e-5 | 5e-5 | 3e-5 |
| ChnSentiCorp | 2e-5 | 5e-5 | 2e-5 |
| LCQMC | 2e-5 | 3e-5 | 2e-5 |
| BQ Corpus | 3e-5 | 5e-5 | 3e-5 |
| THUCNews | 2e-5 | 5e-5 | 2e-5 |

`BERT-wwm family` means BERT-wwm, BERT-wwm-ext, RoBERTa-wwm-ext, and RoBERTa-wwm-ext-large in the README baseline section.

## Task metrics and caveats

| Dataset | Task type | Metric in README | Split columns reported | Caveats |
| --- | --- | --- | --- | --- |
| CMRC 2018 | Simplified Chinese extractive reading comprehension | EM / F1 | Development, Test, Challenge | SQuAD-style span extraction; challenge set is much harder than normal dev/test. |
| DRCD | Traditional Chinese extractive reading comprehension | EM / F1 | Development, Test | Traditional Chinese; README advises against ERNIE for Traditional Chinese because of vocabulary coverage. |
| CJRC | Legal/judiciary reading comprehension | EM / F1 | Development, Test | Repository evidence notes the experiment data is not identical to the official final data, and the test set is in-house and cannot be provided. |
| XNLI | Natural language inference | Accuracy | Development, Test | Three-way classification: entailment, neutral, contradiction/contradictory. |
| ChnSentiCorp | Binary sentiment analysis | Accuracy | Development, Test | Included archive uses TSV columns `label` and `text_a`. |
| LCQMC | Sentence-pair semantic matching | Accuracy | Development, Test | Source-pointer-only; copyright restriction prevents direct download link. |
| BQ Corpus | Sentence-pair semantic matching, banking domain | Accuracy | Development, Test | Source-pointer-only; copyright restriction prevents direct download link. |
| THUCNews | Document-level text classification | Accuracy | Development, Test | README says a 10-category subset was used; full data is external and large. |

## Reported baseline highlights

The table below summarizes the best (non-parenthesized) test-set score for the strongest README model on each main task, only to orient expectations.

| Dataset | Strongest listed model in README table | Test-set score format | Strongest listed test score |
| --- | --- | --- | --- |
| CMRC 2018 | RoBERTa-wwm-ext-large | EM / F1 | 74.2 / 90.6 |
| DRCD | RoBERTa-wwm-ext-large | EM / F1 | 89.6 / 94.5 |
| CJRC | RoBERTa-wwm-ext-large | EM / F1 | 62.4 / 82.2, with in-house data caveat |
| XNLI | RoBERTa-wwm-ext-large | Accuracy | 81.2 |
| ChnSentiCorp | RoBERTa-wwm-ext-large | Accuracy | 95.8 |
| LCQMC | ERNIE in the listed table by max test score | Accuracy | 87.2; RoBERTa-wwm-ext-large reports 87.0 |
| BQ Corpus | RoBERTa-wwm-ext-large | Accuracy | 85.8 |
| THUCNews | BERT and BERT-wwm tie by max test score | Accuracy | 97.8 |

## Small-model table context

The README also reports small-model comparisons for RBT3 and RBTL3 on CMRC 2018, DRCD, XNLI, CSC, LCQMC, and BQ. Use that table for compact-model tradeoff discussions, but remember:

- It lists test results only.
- CMRC and DRCD remain `EM / F1`; XNLI, CSC, LCQMC, and BQ are classification-style scores.
- The parameter percentages are calculated relative to RoBERTa-wwm-ext.
- Directly truncating the first three layers of RoBERTa-wwm-ext-large is not equivalent to RBTL3; that warning belongs primarily in `../task-selection-and-finetuning/SKILL.md`.

## Reproduction cautions

- The repository states that the experiments use simple downstream models, such as Google's `run_classifier.py` for classification tasks, but it does not bundle executable fine-tuning code.
- If a user's result is below the reported average, investigate implementation bugs, data schema mismatches, preprocessing, batch size, random seed, and hyperparameter differences.
- If a user's result does not reach the reported maximum, do not call that a failure by itself; the README explicitly says the maximum has random factors and is not guaranteed.
- The repository disclaimer says results only represent empirical behavior under certain datasets and hyperparameter combinations and should not be treated as conclusive model properties.
