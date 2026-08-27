# Evaluation troubleshooting

## Data layout

- C-Eval needs its `subject_mapping.json` next to the evaluator script and benchmark CSVs under the expected `data/` layout.
- CMMLU needs an `input_dir` with `test/` and `dev/` CSV folders.
- LongBench prediction needs the bundled config JSON files and may need dataset downloads or cache access.

## Model loading

- The benchmark scripts load HF model directories and assume enough memory for generation.
- Long-context evaluation should use a checkpoint and NTK settings that match the intended context length.
- GPU is recommended for real benchmark runs; parser/help and metric-only checks can run without a model.

## Output issues

- Use a fresh `output_dir` per run because scripts create `takeN/`, `pred/`, or `pred_e/` subtrees.
- If per-subject CSVs are missing, check whether the save flag was enabled.
- If a summary score looks impossible, inspect extracted A/B/C/D answers and constrained-decoding settings before blaming the model.

## Optional dependencies

- LongBench scoring uses `jieba`, `rouge`, and `fuzzywuzzy`.
- FlashAttention/xformers warnings are acceleration-related and do not necessarily invalidate metric computation.
