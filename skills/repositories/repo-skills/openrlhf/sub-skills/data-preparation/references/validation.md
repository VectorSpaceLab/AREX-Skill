# Data Validation Workflow

Validate OpenRLHF data before launching Ray, vLLM, DeepSpeed, or remote reward services. The goal is to catch schema and formatting mistakes locally, not to prove GPU/runtime readiness.

## Recommended Preflight Order

1. Inspect a few raw records and identify the training mode: SFT, reward model, DPO, or PPO/RL prompts.
2. Map record keys to the matching CLI flags and write them down next to the planned command.
3. Decide whether records are plain strings or chat messages; enable either `--data.input_template` or `--data.apply_chat_template`, not both for the same prompt formatting.
4. Run the bundled validator on a tiny sample.
5. Check rough prompt/response lengths against `--data.max_len` and planned generation limits.
6. For mixed datasets, verify dataset count equals `--data.dataset_probs` count.
7. For VLM prompts, verify image placeholder counts equal non-null image references and do not enable sample packing.
8. Only after local schema checks pass, hand off to the training sub-skill for command construction.

## Bundled Validator

The validator is self-contained and imports only the Python standard library.

```bash
python skills/openrlhf/sub-skills/data-preparation/scripts/validate_openrlhf_dataset.py --help
```

SFT prompt/response example:

```bash
python skills/openrlhf/sub-skills/data-preparation/scripts/validate_openrlhf_dataset.py \
  --mode sft \
  --input tiny_sft.jsonl \
  --input-key question \
  --output-key response \
  --max-samples 50 \
  --max-len-chars 8000
```

Reward or DPO preference example:

```bash
python skills/openrlhf/sub-skills/data-preparation/scripts/validate_openrlhf_dataset.py \
  --mode dpo \
  --input tiny_pref.jsonl \
  --prompt-key prompt \
  --chosen-key chosen \
  --rejected-key rejected \
  --apply-chat-template
```

PPO VLM prompt example:

```bash
python skills/openrlhf/sub-skills/data-preparation/scripts/validate_openrlhf_dataset.py \
  --mode ppo \
  --input tiny_vlm_prompts.jsonl \
  --input-key prompt \
  --image-key images \
  --max-images-per-prompt 4 \
  --require-image-alignment
```

Dataset mix sanity check:

```bash
python skills/openrlhf/sub-skills/data-preparation/scripts/validate_openrlhf_dataset.py \
  --mode ppo \
  --input tiny_prompts.jsonl \
  --dataset-list 'data/a.jsonl,data/b.jsonl,data/c.jsonl' \
  --dataset-probs '0.1,0.4,0.5'
```

## What the Validator Checks

- Required mode-specific keys exist.
- Required values are not null or empty.
- Chat-template inputs look like `[{"role": ..., "content": ...}]` lists when expected.
- SFT `--data.multiturn` has assistant turns and does not rely on a separate output field.
- Reward/DPO chosen and rejected values are both present and not identical.
- DPO without `prompt_key` and with chat templates uses trajectory-style chosen/rejected lists.
- PPO prompt data can include optional label and datasource fields.
- `dataset_probs` count matches dataset count and values parse as floats.
- Rough character length can warn about likely `--data.max_len` truncation/filtering.
- VLM `<image>` placeholder counts match non-null image references when alignment is required.

## What Still Requires OpenRLHF Runtime

- Tokenizer-accurate `--data.max_len` filtering.
- Exact chat-template rendering and response slicing.
- HuggingFace dataset script execution and remote dataset loading.
- Image decoding through PIL and VLM processor tensor creation.
- Packing, ring-attention, flash-attn, DeepSpeed, Ray, or vLLM runtime checks.

## Interpreting Results

- Any `ERROR` should block training command construction until the data or key flags are fixed.
- `WARNING` messages can be acceptable for exploratory samples, but review each warning before expensive jobs.
- If zero records are checked, verify the input file format and `--max-samples` value.
- If many records are filtered by rough length warnings, reduce prompt length, increase `--data.max_len`, or split long conversations before training.

## Synthetic Verification Cases to Keep

- Mixed SFT JSONL where one record lacks the configured output key; expect an error that includes the record index and missing key name.
- VLM prompt with two `<image>` placeholders and one image reference; expect an image alignment error and troubleshooting guidance about media-token alignment.
