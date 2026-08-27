# C-Eval Workflow

The bundled C-Eval scripts are thin command-line wrappers around the repo's evaluation logic. They assume the classic C-Eval subject layout and a loadable Chinese-LLaMA-Alpaca-compatible model.

## Expected Directory Layout

```text
/data-root/
  dev/
    subject_name_dev.csv
  val/
    subject_name_val.csv
  test/
    subject_name_test.csv
```

Each CSV should contain at least the standard subject columns. The validator in `scripts/validate_ceval_layout.py` checks the layout and columns before the evaluator runs.

## Main Command

```bash
python scripts/ceval/eval.py \
  --model_path /path/to/hf_model \
  --data_dir /path/to/ceval_root \
  --output_dir /path/to/output \
  --few_shot True \
  --ntrain 5 \
  --with_prompt False \
  --constrained_decoding True
```

Important flags:

| Flag | Meaning |
| --- | --- |
| `--model_path` | Required HF model path loaded by `LlamaTokenizer` and `LlamaForCausalLM`. |
| `--data_dir` | Root containing `dev/`, `val/`, and `test/`. Added by the bundled copy so the current working directory is not special. |
| `--subject_mapping` | Optional path to a subject mapping JSON. Defaults to the bundled file. |
| `--cot` | Chain-of-thought style prompt variant. |
| `--few_shot` | Whether to include dev examples in the prompt. |
| `--ntrain` / `-k` | Number of few-shot examples. |
| `--with_prompt` | Wraps question text in the repo's instruction template. |
| `--constrained_decoding` | Uses next-token answer scoring for A/B/C/D. |
| `--temperature` | Generation temperature for non-constrained runs. |
| `--n_times` | Repeat the evaluation multiple times. |
| `--do_save_csv` | Save per-subject CSVs with model outputs and correctness. |
| `--do_test` | Use `test/` instead of `val/` and suppress answer-based scoring. |
| `--output_dir` | Required output directory. Results are saved under `takeN/`. |

## Output Files

For each `takeN` run, the evaluator writes:

- `submission.json`
- `summary.json`
- optional per-subject `*_test.csv` files when `--do_save_csv True`

## Answer Extraction Notes

The LLaMA evaluator tries constrained next-token answer scoring first when requested and otherwise uses regex-based extraction. If it cannot parse a clear answer, it may fall back to a random choice. That is expected behavior in the source project; do not treat a random fallback as a strong benchmark result.

## Example Benchmark Interpretation

The repo's `examples/` directories provide paired score tables for grouped prompt sets such as QA, OQA, reasoning, literature, entertainment, generation, translation, dialogue, code, and ethics. Those scores were presented as comparative results between different quantized/model variants, not as an absolute or reproducible benchmark standard. Use them to understand tendencies, not to prove universal ranking.
