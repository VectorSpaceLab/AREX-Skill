# DARTS genotype reference

This reference covers the genotype schemas used by the CNN and RNN families, the built-in genotype catalog, and the validation rules that future agents should apply before editing or visualizing a cell.

## Quick schema map

| Family | Genotype shape | Key fields | Search parser behavior |
| --- | --- | --- | --- |
| CNN | `Genotype(normal, normal_concat, reduce, reduce_concat)` | two cell graphs plus concat sets | choose the top two non-`none` incoming edges per intermediate node |
| RNN | `Genotype(recurrent, concat)` | one recurrent cell graph plus concat set | choose one predecessor per step and one non-`none` op |

## Shared rules

- A genotype is already discrete. It is the result of the architecture search parser, not the raw architecture weights.
- `none` is part of the search primitive set and means a zero op in the discrete cell.
- The same label can appear in both families. `DARTS` is overloaded, so always name the family when a task could refer to either one.
- Built-in architectures are just predefined genotype constants. They are safe to inspect and visualize without loading the original training code.
- The bundled helper can validate a custom search result from a JSON/mapping spec or a raw `Genotype(...)` expression passed with `--spec`.

## CNN genotype schema

### Shape

`Genotype(normal, normal_concat, reduce, reduce_concat)`

- `normal`: sequence of `(op_name, source_index)` pairs for the normal cell.
- `normal_concat`: indices of the states to concatenate for the normal cell output.
- `reduce`: sequence of `(op_name, source_index)` pairs for the reduction cell.
- `reduce_concat`: indices of the states to concatenate for the reduction cell output.

### Allowed CNN operation names

#### Search-space primitives

These are the primitives used by the architecture search model:

```text
none
max_pool_3x3
avg_pool_3x3
skip_connect
sep_conv_3x3
sep_conv_5x5
dil_conv_3x3
dil_conv_5x5
```

#### Evaluation-time ops

The evaluation cell implementation also understands these additional ops:

```text
sep_conv_7x7
conv_7x1_1x7
```

Use the evaluation-time list when you are validating a fixed architecture such as NASNet or AmoebaNet.

### Built-in CNN genotypes

| Name | Notes |
| --- | --- |
| `NASNet` | Historical CNN baseline; uses `sep_conv_7x7` and `conv_7x1_1x7` in the reduction cell. |
| `AmoebaNet` | Historical CNN baseline; also uses the wider evaluation-only ops. |
| `DARTS_V1` | Early DARTS CNN cell. |
| `DARTS_V2` | Later DARTS CNN cell. |
| `DARTS` | Alias of `DARTS_V2`. |

### CNN validation rules

1. `normal` and `reduce` must each be a sequence of `(op_name, source_index)` pairs.
2. Each of those sequences must have even length.
3. Every operation name must exist in the CNN evaluation op catalog.
4. Every source index must refer to an already available state at that point in the cell.
5. `normal_concat` and `reduce_concat` must contain integer state indices that exist in the corresponding cell.
6. Canonical DARTS cells concatenate intermediate states, so indices `0` and `1` should be treated as unusual even though the runtime model can technically index them.
7. If you edit a custom CNN architecture, do not restrict yourself to the search primitive list when the architecture uses evaluation-only ops.

### CNN search-output interpretation

The CNN search model converts architecture weights into a genotype by:

1. splitting the cell into intermediate steps,
2. ignoring `none` when ranking candidate edges,
3. selecting the two strongest incoming edges for each step, and
4. choosing the strongest non-`none` op on each chosen edge.

The resulting discrete genotype is the one you pass to evaluation-time CNN workflows.

## RNN genotype schema

### Shape

`Genotype(recurrent, concat)`

- `recurrent`: sequence of `(op_name, predecessor_index)` pairs.
- `concat`: indices of the states to average for the final recurrent output.

### Allowed RNN operation names

```text
none
tanh
relu
sigmoid
identity
```

### Built-in RNN genotypes

| Name | Notes |
| --- | --- |
| `ENAS` | Larger fixed recurrent example with 11 recurrent edges. |
| `DARTS_V1` | Early DARTS recurrent cell. |
| `DARTS_V2` | Later DARTS recurrent cell. |
| `DARTS` | Alias of `DARTS_V2`. |

### RNN validation rules

1. `recurrent` must be a sequence of `(op_name, predecessor_index)` pairs.
2. Every operation name must exist in the RNN primitive list.
3. Every predecessor index must point to a state that already exists at that step.
4. `concat` must reference existing recurrent states.
5. Search-derived DARTS recurrent cells normally use 8 steps and a concat range of the last 8 states.
6. `ENAS` is a larger fixed architecture and therefore has a longer recurrent list and a different concat set.

### RNN search-output interpretation

The RNN search model converts architecture weights into a genotype by:

1. considering the states that exist at each step,
2. ignoring `none` when scoring candidate operations,
3. choosing one predecessor state per step,
4. choosing the strongest non-`none` op on that predecessor, and
5. averaging the states selected by the concat list.

## Editing checklist

- Decide the family first: CNN or RNN.
- Check the allowed op list for that family.
- Check that every source/predecessor index exists at the moment it is referenced.
- Check that the concat list only names states the cell can actually produce.
- If the genotype came from search logs, verify that the discrete tuple is already free of architecture weights.
- If the name is `DARTS`, state whether you mean the CNN or RNN alias.
