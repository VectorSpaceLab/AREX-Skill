# Troubleshooting

## Focused Test Selection Is Wrong

- If a decoder change selects no model test, map the decoder folder manually to `tests/models/test_<family>.py`; special cases are `deeplabv3` to `tests/models/test_deeplab.py`, `pspnet` to `tests/models/test_psp.py`, `upernet` to `tests/models/test_upernet.py`, and `unetplusplus` to `tests/models/test_unetplusplus.py`.
- If an encoder change selects the wrong group, inspect the nearest class in `tests/encoders/` and its `files_for_diff` pattern.
- If shared base behavior changed, include both `tests/base/` and model tests because `SegmentationModel`, heads, and shared modules affect all decoders.
- If only docs changed, do not run model suites by default; build docs or inspect rendered table changes instead.

## Slow, Downloading, or Marker Tests

- `make test` uses `--non-marked-only`; it intentionally skips marked `logits_match`, `compile`, `torch_export`, and `torch_script` tests.
- `make test_all` sets `RUN_SLOW=1` and includes marked tests, so it can download model fixtures or run much longer.
- Avoid `logits_match` unless the task affects saved checkpoints, pretrained hub loading, or exact output compatibility.
- Use `RUN_ALL=1` only when you need to force diff-gated marker tests outside `main`.
- Use `RUN_ALL_ENCODERS=1` only when broad encoder matrix coverage is explicitly needed.
- Prefer `encoder_weights=None` in new tests unless pretrained metadata or download fallback is the behavior under test.

## Docs Table Is Out of Date

- Encoder registry or pretrained settings changes usually require `make table`.
- Timm compatibility or DPT/timm table changes may require `make table_timm`.
- `misc/generate_table.py` writes `encoders_table.md`; copy or reconcile generated content into docs only if that is the repository’s current maintainer convention for the branch.
- `misc/generate_table_timm.py` enumerates timm models and can be slow because it probes model capabilities; do not run it for unrelated docs edits.
- If the docs build fails after table regeneration, check RST table indentation and heading anchors before changing source code.

## Duplicate Decoder Signature Patterns

- Many model classes repeat the same constructor pattern. When adding a parameter to one family, update the docstring, signature, decoder call, config-loading behavior, and focused tests together.
- For Unet-like families, `decoder_channels` length must track `encoder_depth`; tests in `tests/models/base.py` slice default decoder channels for depth-specific checks.
- DPT uses `decoder_intermediate_channels` rather than the common `decoder_channels` pattern.
- DeepLab and PAN have output-stride or interpolation-specific behavior; update their tests instead of relying only on shared base tests.
- Keep deprecated argument compatibility, such as historical normalization or interpolation aliases, covered by explicit warning tests when touched.

## Ruff Formatting or Lint Failures

- Use `make fixup` for the repository’s configured Ruff check/fix and formatter.
- If Ruff changes generated docs or notebooks unexpectedly, inspect the diff and keep only changes related to the task.
- Keep imports consistent with existing modules; many files import `segmentation_models_pytorch as smp` in tests and use package-relative imports in source files.

## Generated Test Models and Hugging Face Assumptions

- `misc/generate_test_models.py` creates and uploads model fixtures to Hugging Face using private hub credentials; it is not a safe default maintainer command.
- `logits_match` tests may rely on `smp-test-models` or `smp-hub` checkpoints. If those fail due to network or credentials, report that as an environment limitation unless the user explicitly asked to regenerate fixtures.
- Do not add private hub tokens, local cache paths, or credential instructions to docs or public skill content.

## Encoder and Preprocessing Pitfalls

- `tu-` encoder weights accept `True` or `None`; string weights intentionally warn.
- Dilation support is not universal. Tests expect some encoder groups to raise for unsupported dilated mode.
- `get_preprocessing_params` can touch Hugging Face or timm metadata. Use focused tests and mock or deterministic metadata when possible.
- `out_channels` length and output strides must match the selected `depth` expectations in `tests/encoders/base.py`.

## Synthetic Maintainer Cases

Use these hard cases when validating this sub-skill:

1. Add a new optional decoder parameter to `Unet`, wire it through `UnetDecoder`, update the model docstring and interpolation-style tests, run focused non-marked tests, then decide whether marker tests are needed.
2. Add a registry-backed encoder with preprocessing metadata, update exports and docs table guidance, add focused encoder/preprocessing tests, and avoid broad `RUN_ALL_ENCODERS=1` or Hugging Face fixture regeneration unless explicitly requested.
