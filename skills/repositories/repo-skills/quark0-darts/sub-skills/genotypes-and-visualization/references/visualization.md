# Visualization reference

This sub-skill provides DOT-only visualization for DARTS genotype objects. The helper mirrors the structure used by the original repo's visualizers, but it does not call Graphviz itself.

## CNN cell graphs

The CNN family has two cell graphs:

- **normal**: the standard cell layout.
- **reduction**: the downsampling cell layout.

Each CNN cell is built the same way:

1. Start with the two previous cell outputs, labeled `c_{k-2}` and `c_{k-1}`.
2. Create one intermediate node per step.
3. Each step has two incoming edges, so the genotype contributes pairs of `(op_name, source_index)` values.
4. For a reduction cell, the underlying model uses stride-2 operations when the source is one of the two previous cell outputs.
5. Concatenate the states named by `normal_concat` or `reduce_concat` to produce `c_k`.

The bundled DOT helper keeps the same node naming convention:

- inputs: `c_{k-2}`, `c_{k-1}`
- intermediate nodes: `0`, `1`, `2`, ...
- output: `c_k`

## RNN recurrent graph

The RNN family has a single recurrent graph.

1. Start with `x_t` and `h_{t-1}`.
2. Combine them into the initial state node `0`.
3. Create one node per recurrent step.
4. Each step selects one predecessor from the states that already exist and applies one op from the primitive list.
5. Average the states named by `concat` to produce `h_t`.

The bundled DOT helper uses the same node names as the source visualizer:

- inputs: `x_t`, `h_{t-1}`
- initial state: `0`
- recurrent states: `1`, `2`, `3`, ...
- output: `h_t`

## Bundled helper

The script lives at [scripts/darts_genotype_tools.py](../scripts/darts_genotype_tools.py).

### Commands

```bash
python scripts/darts_genotype_tools.py list
python scripts/darts_genotype_tools.py show DARTS --schema cnn
python scripts/darts_genotype_tools.py show DARTS --schema rnn
python scripts/darts_genotype_tools.py dot DARTS --schema cnn --cell both --output-dir out/
python scripts/darts_genotype_tools.py dot DARTS --schema rnn --output recurrent.dot
```

### What the helper does

- `list` prints the bundled CNN and RNN genotype catalogs plus the allowed op lists.
- `show` prints a human-readable summary and validation notes for one genotype.
- `dot` emits DOT text to stdout or to files.
- `--spec` can read a JSON mapping, a Python mapping literal, or a source-style `Genotype(...)` expression from a file or stdin.
- The helper never renders through Graphviz by default.

### File output behavior

- CNN `--cell both` writes separate `normal.dot` and `reduction.dot` files when you provide `--output-dir`.
- Single-graph requests can be written with `--output path/to/file.dot`.
- If you want PDF or PNG later, render the DOT yourself after generation.

## DOT conventions

The helper emits plain DOT with a left-to-right layout and rectangular filled nodes so the graph is still readable without external rendering support.

## Optional external rendering

If Graphviz is installed later, you can render the emitted DOT file manually, for example:

```bash
dot -Tpdf out/normal.dot -o normal.pdf
```

That rendering step is optional and not part of the bundled helper's default behavior.
