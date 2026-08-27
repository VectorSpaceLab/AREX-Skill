# FT-Agent contract

## Benchmark registry

The checked-in adapters include math (`aime24`, `aime25`), patent, chemistry, table QA, finance (`FinanceIQ_gen`), and biology benchmark families. Verify the current registry before using a name; a benchmark description must state the expected answer/output format.

## Dataset and generated-data contract

Registered resources are prepared under `FT_FILE_PATH`. Generated training data must satisfy the validator's Alpaca-style `instruction`, `input`, and `output` fields. Preserve the raw/processed dataset version, row count, split, and any filtering or upper-size limit.

## Training/evaluation contract

Record base model id, tokenizer/adapter/merge settings, backend (`docker` or `conda`), device, training budget, checkpoint path, and evaluation command. Keep validation feedback separate from the held-out test result. A score is meaningful only with the same benchmark, prompt/output protocol, and evaluation version.

## Cost and privacy

The first run may download large assets and create external environments. Do not put API keys or private dataset paths in task JSON, generated skill files, or shared logs. Use a bounded `--loop-n` and timeout for a smoke test; reserve full training for an explicitly approved run.
