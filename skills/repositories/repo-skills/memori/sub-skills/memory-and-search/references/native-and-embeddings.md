# Native Core and Embeddings

## Native runtime basics

- The native Rust core is optional at runtime and is used only when BYODB is
  active and `use_rust_core` is enabled.
- `MEMORI_DISABLE_RUST_CORE=1` forces the pure Python path.
- `MEMORI_USE_RUST_CORE=0` also disables the native path.
- The adapter is created only when Memori has a storage connection factory.

## When native help is useful

- Faster embedding/retrieval behavior on BYODB setups.
- More realistic native troubleshooting when the user sees an import or model
  bootstrap failure.
- Confirms that the Python layer can find and use the bundled core extension.

## Model/runtime notes

- The native runtime uses ONNX/runtime assets that are selected by platform.
- Model or runtime downloads are optional setup steps, not required verification
  for the default CPU package path.
- Memori's recall tuning also uses lexical weights from the native core docs:
  `MEMORI_RECALL_LEX_WEIGHT` and `MEMORI_RECALL_LEX_WEIGHT_SHORT`.

## Practical rule

If a user only needs Python package guidance, do not require a native model
bootstrap. If they explicitly need native or embedding behavior, treat runtime
availability and model download as a separate, explicit step.
