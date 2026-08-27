# Model Selection Guide

This guide distills the repository's README and English README into operational advice for selecting Chinese-BERT-wwm family checkpoints for downstream Chinese NLP. It is self-contained and avoids any requirement to reopen the construction source materials.

## Whole Word Masking and Chinese CWS

Whole Word Masking (WWM) changes how masked language-modeling examples are created during pretraining. In ordinary WordPiece masking, subword pieces belonging to the same word may be masked independently. In WWM, if one WordPiece of a word is selected for masking, the other pieces of that same word are masked together. The masking operation is still the standard BERT-style mixture of `[MASK]`, keeping the original token, or replacing with a random token; it is not limited to literal `[MASK]` replacement.

For Chinese, the repository applied WWM by first using Chinese Word Segmentation (CWS) to identify which Chinese characters formed the same word during pretraining. Characters belonging to the same segmented word were then masked together. This CWS step is a pretraining-data construction detail.

**Do not segment downstream inputs just because the checkpoint is WWM.** The repository FAQ explicitly says downstream text is used as with original Chinese BERT: WWM affects pretraining input generation, not the input format for downstream fine-tuning or inference. Use normal BERT-family tokenization in the loading workflow.

## Model comparison dimensions

The repository compares the main released models by masking, size/type, pretraining corpus, training tokens, device, steps, batch size, optimizer, vocabulary, and initialization. Use the table below as the task-selection view; route actual loading details to the model-loading sub-skill.

| Model | Selection role | Corpus and tokens | Size / layers | Pretraining schedule | Optimizer | Vocabulary / init checkpoint | Evidence notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BERT-wwm | Conservative WWM replacement for original Chinese BERT; strong compatibility with BERT-style pipelines and formal text. | Chinese Wikipedia, about 0.4B tokens. | BERT-base: 12 layers, 768 hidden, 12 heads, about 110M parameters. | 100K steps at max length 128 plus 100K steps at max length 512; batch 2,560 / 384. | LAMB for pretraining. | Inherits original Google Chinese BERT vocabulary/config; initialized from original BERT weights. | Good when you want the WWM change without switching to extended-corpus or large checkpoints. |
| BERT-wwm-ext | Base-size WWM model trained on much more data; often a low-risk upgrade over BERT-wwm when resource budget is still base-size. | Extended data: Chinese Wikipedia plus other encyclopedia, news, Q&A, etc.; about 5.4B tokens. | BERT-base shape. | 1M steps at max length 128 plus 400K steps at max length 512; batch 2,560 / 384. | LAMB for pretraining. | Inherits original Google Chinese BERT vocabulary/config; initialized from original BERT weights. | Best first base-size candidate when task is general Chinese and you can use an HFL WWM checkpoint. |
| RoBERTa-wwm-ext | Strong base-size benchmark candidate; keeps BERT-family usage while adopting RoBERTa-like pretraining choices. | Same extended 5.4B-token data. | BERT-base shape. | 1M steps directly at max length 512; batch 384. | AdamW for pretraining. | Inherits original Google Chinese BERT vocabulary/config; initialized from original BERT weights. | Removes NSP and trains in a RoBERTa-like way, but is still handled as a BERT-family model. |
| RoBERTa-wwm-ext-large | Accuracy-first candidate when memory/latency/training cost can support large models. | Same extended 5.4B-token data. | BERT-large: 24 layers, 1024 hidden, 16 heads; about 325-330M parameters in repository tables. | 2M steps at max length 512; batch 512. | AdamW for pretraining. | Inherits original Google Chinese BERT vocabulary/config; random initialization. | Often best in reading comprehension and XNLI tables; high cost and sometimes small gains on simpler classification tasks. |
| RBT3 | Compact RoBERTa-wwm-ext-derived model for tight memory/latency budgets. | Extended-data family. | 3-layer compact model; about 38M parameters in the XNLI-classification parameter calculation. | Initialized from the first 3 layers of RoBERTa-wwm-ext, then continued pretraining for 1M steps. | Not specified in the small-model README evidence. | Parent-family vocabulary/config details should be verified after loading when exact deployment size matters. | Keeps much of classification performance but loses more on MRC tasks than on sentence classification. |
| RBTL3 | Compact model derived from the large checkpoint; use when RBT3 is too small but full large is too heavy. | Extended-data family. | 3-layer compact model; about 61M parameters in the XNLI-classification parameter calculation. | Initialized from the first 3 layers of RoBERTa-wwm-ext-large, then continued pretraining for 1M steps. | Not specified in the small-model README evidence. | Parent-family vocabulary/config details should be verified after loading when exact deployment size matters. | Better than naive truncation of the large checkpoint; stronger than RBT3 in average small-model results. |
| RBT4 / RBT6 | Intermediate compact candidates only when you need a middle size and can validate your own task. | Listed as released HFL RBT checkpoints in the Chinese and English download tables; corpus shown as extended data. | The distilled repository documentation does not provide detailed benchmark rows or pretraining specifications for RBT4/RBT6. | Not stated in the distilled comparison tables. | Not stated in the distilled comparison tables. | Verify exact config after loading. | Do not claim the RBT3/RBTL3 benchmark numbers for RBT4/RBT6; treat them as downloadable compact variants requiring task validation. |

