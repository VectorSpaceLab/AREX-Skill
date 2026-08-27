# Data Preparation Troubleshooting

Stop before training when any data validation fails. Bad masks, bad labels, or
wrong schemas usually waste more time than rerunning preprocessing.

## Missing Python Packages

| Symptom | Likely missing package | Fix |
|---|---|---|
| `ModuleNotFoundError: h5py` | HDF5 reader/writer missing | Install `h5py`; validators and HDF5 data prep require it. |
| `ModuleNotFoundError: numpy` | numeric dependency missing | Install `numpy`; all HDF5 validators use it. |
| `ModuleNotFoundError: tiktoken` | tokenizer missing | Install `tiktoken`; required for data generation and optional HDF5 decode. Validator stats without decode do not need it. |
| `ModuleNotFoundError: datasets` | Hugging Face datasets missing | Install the training/data extra or `datasets` when preparing SFT, preference, or GSM8K RL data. |
| `ModuleNotFoundError: zstandard` | Pile `.zst` streaming missing | Install `zstandard` for raw `.jsonl.zst` preprocessing. |

## Hugging Face, Pile, Network, And Cache Failures

- If the data already exists locally, prefer validating local files over
  redownloading.
- For Hugging Face datasets, set a cache location with enough space, for example
  `HF_HOME=/ephemeral/hf_cache`, or reuse an existing populated cache.
- For Pile/Pile-uncopyrighted `.jsonl.zst`, verify the raw cache directory exists
  and has enough disk before retrying a download.
- If partial downloads leave `*.part` files, remove only the incomplete partial
  file and rerun the same command.
- If network access is unavailable, do not claim the public-data preparation
  succeeded. Ask the user for local raw files, a populated cache, or permission
  to defer data generation.

## Path And Disk Layout Problems

| Symptom | Cause | Fix |
|---|---|---|
| `No such file or directory` for output | Parent data directory was never created | Create the directory first, then rerun. |
| User references a full data path before the data directory exists | Config points at future files | Create the directory and generate/validate files before launching training. |
| HDF5 opens but dataset is missing | Wrong file shape for the stage | Regenerate with the matching pipeline or pass the correct dataset name to `inspect_h5_tokens.py`. |
| Disk fills during Pile/HF prep | Cache and outputs share limited disk | Move cache/output to a larger local disk and rerun from the last safe boundary. |

## Flat HDF5 Token Failures

- **Dataset is not one-dimensional:** the file is probably SFT packed data, not
  pretraining data. Route to `validate_sft_h5.py` or regenerate flat tokens.
- **No `tokens` dataset:** wrong HDF5 schema or dataset name. Inspect the HDF5
  keys or regenerate.
- **Negative ids:** corrupted file or incorrect dtype conversion.
- **Max token id above `50256`:** raw tokenizer data should not contain padded
  model-vocab ids. Regenerate using `r50k_base` and EOT `50256`; do not feed
  model outputs back as pretraining data without filtering.
- **No EOT separators:** real document data was probably encoded without the
  per-document EOT append. Regenerate so document boundaries are learned.

## Packed SFT HDF5 Failures

| Failure | Meaning | Action |
|---|---|---|
| Missing `tokens` or `loss_mask` | Not a packed SFT file | Regenerate SFT data; do not use flat pretraining HDF5 for SFT. |
| Shapes differ | Mask no longer aligns with tokens | Regenerate; manual repair is risky unless you can prove exact alignment. |
| Mask contains values outside `{0,1}` | Loss mask is not binary | Regenerate or normalize only if nonzero truly means assistant token. |
| Mask all zeros | No assistant completion tokens are trained | Check chat roles and context filtering; examples may be missing assistant turns or all examples exceeded context length. |
| Mask all ones | Prompt/user tokens are being trained | Rebuild through chat template; prompt role headers and user content must be masked out. |
| Trained fraction extremely low | Most completions were dropped or truncated | Increase context length, reduce long prompts, or inspect examples. |
| Trained fraction extremely high | Prompt tokens may be included in the loss | Check role parsing and mask generation. |
| Token id above model vocab or below 0 | Bad tokenizer/data corruption | Regenerate with `r50k_base`; verify vocab assumptions. |
| Context length mismatch | File rows do not match stage config | Use matching `--context_length` during prep or update stage config. |

Remember that SFT loss uses `loss_mask[:, 1:]` after next-token shifting. A mask
that looks off by one usually means it was not generated alongside token ids.

## Preference JSONL Failures

- **Invalid JSON line:** repair or remove the row; one malformed row can stop a
  loader that reads the full file.
- **Missing/empty `prompt`, `chosen`, or `rejected`:** row cannot train a pairwise
  preference.
- **`chosen == rejected`:** degenerate pair; remove it before reward/DPO.
- **Very long prompt:** the stage `max_len` may truncate away the response. Use a
  shorter prompt, higher `max_len` within model context, or filter the row.
- **Responses include the prompt text again:** this may be acceptable only if both
  chosen and rejected were normalized consistently; otherwise split prompt and
  response more carefully.

## RL Prompt JSONL Failures

- **Missing or empty `prompt`:** row cannot be rolled out; remove or repair it.
- **`gold` is a string such as `"42"`:** convert to a JSON number `42` or `42.0`.
- **`gold` is nonnumeric text:** verifier reward cannot compare it. Use `null`
  only when the downstream reward policy explicitly supports unlabeled prompts.
- **Arithmetic sanity mismatch:** generated prompt/gold pair is inconsistent; fix
  generation seed/code or remove the row from curriculum.
- **Null gold with verifier reward:** PPO/GRPO verifier reward will score as
  incorrect or uninformative. Use numeric gold for GSM8K/arithmetic verifier runs.

## Context Truncation

The model uses learned absolute positions, so every post-training sequence must
fit within `context_length`. If a user reports missing answer tokens, zero response
mask, or poor preference/RL reward after data prep:

1. Check the configured context length for the consuming stage.
2. For SFT, count skipped examples during preparation; long examples are skipped
   before packing.
3. For preferences, inspect whether `prompt + chosen/rejected` exceeds `max_len`.
4. For RL, ensure `prompt tokens + rollout_len <= context_length`; routing after
   data validation belongs to the post-training skill.

## EOT And Vocab Range Issues

- EOT must be `50256` for this tokenizer and is the only true special token.
- Chat role and reasoning markers are ordinary text, so do not add custom special
  token ids for them.
- Data files generated from text should contain ids in `0..50256`. The model's
  configured vocab may be `50304` to pad the embedding size, but ids `50257..50303`
  should not appear in prepared training data.
- Decode helpers should drop ids outside `0..50255` because `tiktoken` cannot
  decode padded model-vocab ids.
