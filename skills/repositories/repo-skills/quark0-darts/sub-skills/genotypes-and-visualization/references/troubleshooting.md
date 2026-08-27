# Genotype and visualization troubleshooting

Use this when a genotype cannot be resolved, validated, or visualized safely.

## Common failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `unknown architecture name` or no built-in match | The name is misspelled, missing from the selected family, or `DARTS` was used without a CNN/RNN schema. | Run `python scripts/darts_genotype_tools.py list`, then retry with `--schema cnn`, `--schema rnn`, or a qualified name such as `cnn:DARTS`. |
| Operation not in primitive list | A custom genotype uses an op name that the chosen schema cannot execute. | For CNN, check both search primitives and evaluation-time ops. For RNN, use only `none`, `tanh`, `relu`, `sigmoid`, or `identity`. |
| Predecessor index points to the future | A CNN `source_index` or RNN `predecessor_index` names a state that has not been created yet. | Walk the cell step by step. CNN step `i` can use the two input states plus earlier intermediate nodes. RNN step `i` can use recurrent states `0..i`. |
| Concat output is wrong or crashes | The concat list names a state outside the cell, duplicates states unexpectedly, or mixes input and intermediate states. | Ensure concat entries reference existing states. Canonical CNN cells concatenate intermediate nodes; canonical DARTS RNN cells usually average the last recurrent states. |
| Graphviz import or binary is missing | The old visualizers rendered PDFs directly through Graphviz. | Use the bundled `dot` command to emit DOT text or files. Only run external `dot -Tpdf` if Graphviz is already available. |
| CNN/RNN schema mixup | A CNN genotype has `normal`/`reduce` fields; an RNN genotype has `recurrent`/`concat`. The overlapping names `DARTS`, `DARTS_V1`, and `DARTS_V2` are family-specific. | Choose the schema explicitly before listing, showing, validating, or generating DOT. Do not pass a CNN genotype to RNN workflows or vice versa. |

## Fast diagnosis

1. Identify the family first: CNN or RNN.
2. Run `python scripts/darts_genotype_tools.py list` and verify the architecture name.
3. Run `python scripts/darts_genotype_tools.py show NAME --schema FAMILY` and review validation messages.
4. If the genotype is custom, compare its fields against [genotype-reference.md](genotype-reference.md).
5. Generate DOT with `dot` only after the `show` summary reports no structural errors.

## Interpreting ambiguous `DARTS`

`DARTS` is an alias in both families. A bare `DARTS` name is not enough context for future agents. Use one of these instead:

```bash
python scripts/darts_genotype_tools.py show DARTS --schema cnn
python scripts/darts_genotype_tools.py show DARTS --schema rnn
python scripts/darts_genotype_tools.py show cnn:DARTS
python scripts/darts_genotype_tools.py show rnn:DARTS
```

## Missing Graphviz is not a blocker

DOT generation is self-contained. A missing Graphviz Python package or missing `dot` binary only blocks rendering to PDF/PNG, not inspection or DOT output.
