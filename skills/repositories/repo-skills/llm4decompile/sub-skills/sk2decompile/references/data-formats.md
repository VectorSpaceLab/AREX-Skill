# SK²Decompile Data Formats

## Normalized pseudo-code records

The normalization helpers expect a JSON list. Each item contains a pseudo-code field such as `pseudo`, `ida_pseudo`, or `ida_pseudo_norm` depending on the pipeline stage.

The output adds a new normalized field named `<key_name>_norm`.

## Two-stage inference input

`scripts/sk2decompile_inf.py` accepts JSON or JSONL input. Each item should contain:

- `opt`: optimization level (`O0`-`O3`),
- `language`: usually `c` or `cpp`,
- `index`: benchmark index,
- `func_name`: original function name,
- the selected decompiler field, defaulting to `ida_pseudo_norm`.

The script writes:

- `gen_result_model1` for the structure-recovery output,
- `gen_result_model2` for identifier-recovery output,
- `gen_result_model2_stripped` when function-name stripping is enabled,
- per-function `.log` files and an `inference_results.jsonl` summary.

## BringUpBench `func_map.jsonl`

Each line joins source, pseudo-code, normalized pseudo-code, binary, and assembly:

```jsonc
{
  "source": {
    "path": "ackermann/ackermann.c",
    "function_name": "ackermann",
    "content": "int ackermann(...) { ... }\n"
  },
  "pseudo": {
    "path": "ackermann/ackermann.host.O0.pseudo",
    "function_name": "ackermann",
    "address": "0x11e9",
    "label": "ackermann",
    "content": "..."
  },
  "pseudo_normalize": "int ackermann(...) { ... }",
  "binary": "ackermann/ackermann.host.O0",
  "assembly": "<ackermann>:\n..."
}
```

## BringUpBench inference output

`func_map.infer.jsonl` extends the mapping with:

- `pseudo.content-fix`: final decompiled function used for replacement,
- `infer-out-model1`: phase 1 output,
- `infer-out-model2`: phase 2 output,
- `pseudo_normalize-fix`: corrected normalized pseudo-code.

## RL reward data

The VERL reward path expects Parquet data rows containing:

- `prompt`: chat-format prompt messages,
- `data_source`: reward dispatch key,
- `reward_model.ground_truth`: expected IR or source code,
- `reward_model.style`: usually `rule`,
- `extra_info.header`: optional C header declarations for compilability rewards.
