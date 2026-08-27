# Fine-Tuning and Reproducibility Guide

This reference captures the repository's fine-tuning tips, best learning-rate table, and reproducibility cautions for downstream Chinese NLP tasks.

## Best initial learning rates from the README

The repository reports best initial learning rates for BERT, ERNIE, and BERT-wwm-family models. The `BERT-wwm*` column covers BERT-wwm, BERT-wwm-ext, RoBERTa-wwm-ext, and RoBERTa-wwm-ext-large in the README. The authors note that for BERT-wwm-ext, RoBERTa-wwm-ext, and RoBERTa-wwm-ext-large they did not further tune the best learning rate; they directly reused BERT-wwm's best learning rate.

| Task | BERT | ERNIE | BERT-wwm* |
| --- | ---: | ---: | ---: |
| CMRC 2018 | 3e-5 | 8e-5 | 3e-5 |
| DRCD | 3e-5 | 8e-5 | 3e-5 |
| CJRC | 4e-5 | 8e-5 | 4e-5 |
| XNLI | 3e-5 | 5e-5 | 3e-5 |
| ChnSentiCorp | 2e-5 | 5e-5 | 2e-5 |
| LCQMC | 2e-5 | 3e-5 | 2e-5 |
| BQ Corpus | 3e-5 | 5e-5 | 3e-5 |
| THUCNews | 2e-5 | 5e-5 | 2e-5 |

Use this table as a starting grid, not a final hyperparameter contract. The README tips emphasize that initial learning rate is very important and should be tuned for the target task.

## Practical tuning procedure

1. Start from the table row for the closest task type.
2. Sweep nearby learning rates before drawing model-quality conclusions. A simple first sweep is one lower value, the table value, and one higher value around the published starting point.
3. Keep batch size, maximum sequence length, warmup, epochs/steps, and random seed visible in experiment records. Batch-size changes can materially affect reported performance.
4. Compare both best and average behavior across seeds. Do not choose solely from a single lucky run.
5. If switching from BERT/BERT-wwm to ERNIE or vice versa, retune learning rate. The README explicitly says ERNIE's best learning rates differ substantially and are generally higher in the reported table.

## Model-family fine-tuning notes

### BERT-wwm and BERT-wwm-ext

- Use when you want original Chinese BERT compatibility with WWM pretraining benefits.
- BERT-wwm-ext is usually a better first candidate than BERT-wwm when base-size resources are acceptable because it uses the 5.4B-token extended corpus.
- The same BERT-wwm learning-rate starting points were used for BERT-wwm-ext in the README tables, but task-specific tuning is still required.

### RoBERTa-wwm-ext and RoBERTa-wwm-ext-large

- Use for stronger reported benchmark performance, especially reading comprehension and XNLI.
- RoBERTa-wwm-ext is RoBERTa-like in pretraining choices: WWM, no NSP, max length 512 directly, and extended training steps. It is not original RoBERTa architecture for downstream loading.
- RoBERTa-wwm-ext-large is the accuracy-first option but increases memory and training cost. On some sentence classification tasks, gains over base-size checkpoints are modest, so validate cost/performance.

### RBT3, RBTL3, RBT4, and RBT6

- Use compact RBT checkpoints for memory/latency constraints, especially when classification-style performance is more important than span-extraction MRC performance.
- RBT3 and RBTL3 have explicit README small-model evidence. RBT3 has about 38M parameters; RBTL3 has about 61M parameters. Their relative average classification scores are much closer to the base model than their MRC scores are.
- RBT4 and RBT6 are listed as released checkpoints, but the distilled repository documentation does not provide the same detailed benchmark or training rows for them. Treat them as intermediate compact candidates that require your own validation.
- Do not directly truncate RoBERTa-wwm-ext-large and assume it is equivalent to RBTL3. The README reports much worse CMRC 2018 performance for direct three-layer truncation.

## Long text, formal text, and Traditional Chinese

- The README tips say BERT/BERT-wwm are strong for formal text because they were trained on Wikipedia.
- For long-sequence tasks such as machine reading comprehension and document classification, the README suggests BERT/BERT-wwm. Among the released WWM-family models, the benchmark tables often favor RoBERTa-wwm-ext-large when resources allow.
- For Traditional Chinese, choose BERT or BERT-wwm-family checkpoints rather than ERNIE. The repository reports that ERNIE's vocabulary has almost no Traditional Chinese characters and DRCD is a Traditional Chinese QA benchmark.

## Domain shift and continued pretraining

If the downstream data is extremely different from the general-domain pretraining data, the README recommends another pretraining step on task/domain data before supervised fine-tuning. Treat this as a strategy requirement, not a repository-provided executable workflow:

- The repository FAQ says original pretraining code is not released.
- Do not invent a repository-specific pretraining script or command.
- If continued pretraining is needed, use an external, maintained BERT/Transformers workflow and document the new corpus, tokenizer compatibility, checkpoint lineage, and validation task.

## Reproducibility expectations

The repository's benchmark protocol used 10 runs with different random seeds for each model and reports maximum score plus average score in parentheses. Interpret results accordingly:

- The number outside parentheses is the maximum over runs; it is not guaranteed in a single rerun.
- The number inside parentheses is the average over runs and is a better stability signal.
- If a reproduced run falls below the average, first check data preprocessing, label mapping, tokenizer/model class, learning rate, batch size, sequence length, random seed, and train/eval split before concluding the checkpoint is wrong.
- The FAQ says classification tasks used a simple Google BERT `run_classifier.py` baseline. This is evidence about the simplicity of the benchmark setup, not a bundled script in this generated skill.
- The FAQ warns that reducing batch size can significantly reduce performance.

## Reporting checklist for future experiments

When a Researcher reports fine-tuning results based on this family, include:

- Checkpoint name and model size family.
- Task and dataset split.
- Initial learning rate and any sweep range.
- Batch size, maximum sequence length, epochs/steps, warmup, optimizer, and framework.
- Random seeds and whether the result is a single run, maximum over runs, or average over runs.
- Whether the task uses Simplified Chinese, Traditional Chinese, casual web text, formal text, or a specialized domain.
- Whether any continued pretraining was performed and, if so, on what data.
