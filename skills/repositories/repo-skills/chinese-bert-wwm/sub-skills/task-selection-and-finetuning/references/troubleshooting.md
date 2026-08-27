# Troubleshooting: Task Selection and Fine-Tuning

Use this matrix when a user asks why a model choice or fine-tuning run is underperforming, confusing, or inconsistent with the README evidence.

| Symptom | Likely cause | What to check | Recommended response |
| --- | --- | --- | --- |
| User expects exact reproduction of the best README score. | The README reports max and average over 10 random-seed runs; the max is not guaranteed. | Confirm whether the user ran one seed or many; compare against the average in parentheses, not only the max. | Explain max-vs-average reporting and suggest multi-seed runs before judging model quality. |
| User's score is below the reported average. | Hyperparameters, data splits, preprocessing, random seed, batch size, or loading class may differ. | Check learning rate, batch size, max sequence length, warmup/epochs, label mapping, train/dev/test split, tokenizer/model class, and whether the task data matches the benchmark. | Start from the README learning-rate row, rerun a small sweep, and inspect preprocessing before blaming the checkpoint. |
| Performance drops after lowering batch size. | The README FAQ notes that lower batch size can significantly hurt performance. | Compare effective batch size, gradient accumulation, and training steps against the intended setup. | Increase effective batch size if possible or retune learning rate/warmup for the smaller batch. |
| User manually segments Chinese text before downstream fine-tuning because the checkpoint is WWM. | CWS was used only during pretraining sample construction. | Ask whether spaces or word boundaries were inserted solely for WWM. | Remove unnecessary CWS preprocessing; downstream input should be handled as with original Chinese BERT unless the task pipeline independently requires segmentation. |
| User assumes RoBERTa-wwm-ext must be loaded or fine-tuned as original RoBERTa. | The repository describes RoBERTa-wwm-ext as RoBERTa-like BERT, not original RoBERTa architecture. | Check whether the user selected RoBERTa tokenizer/model classes or changed architecture assumptions. | Route loading details to `../model-loading/SKILL.md`; explain that selection can use RoBERTa-wwm-ext benchmarks while loading remains BERT-family. |
| Traditional Chinese QA performs poorly with ERNIE. | The README warns ERNIE's vocabulary has almost no Traditional Chinese characters. | Confirm whether the task is DRCD-like Traditional Chinese and whether conversion to Simplified Chinese was applied. | Prefer BERT/BERT-wwm-family checkpoints for Traditional Chinese; route checkpoint loading to `../model-loading/SKILL.md`. |
| Casual web text, slang, or microblog task underperforms with BERT-wwm. | BERT/BERT-wwm were trained on Wikipedia/formal text; README says ERNIE has an advantage on casual web text because of web data. | Check domain match and whether the task resembles Weibo/casual text. | Validate multiple checkpoints or consider continued pretraining on in-domain data. Do not claim BERT-wwm is always best. |
| Specialized legal, biomedical, finance, or company-internal domain underperforms. | Large domain shift from general pretraining data. | Inspect vocabulary coverage, entity style, corpus genre, and error examples. | Consider additional pretraining on domain/task data before supervised fine-tuning, while noting this repo does not release original pretraining code. |
| User wants to produce a smaller model by taking the first layers of RoBERTa-wwm-ext-large. | Naive truncation is not equivalent to released compact RBT checkpoints. | Ask whether they used released RBTL3/RBT3 or manually truncated a large checkpoint. | Use RBT3/RBTL3 or perform proper continued pretraining. Cite the README caveat: direct 3-layer truncation scored 42.9 / 65.3 on CMRC 2018 versus 63.3 / 83.4 for RBTL3. |
| User asks for RBT4/RBT6 benchmark guarantees. | This checkout lists RBT4/RBT6 as released checkpoints but does not provide the detailed small-model benchmark table for them. | Check whether their claim is based on local validation or assumed from RBT3/RBTL3. | Treat RBT4/RBT6 as intermediate compact candidates; require task-specific validation and exact config inspection after loading. |
| User asks for the repository's original pretraining implementation. | The FAQ says pretraining code is not released. | Confirm whether they need original pretraining reproduction or continued pretraining strategy. | State the gap clearly; suggest using an external maintained BERT/Transformers pretraining workflow if authorized, but do not invent repo-specific code. |
| User assumes published results are universal model rankings. | The repository describes results as empirical under specific conditions and encourages trying models on the target task. | Check task, domain, data size, language variety, and constraints. | Use benchmark tables as priors, then validate on the user's task with tuned learning rates and repeated seeds. |

## Fast diagnostic questions

Ask these before recommending a major model change:

1. What is the task type: span QA, NLI, sentence pair, sentiment, document classification, NER, or another task?
2. Is the text Simplified Chinese, Traditional Chinese, formal, casual web text, or a specialized domain?
3. What is the resource constraint: full large model acceptable, base-size only, or compact/latency-limited?
4. Which checkpoint, tokenizer/model class, learning rate, batch size, max sequence length, and random seed setup were used?
5. Is the reported score a single run, a max over several runs, or an average over runs?

## Stop conditions and gaps

- Stop rather than inventing commands when the user asks for unreleased original pretraining code.
- Route model-id, tokenizer class, cache, and framework errors to `../model-loading/SKILL.md`.
- Route dataset schema, split, label, and benchmark-table detail questions to `../data-and-benchmarks/SKILL.md`.
- Require task-specific validation for RBT4/RBT6 because the distilled repository documentation does not include the detailed benchmark evidence provided for RBT3/RBTL3.
