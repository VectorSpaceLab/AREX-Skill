# Troubleshooting

## Common failure modes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `--use_gpu False` or `--train_only False` still behaves oddly | The root parser uses `type=bool`, so the literal string `False` is truthy | Use the wrapper's `--cpu` flag for GPU control and let the wrapper normalize `--train_only`; if you invoke the root script directly, avoid bool-looking strings. |
| Autoformer test or predict fails on CPU | The inference autocorrelation path calls `.cuda()` | Run the forward path on CUDA or keep the smoke check in train mode. |
| A CSV cannot be found | `root_path` and `data_path` do not point at the same dataset root | Verify the dataset directory and file name, especially for custom CSVs. |
| `checkpoint.pth` is missing or the test run loads the wrong file | The `setting` string changed between runs | Reuse the exact shape-related arguments or pass the direct checkpoint path to the plotting helper. |
| Weight plotting says a seasonal or trend key is missing | The checkpoint is not a DLinear-style state dict, the keys are prefixed with `module.`, or the run used a different weight layout | Use the helper's key normalization; for `--individual` checkpoints, it falls back to channel 0. |
| Former models raise shape errors | `enc_in`, `dec_in`, `c_out`, `features`, `freq`, or `embed_type` do not match the CSV layout | Recheck the dataset column count and the former-model flags together. |
| The smoke helper fails with a top-k or short-sequence error | The input length is too short for the autocorrelation top-k calculation | Keep the default smoke length or increase `seq_len`. |

## Autoformer-specific notes

- The CPU failure is expected for `test`/`predict` mode because the inference
  branch uses CUDA calls internally.
- If you only need a quick smoke check, use the bundled helper in train mode.
- If you are trying to benchmark the former family on CPU only, route the task
  to Linear, DLinear, or NLinear instead.

## Checkpoint naming and path mismatches

The root launcher builds the checkpoint directory name from the run arguments.
If any of these change between training and testing, the path will no longer
match:

- `model_id`
- `model`
- `data`
- `features`
- `seq_len`
- `label_len`
- `pred_len`
- `d_model`
- `n_heads`
- `e_layers`
- `d_layers`
- `d_ff`
- `factor`
- `embed`
- `distil`
- `des`
- `itr`

When in doubt, copy the exact training command and only change the mode flag.

## Dataset layout reminders

- ETT files are already preprocessed and should be used as provided.
- Custom datasets still need a `date` column and enough feature columns for the
  selected model family.
- The root and FEDformer routes share the same dataset root convention.

## When to route elsewhere

- Statistical baseline issues belong to the sibling baseline route.
- FEDformer-only failures belong to the FEDformer route.
- Pyraformer preprocessing, TVM, or graph-attention issues belong to the
  Pyraformer route.
