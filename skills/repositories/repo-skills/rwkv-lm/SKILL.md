---
name: rwkv-lm
description: "Routes RWKV-LM repository tasks for RWKV training data, RWKV-7
  inference/evaluation, architecture comparison, and RWKV-8 ROSA experiments."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# RWKV-LM

Use this skill for tasks involving the RWKV-LM repository, RWKV-5/6/7/8 model
scripts, RWKV recurrent language-model training, RWKV token/binidx data,
RWKV-7 Goose inference, Qwen/RWKV tensor comparison, or RWKV-8 ROSA research
prototypes.

RWKV-LM is a script-oriented research repository, not a single installable
Python package. Future agents should use this skill to choose the right
repository workflow and avoid mixing version directories, tokenizer families,
training flags, and backend assumptions.

## Quick routing

| User task | Read |
| --- | --- |
| Convert JSONL to RWKV `.bin/.idx`, compute `magic_prime`, or construct MiniPile/Pile training commands | [training-data](sub-skills/training-data/SKILL.md) |
| Decide between RWKV-7 GPT-mode, RNN-mode, fast inference, or MMLU-style evaluation | [inference-evaluation](sub-skills/inference-evaluation/SKILL.md) |
| Explain RWKV-7 tensor names, state shapes, Qwen3.5 export, or context-parallel state composition | [architecture-reference](sub-skills/architecture-reference/SKILL.md) |
| Understand RWKV-8/Heron/ROSA toy scripts, reverse-digit demos, or suffix-automaton behavior | [rosa-experiments](sub-skills/rosa-experiments/SKILL.md) |
| Debug install, backend, tokenizer, data, or checkpoint confusion across workflows | [troubleshooting.md](references/troubleshooting.md) |
| Check whether this skill is current for a checkout | [repo-provenance.md](references/repo-provenance.md) |
| Understand version-directory history | [compatibility-and-history.md](references/compatibility-and-history.md) |

## Minimal environment guidance

For most inspection, prompt rendering, data conversion, and architecture tasks:

```bash
python -m pip install torch numpy rwkv transformers datasets safetensors
```

For RWKV-7 training commands, the repository recommends Python 3.10+, PyTorch
2.5+ or newer, CUDA 12.5+ or a compatible wheel, current DeepSpeed, `ninja`,
`wandb` if logging, and **`pytorch-lightning==1.9.5`**. Do not upgrade Lightning
blindly; the training scripts branch on the Lightning version.

Run the bundled runtime check from this skill tree:

```bash
python scripts/check_runtime.py --check-cuda
```

A passing CUDA allocation proves PyTorch can see the GPU. It does not prove that
RWKV-LM custom CUDA kernels can compile; check `CUDA_HOME`, `nvcc`, and the
specific directory's `cuda/` sources for training or fast inference claims.

## Important repository conventions

- RWKV-7 `RWKV-v7/train_temp` is the current reference training implementation.
- RWKV-6 uses the RWKV-v5 tree with `--my_testing x060`.
- RWKV-7 standard examples use the `rwkv_vocab_v20230424` tokenizer and often
  `vocab_size 65536`.
- Training data is a prefix pair (`<prefix>.bin`, `<prefix>.idx`) passed to the
  trainer without a suffix.
- `magic_prime` depends on token count and context length. Recompute it for
  every corpus or `ctx_len` change.
- Stage-2/3 training resumes by scanning `proj_dir` for `rwkv-*.pth`; inspect
  checkpoint names before resuming.
- Demo scripts in the repository contain maintainer-local absolute checkpoint
  paths. Treat those as placeholders and require user-provided paths.

## Safety boundaries

Do not start network downloads, model checkpoint downloads, full training,
MMLU evaluation, or CUDA source-extension builds unless the user explicitly
requests that operation and the environment is ready. Many native repo examples
are long-running, data-dependent, GPU-dependent, or checkpoint-dependent. When
the user only needs planning, conversion, prompt rendering, or troubleshooting,
use the bundled references/scripts here instead of running original examples.

## Refresh and provenance

Before using this skill for a different checkout, compare the current commit,
major version directories, and public training/inference scripts against
[repo-provenance.md](references/repo-provenance.md). Run `refresh-repo-skill`
if the checkout changed in a way that may affect flags, tokenizers, model
shapes, or backend requirements.
