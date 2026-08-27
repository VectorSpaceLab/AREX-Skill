# Model Family Overview

This repository revolves around two public model families:

- **Chinese LLaMA**: base/continuation-oriented. Use it for text continuation, continued pretraining, or workflows that do not require the instruction/chat tuning behavior of Alpaca.
- **Chinese Alpaca**: instruction/chat-oriented. Use it for QA, writing, dialogue, advice, and other instruction-following tasks.

The release extends the original LLaMA vocabulary and publishes LoRA adapters. It does not redistribute original full LLaMA weights.

## Size and Variant Guidance

| Variant | Typical use | Practical note |
| --- | --- | --- |
| 7B | easiest to test locally | recommended first smoke target |
| 13B | better quality, higher memory | often requires more VRAM/RAM than 7B |
| 33B | much heavier | only for machines with substantial resources |
| Plus | more training data | generally preferred over older base variants when available |
| Pro | improved instruction behavior | recommended when Plus replies are too short |

## Tokenizer Facts

- LLaMA and Alpaca tokenizers are different.
- Chinese LLaMA expands the vocabulary to `49953`.
- Chinese Alpaca adds a pad token and uses tokenizer length `49954`.
- Do not mix tokenizer families when merging or loading adapters.

## When To Choose Which

| User goal | Family |
| --- | --- |
| Continue raw Chinese text or pretraining-like adaptation | Chinese LLaMA |
| Ask questions, write letters/articles, converse, or follow instructions | Chinese Alpaca |
| Merge an Alpaca adapter with a base model and then generate | Chinese Alpaca after reconstruction |
| Compare model quality using repo example tables | Either family, but note that the tables are paired/comparative |

## Workflow Hints

- For HF inference with instruction prompts, use the Alpaca wrapper (`--with_prompt`) and a matching tokenizer.
- For SFT, the repo scripts expect Chinese Alpaca tokenizer length `49954`.
- For tokenizer extension before reconstruction, use the bundled tokenizer merge helper rather than editing tokenizers manually.
