# Grounding, GUI Knowledge, and GUI-Critic-R1

## Grounding and GUI knowledge benchmarks

The grounding and knowledge scripts expose the same core arguments:

```text
python eval_grounding_benchmarks.py \
  --model_path <checkpoint-or-model> \
  --ds_path <dataset> \
  --save_path <output> \
  --eval_benchmark_type <type>

python eval_gui_knowledge_benchmark.py \
  --model_path <checkpoint-or-model> \
  --ds_path <dataset> \
  --save_path <output> \
  --eval_benchmark_type <type>
```

Use `scripts/build_grounding_eval_command.py` to print the selected command. Live execution needs the model/checkpoint, dataset, compatible inference stack, and often GPU memory.

## GUI-Critic-R1 data validation

GUI-Critic-R1 evaluates critique/judgement data with images, problem text, solution labels, and optional score tags. Validate JSONL before running any model scoring:

```bash
python sub-skills/benchmarks-and-evaluation/scripts/validate_gui_critic_dataset.py --jsonl gui_critic_sample.jsonl
```

Expected row signals include:

- Non-empty image path/list.
- A problem/prompt that includes an image marker and decision/instruction sections.
- `solution`, `label`, or answer values of `Correct`/`Incorrect` when using binary labels.
- `<score>...</score>` tags when downstream scoring parses score tags.

## Credential warning

If adapting source evaluation code for online scoring, replace any sample or hard-coded key with environment-variable lookup before running. Do not paste scoring keys in JSONL, shell history, or benchmark reports.
