# Inference and chat reference

This reference covers checkpoint loading, chat-template prompting, raw continuation, decoding, and chat command construction.

## Dry-run chat command builder

From this sub-skill directory:

```bash
python scripts/build_chat_command.py --ckpt checkpoints/sft.pt --prompt 'What is 13 + 29?' --greedy
python scripts/build_chat_command.py --ckpt checkpoints/base_pretrained.pt --raw --prompt 'Once upon a time'
python scripts/build_chat_command.py --ckpt checkpoints/grpo.pt --device cuda
```

The helper prints the command only. If `--prompt` is omitted, the generated command starts the repo's interactive REPL.

## Chat CLI command shape

Run from a checkout or environment where the repo package is importable:

```bash
PYTHONPATH=. python scripts/chat.py --ckpt checkpoints/sft.pt --prompt 'What is 13 + 29?' --greedy
PYTHONPATH=. python scripts/chat.py --ckpt checkpoints/base_pretrained.pt --raw --prompt 'Once upon a time'
PYTHONPATH=. python scripts/chat.py --ckpt checkpoints/sft.pt
```

The first command is one-shot chat, the second is base-model raw continuation, and the third starts the interactive REPL.

## `chat.py` flags

| Flag | Meaning | Typical use |
|---|---|---|
| `--ckpt PATH` | Required checkpoint path. | Any base, SFT, DPO, PPO, GRPO, or compatible reward checkpoint. |
| `--prompt TEXT` | One-shot user prompt. | Omit it to start the interactive REPL. |
| `--system TEXT` | Optional system message in chat mode. | Use only for instruction/post-training checkpoints; raw mode ignores chat roles. |
| `--raw` | Raw prefix continuation with no chat template. | Use for a base/pretrained checkpoint. |
| `--max_new_tokens N` | Maximum new tokens to generate. Default is 256. | Keep within the checkpoint's context length. |
| `--temperature X` | Sampling temperature. Default is 0.8. | Higher is more random; ignored operationally when `--greedy` is used. |
| `--top_p X` | Nucleus sampling probability mass. Default is 0.95. | Use values below 1.0 to trim the long tail. |
| `--top_k N` | Top-k sampling cutoff. Default is unset. | Use a positive integer to sample only among the top tokens. |
| `--greedy` | Deterministic argmax decoding. | Use for math checks and reproducible comparisons. |
| `--device DEVICE` | Torch device. Defaults to CUDA when available, otherwise CPU. | Set explicitly for CPU fallback or CUDA diagnosis. |

## Checkpoint loading behavior

`load_model_from_ckpt(ckpt_path, device, overrides=None)` builds a `Transformer` from dimensions saved inside the checkpoint's `cfg` field. Future agents should not ask users to retype model dimensions unless the checkpoint is missing or has a bad `cfg`.

Loader behavior:

1. Load the checkpoint on CPU first.
2. Merge the stored `cfg` with optional overrides.
3. Instantiate `Transformer(n_head, n_embed, context_length, vocab_size, N_BLOCKS)` using stored values or safe defaults.
4. Read `model_state_dict` if present; otherwise treat the checkpoint object as the state dict.
5. Remove `module.` prefixes from DistributedDataParallel checkpoints.
6. Remove `transformer.` prefixes from reward/value-head wrapper checkpoints.
7. Filter state keys to the Transformer backbone before loading with `strict=False`.
8. Move the model to the requested device and set eval mode.

This prefix/key filtering lets generation work with normal stage checkpoints, DDP-saved checkpoints, and reward checkpoints that include extra reward-head parameters. It does not fix a real shape mismatch: if the checkpoint tensors do not match the dimensions in `cfg`, loading should fail and the checkpoint/config must be inspected.

## Chat mode versus raw mode

Choose the mode from the checkpoint stage:

| Checkpoint type | Mode | Why |
|---|---|---|
| Base/pretrained language model | `--raw` | The model was trained for next-token continuation, not role-marked assistant chat. |
| SFT/DPO/PPO/GRPO instruction model | default chat mode | The prompt is wrapped with plain-text role markers and an assistant generation header. |
| Reward checkpoint used only for backbone generation | usually chat mode if initialized from SFT/aligned backbone | Extra reward-head keys are ignored, but generation quality follows the backbone stage. |

Chat mode builds messages with optional system content, user content, and a trailing assistant header. Raw mode encodes the user's text as ordinary tokenizer tokens and continues from that prefix.

## Chat template and decoding facts

- The tokenizer is `r50k_base`.
- The only true special token is end-of-text id `50256`.
- Role markers such as `<|user|>`, `<|assistant|>`, and `<|system|>` are ordinary text, not registered special tokens.
- Reasoning markers such as `<think>` and `<answer>` are also ordinary text learned during SFT/RL.
- Decoding drops end-of-text and padded vocabulary ids at or above `50256`, because the model vocabulary is padded to `50304` while the tokenizer can decode only ordinary ids below `50256`.

## Sampling controls

- `--greedy`: deterministic argmax; best for math prompts, reproducibility, and evaluation-like checks.
- `--temperature`: scales logits before sampling. Low values are conservative; high values are more random.
- `--top_p`: nucleus sampling. Values below `1.0` keep the smallest likely-token set whose cumulative probability crosses the threshold.
- `--top_k`: keeps only the top-k logits before sampling.
- `--max_new_tokens`: generation budget, ultimately limited by the checkpoint's context length.

Do not mix expectations: greedy output should be stable but may be terse; sampled output may be more varied but is not comparable for GSM8K tables.

## Legacy raw generation note

The older raw text generator was base-model-only and depended on the legacy Python config. Prefer `scripts/chat.py --raw` for base continuation because it reads checkpoint dimensions from the checkpoint itself and uses the same generation core as chat/evaluation.

## Minimal API semantics

For code-level guidance, the reusable inference pattern is:

```python
model = load_model_from_ckpt(ckpt_path, device)
reply = generate_reply(
    model,
    user_text,
    device=device,
    system=system_text_or_none,
    raw=False,
    max_new_tokens=256,
    temperature=0.8,
    top_p=0.95,
    top_k=None,
    greedy=False,
)
```

Set `raw=True` only when you want prefix continuation without the chat template.
