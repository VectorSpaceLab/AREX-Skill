# Troubleshooting

## Common failure modes

### ROUGE evaluation fails because `datasets.load_metric` changed or `rouge_score` is missing

- Use the bundled `scripts/eval_rouge_json.py` helper.
- Verify that the installed `datasets` package is compatible with the task helper.
- If the helper says `missing optional dependency: rouge_score`, install the ROUGE package before rerunning.
- Make sure the prediction file is a JSON list of objects.

### Gigaword predictions look garbled

- Confirm the source/target TSV order.
- Check the tokenization fixup in the task helper.
- Validate that the selected columns are `0,1`.

### A GLUE task has the wrong label mapping

- Make sure the task name matches the selected columns and the prompt type.
- Do not reuse a CoLA command for MNLI, QQP, or SST-2 without changing the selected columns.
- Inspect the task-specific selected columns before launch.

### Validation metrics look like the wrong score

- Gigaword should report ROUGE-style scores.
- CoLA should report MCC during training.
- The other GLUE tasks usually report accuracy.

## Recovery order

1. Validate the input TSV layout.
2. Confirm the task name and selected columns.
3. Render or inspect the command.
4. Only then run the finetuning or evaluation job.
