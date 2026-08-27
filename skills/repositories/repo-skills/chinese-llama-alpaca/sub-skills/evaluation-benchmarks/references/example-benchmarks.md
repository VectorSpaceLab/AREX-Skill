# Example Benchmark Interpretation

The original project includes manually curated generation examples and paired score tables comparing Chinese Alpaca variants under selected quantization/runtime settings. Use this reference to interpret those examples without overstating them.

## Score Table Meaning

The examples are paired/comparative scores. They compare multiple systems on the same prompts and normalize scores within that comparison. They are not absolute model-quality numbers and should not be mixed across unrelated experiments as if they were the same benchmark.

The source README notes that generation is random and affected by decoding hyperparameters and seeds. Some samples were run multiple times and the best output was selected for scoring, so the results are demonstration evidence rather than a strict reproducibility benchmark.

## Compared Groups

| Group | Compared variants | Quantization/runtime note | Source summary |
| --- | --- | --- | --- |
| `q4_7b-13b` | Alpaca 7B vs 13B | 4-bit quantized | 160 examples; 13B scored higher overall in that table. |
| `q8_7b-13b-p7b` | Alpaca 7B, 13B, Plus-7B | 8-bit quantized | 200 examples; Plus-7B scored highest overall in that table. |
| `q8_13b-p7b-p13b` | Alpaca 13B, Plus-7B, Plus-13B | 8-bit quantized | 200 examples; Plus-13B scored highest overall in that table. |
| `f16-p7b-p13b-33b` | Alpaca Plus-7B, Plus-13B, 33B | 33B FP16 comparison | 200 examples; 33B scored highest overall in that table. |

## Task Categories

The example task files cover:

- Knowledge QA (`QA`)
- Open-ended QA (`OQA`)
- Numerical reasoning and calculation (`REASONING`)
- Literature, poetry, philosophy (`LITERATURE`)
- Entertainment, music, sports (`ENTERTAINMENT`)
- Writing, letters, articles (`GENERATION`)
- Translation (`TRANSLATION`)
- Multi-turn interaction (`DIALOGUE`)
- Code/programming (`CODE`)
- Ethics/refusal (`ETHICS`)

Use these categories to design smoke prompts or qualitative user tests, but do not present them as a complete safety/evaluation suite.

## Reporting Guidance

When a user asks which model is better:

1. Name the exact comparison group and quantization/runtime setting.
2. State that the score is paired/comparative and prompt-set-specific.
3. Mention that prompt templates and decoding parameters matter.
4. Prefer running a task-specific evaluation on the user's own prompts when correctness matters.
5. Use C-Eval for objective multiple-choice NLU-style scoring when the user has the dataset and model assets.

## Common Misreadings

| Misreading | Correction |
| --- | --- |
| "Plus-7B is always better than 13B." | It scored higher in one paired q8 table for that prompt set; other tasks may differ. |
| "The average score is absolute accuracy." | It is a relative paired score in the source examples, not accuracy. |
| "C-Eval and examples measure the same thing." | C-Eval is multiple-choice objective evaluation; examples are qualitative generation prompts. |
| "Scores are deterministic." | Generation and scoring were affected by decoding randomness and scorer choice. |
