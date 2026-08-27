# Workflows

## Gigaword

1. Prepare the source/target TSV.
2. Use the Gigaword selected columns from the repo script: `0,1`.
3. Run the Gigaword task with the relevant checkpoint.
4. Evaluate the JSON output with the bundled ROUGE helper.

## GLUE-style tasks

The OFA scripts cover the following tasks and selected columns:

| Task | Selected columns | Typical label space | Notes |
| --- | --- | --- | --- |
| CoLA | `1,2` | yes / no | Uses the MCC metric during training. |
| MNLI | `0,1,2` | yes / no / maybe | Uses prompt-type `src` in the repo scripts. |
| MRPC | `0,1,2` | yes / no | Often uses a larger batch size than the other GLUE tasks. |
| QNLI | `1,2,3` | yes / no | Sentence-pair task. |
| QQP | `3,4,5` | yes / no | Sentence-pair task. |
| RTE | `1,2,3` | yes / no | Sentence-pair task. |
| SST-2 | `0,1` | yes / no | Single-sentence sentiment task. |

## Workflow pattern

- The tasks use `train.py` with the same OFA/Fairseq backbone as the vision workflows.
- Prompt type is often `src` for GLUE tasks.
- Selected columns are task-specific and should not be guessed from memory.
- The output metric is usually accuracy or MCC, not a language-model perplexity score.

## ROUGE helper

- `scripts/eval_rouge_json.py` accepts a JSON list of `{hyp, ref}` objects by default.
- Use it when you want a quick metric check on a prediction file without reading the full task code.
