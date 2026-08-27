---
name: sft-and-pretraining
description: "Guides agents creating Axolotl SFT and continual pretraining
  configs, LoRA or QLoRA recipes, preprocessing workflows, checkpoint resumes,
  sample packing, and stability triage."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SFT and Pretraining

Use this sub-skill when the task is to fine-tune with Axolotl using supervised fine-tuning, adapt a pretraining recipe, create a LoRA or QLoRA starter config, debug SFT/pretraining loss behavior, reason about checkpoint resume fields, or decide whether to run preprocessing before training.

Axolotl is config-driven: produce or edit a YAML config first, validate it, then use the same config with `axolotl preprocess`, `axolotl train`, `axolotl inference`, and `axolotl merge-lora` as appropriate.

## Read First

- [references/workflows.md](references/workflows.md) for SFT, completion-style pretraining, streaming pretraining, validation order, and checkpoint/resume workflow.
- [references/training-options.md](references/training-options.md) for LoRA/QLoRA/full fine-tune choices, core config fields, packing, batch sizing, output fields, and preprocessing reuse.
- [references/troubleshooting.md](references/troubleshooting.md) for NaN/loss spikes, OOM, tokenizer mismatch, packing length issues, dataset-prepared reuse, checkpoint confusion, and network/model path problems.
- [scripts/make_minimal_sft_config.py](scripts/make_minimal_sft_config.py) for a safe local helper that emits a starter SFT YAML without downloading models, loading datasets, or starting training.

## Route Boundaries

- Use this sub-skill for default SFT, chat-template/input-output/completion training flow, continual pretraining, minimal config construction, `axolotl preprocess` before expensive runs, `output_dir`, checkpoints, resume, `dataset_prepared_path`, and SFT/pretraining stability triage.
- Route dataset schema details, custom field mappings, and prompt-format mechanics to `data-and-configs`.
- Route DPO, IPO, KTO, ORPO, SimPO, reward modeling, GRPO, and EBFT to `preference-tuning` or `rl-and-rewards`.
- Route model architecture quirks, tokenizer/model loading internals, LoRA target-module internals, and adapter compatibility to `model-loading-and-adapters`.
- Route DeepSpeed/FSDP launch topology, throughput tuning, vLLM serving, and distributed performance to `distributed-and-performance`.
- Route complete CLI catalog, installation, fetching examples, inference UI, and operational command details to `cli-and-operations`.

## Quick Workflow

1. Pick the workflow: SFT via `datasets`, non-streaming pretraining via `datasets: [{type: completion}]`, or streaming pretraining via `pretraining_dataset`.
2. Choose the training mode: LoRA for a common adapter baseline, QLoRA for 4-bit memory pressure, or full fine-tune when all weights should update and hardware allows it.
3. Create a config with `base_model`, dataset source/type, `output_dir`, sequence/batch settings, optimizer/LR, precision, checkpoint fields, and adapter fields when needed.
4. Run `axolotl preprocess <config.yaml>` for non-streaming data when you want to validate tokenization, label masking, or reusable `dataset_prepared_path` before training.
5. Run `axolotl preprocess <config.yaml> --debug` when label masking, chat template behavior, or empty/overlong examples are suspected.
6. Only after validation, run `axolotl train <config.yaml>` in the user’s prepared Axolotl environment.

For a starter YAML, use:

```bash
python sub-skills/sft-and-pretraining/scripts/make_minimal_sft_config.py \
  --base-model NousResearch/Llama-3.2-1B \
  --dataset-path ./chat.jsonl \
  --dataset-type chat_template \
  --adapter qlora \
  --output-dir ./outputs/chat-qlora
```

The helper only writes YAML to standard output or to a requested file; it does not inspect models, access the network, load datasets, or train.
