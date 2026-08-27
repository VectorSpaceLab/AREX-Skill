# API Reference

## Verified source signatures

- `weight_diff.make_diff(path_raw: str, path_tuned: str, path_diff: str, device="cpu")`
- `weight_diff.recover(path_raw, path_diff, path_tuned: Optional[str] = None, device="cpu", test_inference=True, check_integrity_naively=True)`
- `train.smart_tokenizer_and_embedding_resize(special_tokens_dict: Dict, tokenizer: transformers.PreTrainedTokenizer, model: transformers.PreTrainedModel)`

## Shared path-role contract

| role | meaning | execution notes |
| --- | --- | --- |
| `path_raw` | base checkpoint directory | should be the Hugging Face-converted LLaMA model |
| `path_tuned` | tuned checkpoint input or recovery output | required input for `make_diff`; optional output for `recover` |
| `path_diff` | diff checkpoint input or output | released weight diff for `recover`; save target for `make_diff` |

## `make_diff`

- Arithmetic: `diff-minus-raw`, i.e. `state_dict_tuned[key] += -state_dict_raw[key]`.
- Tokenizer rule: if the raw tokenizer has no pad token, call the resize helper before subtracting.
- Save behavior: `path_diff` receives the diff model and tokenizer via `save_pretrained()`.
- Device: pass a string accepted by `torch.device(...)`; the source loads weights in float32.

## `recover`

- Arithmetic: `diff-plus-raw`, i.e. `state_dict_recovered[key] += state_dict_raw[key]`.
- Tokenizer rule: if the raw tokenizer has no pad token, call the resize helper before adding.
- Integrity check: when `check_integrity_naively` is enabled, the source sums all recovered tensor values and compares the scalar against `50637.1836` with `atol=1e-2`.
- Save behavior: if `path_tuned` is `None`, nothing is written; if it is provided, the recovered model/tokenizer are saved there.
- Smoke check: if `test_inference` is enabled, the source runs a short Alpaca-style prompt completion as a qualitative sanity test only.

## Tokenizer resize helper

- `train.smart_tokenizer_and_embedding_resize(...)` adds special tokens, resizes the model embeddings, and initializes new token rows by averaging existing embedding rows.
- The helper is the source-aligned way to keep tokenizer and embedding shapes consistent when the raw tokenizer is missing `[PAD]`.

## Skill-tree helpers

- `scripts/alpaca_weight_diff.py` mirrors the source behavior and adds `dry_run` planning.
- `scripts/build_weight_diff_command.py` prints a safe shell command and never loads checkpoints.
