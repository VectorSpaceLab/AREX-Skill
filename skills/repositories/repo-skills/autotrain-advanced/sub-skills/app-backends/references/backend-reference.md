# Backend reference

AutoTrain backend keys come from `autotrain.backends.base.AVAILABLE_HARDWARE`.

## Local keys

- `local`
- `local-cli`
- `local-ui`

Use local keys when validating parser/data logic, when the user has local compute, or when avoiding hosted auth/network dependencies.

## Hugging Face Spaces keys

Examples include:

- `spaces-cpu-basic`
- `spaces-cpu-upgrade`
- `spaces-t4-small`
- `spaces-t4-medium`
- `spaces-a10g-small`
- `spaces-a10g-large`
- `spaces-a100-large`
- `spaces-l4x1`, `spaces-l4x4`
- `spaces-l40sx1`, `spaces-l40sx4`, `spaces-l40sx8`

Use Spaces keys for hosted training/runtime when artifacts are Hub-accessible and the user has credentials.

## Hugging Face endpoint keys

Endpoint keys begin with `ep-`, for example:

- `ep-aws-useast1-s`
- `ep-aws-useast1-m`
- `ep-aws-useast1-l`
- `ep-aws-useast1-xl`
- `ep-aws-useast1-2xl`
- `ep-aws-useast1-4xl`
- `ep-aws-useast1-8xl`

Use only when the user explicitly wants endpoint-backed execution and has the needed auth/billing context.

## NVIDIA backend keys

NGC/DGX examples:

- `dgx-a100`
- `dgx-2a100`
- `dgx-4a100`
- `dgx-8a100`

NVCF examples:

- `nvcf-l40sx1`
- `nvcf-h100x1`
- `nvcf-h100x2`
- `nvcf-h100x4`
- `nvcf-h100x8`

Use only when the user explicitly provides the required service context.

## Inspect active keys

```bash
python skills/disco/autotrain-advanced/scripts/check_backends.py
```

The exact key list should be treated as the installed package's source of truth.