## Task and resource decision workflow

1. **If accuracy is the main objective and resources are sufficient**, start with RoBERTa-wwm-ext-large. It is the strongest reported model for CMRC 2018, DRCD, CJRC, and XNLI in the README tables, and it is also competitive on classification tasks. Expect larger memory, latency, and fine-tuning cost.
2. **If you need a base-size general-purpose default**, start with RoBERTa-wwm-ext or BERT-wwm-ext. Both use the 5.4B-token extended corpus. RoBERTa-wwm-ext has stronger evidence on several long-sequence and NLI benchmarks; BERT-wwm-ext is a conservative BERT-like extension with the original two-stage max-length schedule.
3. **If you need compatibility with original Chinese BERT behavior**, use BERT-wwm. It keeps the original BERT-base shape and vocabulary/config inheritance while adding Chinese WWM pretraining.
4. **If memory or latency dominates**, consider RBT3 or RBTL3 before inventing your own truncated model. RBT3 is smaller; RBTL3 is larger and stronger. RBT4/RBT6 can be considered as intermediate released variants, but the distilled repository documentation does not provide detailed benchmark evidence for them.
5. **If the task domain is far from Wikipedia/news/general Chinese**, consider further pretraining on your own task/domain data before supervised fine-tuning. This is a strategy recommendation, not a repository-provided command.

## Task-specific notes

### Reading comprehension: CMRC 2018, DRCD, CJRC

- The README evidence consistently favors RoBERTa-wwm-ext-large when compute allows.
- RoBERTa-wwm-ext is a strong base-size alternative.
- DRCD is Traditional Chinese span extraction. Prefer BERT/BERT-wwm-family checkpoints over ERNIE for Traditional Chinese; the README warns that ERNIE's vocabulary has almost no Traditional Chinese characters.
- CJRC results in the README are marked as not identical to the final official data, so use them as a directional legal-domain reference rather than a guaranteed official benchmark.

### XNLI and sentence-pair tasks: LCQMC, BQ Corpus

- For XNLI, RoBERTa-wwm-ext-large has the strongest reported dev/test accuracy.
- For LCQMC and BQ, gains among full-size models are smaller and can vary by split. If memory is constrained, compact RBT models are reasonable candidates for sentence matching because their relative classification average is much closer to the base model than their MRC scores are.
- Always tune learning rate on the target split; do not assume a single published row transfers unchanged.

### Sentiment and document classification: ChnSentiCorp, THUCNews

- For ChnSentiCorp, the reported full-size WWM-family results are close; ERNIE is also strong in the README comparison. If you stay within this repository's model family, choose by resource and pipeline compatibility rather than expecting a large guaranteed gain.
- For THUCNews and other longer document tasks, the README tips say BERT/BERT-wwm do well on long-sequence tasks such as document classification. Still respect the downstream implementation's maximum sequence length and chunking/windowing choices.

### Formal, casual, Traditional, and domain-shifted Chinese

- BERT and BERT-wwm were trained on Wikipedia and are recommended in the README for relatively formal text.
- ERNIE is described as advantaged on casual web text such as Weibo because of its extra web data. ERNIE is a comparison point, not a Chinese-BERT-wwm checkpoint; if you use this family on casual or very different domains, plan extra validation or continued pretraining.
- For Traditional Chinese, prefer BERT/BERT-wwm-family checkpoints over ERNIE unless you intentionally convert the text and validate the effect.

## Compact-model caveat

RBT3 and RBTL3 are not equivalent to taking the first three layers of a large model and directly fine-tuning them. The README explicitly warns that directly using the first three layers of RoBERTa-wwm-ext-large for downstream fine-tuning performed much worse on CMRC 2018: 42.9 / 65.3 versus 63.3 / 83.4 for RBTL3. Use released compact checkpoints or a properly continued-pretrained compact model rather than naive truncation.
