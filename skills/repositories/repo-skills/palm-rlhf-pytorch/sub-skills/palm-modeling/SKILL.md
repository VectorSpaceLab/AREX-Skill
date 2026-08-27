---
name: palm-modeling
description: "Operate the PaLM transformer core in palm-rlhf-pytorch:
  construction, loss/generation checks, LoRA finetuning scopes, flash-attention
  choices, and reference-only pretraining."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# PaLM Modeling

Use this sub-skill when a task is about the package's base `PaLM` transformer rather than reward models or policy-optimization trainer loops.

## Route Here For

- Constructing a `PaLM` model for autoregressive language modeling or non-causal embedding use.
- Running a tiny loss/backward/logits/embedding/generation smoke check with `scripts/tiny_palm_smoke.py`.
- Understanding `PaLM.forward`, `PaLM.generate`, sampling helpers, embedding/logit return modes, save/load, dropout changes, and LoRA finetune scopes.
- Deciding whether to enable `flash_attn=True`; this package uses PyTorch scaled-dot-product attention, not the external `flash-attn` package.
- Adapting the repository's PaLM pretraining flow as a reference-only recipe without running the expensive source training script.

## Do Not Use This For

- Reward scoring, binned rewards, prompt masks, or implicit process rewards; route those to the `reward-modeling` sub-skill.
- PPO, GRPO, TPO, FlowRL, `RLHFTrainer`, or post-training loops; route those to the `policy-optimization` sub-skill.
- Full-scale enwik8 training or benchmark-quality model recovery. This sub-skill covers mechanics and bounded checks, not long training.

## Start Here

1. For API facts and shapes, read [`references/api-reference.md`](references/api-reference.md).
2. For the distilled pretraining recipe and why the original training flow is reference-only, read [`references/pretraining-workflows.md`](references/pretraining-workflows.md).
3. For common failures, read [`references/troubleshooting.md`](references/troubleshooting.md).
4. To verify an installed package quickly, run the bundled helper instead of any source-repo script:

```bash
python sub-skills/palm-modeling/scripts/tiny_palm_smoke.py --device auto --check-lora
```

If running from inside this sub-skill directory, use:

```bash
python scripts/tiny_palm_smoke.py --device auto --check-lora
```

## Operating Notes

- Prefer device-neutral examples: create a `torch.device`, move model and tensors with `.to(device)`, and avoid README-style unconditional `.cuda()` calls on CPU hosts.
- Keep generation targets explicit: `generate(seq_len, prompt=...)` treats `seq_len` as the target total length. With the default `return_seq_without_prompt=True`, the returned tensor is only the generated suffix of length `seq_len - prompt_len` when `seq_len > prompt_len`.
- Use `palm.palm_parameters()` for base pretraining optimizers and `palm.finetune_parameters(scope)` only after creating a matching LoRA scope.
- `flash_attn=True` compares the torch SDPA backend, not a separate flash-attn dependency. Treat it as an optional acceleration choice.
- The base model can return logits, embeddings, or both; use the tiny smoke helper to confirm the shapes before debugging a larger workflow.
- The source training recipe is reference-only because it is long-running and depends on a missing extra in the repository metadata.

## Common Prompt Patterns

- "Build a small causal LM smoke test" → use the bundled tiny smoke helper.
- "Check generation length or logits shape" → use `return_logits_with_embedding=True` or `return_seq_without_prompt=False`.
- "Add and merge a LoRA scope" → create a fresh unique scope, train only `finetune_parameters(scope)`, then merge intentionally.
- "Should I set `flash_attn=True`?" → yes only when you are intentionally comparing the SDPA path.
- "Can I run the pretraining script unchanged?" → not as a default runtime workflow; treat it as reference-only and note the missing `lion_pytorch` extra.

## Quick Decision Points

- If the task is about next-token loss or embedding shapes, use a tiny PaLM smoke before anything larger.
- If the task is about device portability, use `.to(device)` in examples and avoid unconditional `.cuda()` calls.
- If the task is about LoRA parameters, keep base and adapter optimizers separate unless you explicitly want a merged model.
- If the task is about pretrained weights, remember the repository does not ship a checkpoint.
- If the task is about long training, point the user to the pretraining reference and explain that it is not a smoke path.

## Tiny Verification Checklist

A correct tiny check should:

- instantiate a very small `PaLM` on the selected device;
- compute a scalar loss and call `backward()`;
- confirm logits shape `(batch, seq_len, num_tokens)`;
- confirm embedding shape `(batch, seq_len, dim)`;
- confirm suffix length `seq_len - prompt_len` when the prompt is omitted from the return;
- optionally add, use, remove, and merge a LoRA scope.

## Related Files

- `references/api-reference.md` for verified signatures and generation semantics.
- `references/pretraining-workflows.md` for the distilled training recipe and why it is reference-only.
- `references/troubleshooting.md` for CPU/device, flash-attn, generation, and LoRA issues.
- `scripts/tiny_palm_smoke.py` for the safe runnable smoke check.
