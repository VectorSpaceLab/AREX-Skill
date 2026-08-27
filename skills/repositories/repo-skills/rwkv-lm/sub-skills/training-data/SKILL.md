---
name: training-data
description: "Guides RWKV-LM data preparation, RWKV-5/6/7 training command
  construction, checkpoint resume behavior, and training-backend
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# RWKV training and data

Use this route when the request mentions RWKV-5, RWKV-6, RWKV-7, MiniPile,
Pile/binidx data, `make_data`, `magic_prime`, `my_exit_tokens`, `train_stage`,
`my_testing`, DeepSpeed, Lightning, checkpoint resume, or training spikes.

## Route by task

- **Prepare a corpus**: read [data-formats.md](references/data-formats.md),
  run the bundled JSONL converter, then run the bundled magic-prime checker.
- **Train RWKV-7**: read [training-workflows.md](references/training-workflows.md)
  before constructing a command. RWKV-7 `train_temp` is the current reference
  implementation; do not mix its flags with the older v5/v6 launcher.
- **Train RWKV-5/6**: read [v5-v6-compatibility.md](references/v5-v6-compatibility.md).
  RWKV-6 is selected through the RWKV-5 training tree with `--my_testing x060`.
- **Resume or debug a run**: read [troubleshooting.md](references/troubleshooting.md)
  and inspect checkpoint names and `train_log.txt` before changing flags.

## Safe preparation sequence

1. Confirm the tokenizer family, vocabulary size, data prefix, total token count,
   context length, model family, and target backend.
2. Convert JSONL only into a new output prefix. Keep the source JSONL unchanged
   and never use a training launcher that deletes checkpoints as a first step.
3. Verify that the output has matching `.bin` and `.idx` files and that each
   document ends with token `0` when using the RWKV v20230424 tokenizer.
4. Compute a `magic_prime` for the exact token count and `ctx_len`; do not copy
   a value from a different context length. The candidate must be prime and
   congruent to `2 mod 3`.
5. Construct an initialization command (`train_stage`/`my_pile_stage` 1) and
   a separate resume command (stage 2/3). Use a fresh `proj_dir` for the first
   run and save the complete command in the run directory.
6. Perform a parser/help check and a tiny data-layout check before allocating
   GPU time. Full training is long-running and requires the checkout's matching
   CUDA extension sources, toolkit, and data files.

## Non-negotiable training rules

- Keep `ctx_len`, `magic_prime`, and `my_exit_tokens` consistent with one data
  prefix. The trainer uses mini-epochs of `40320 * ctx_len` tokens.
- Match `head_size`/`head_size_a` to the model family. RWKV-7 reference code
  expects a head size of 64 for the standard x070 LM configuration.
- RWKV-7 has carefully chosen initialization, parameter-specific learning-rate
  scales, and weight-decay groups. Do not simplify the optimizer grouping and
  assume the same loss curve.
- Set `grad_cp=1` to reduce memory at the cost of speed. Tune `micro_bsz` and
  `head_chunk` before changing architecture flags.
- A checkpoint directory is stateful: stage-2/3 code searches for the latest
  `rwkv-*.pth`. Remove or move stale files only after recording a backup and
  confirming the intended resume point.
- CUDA torch availability is not proof that the repository's custom `.cu`
  extensions can compile. Check `CUDA_HOME`, `nvcc`, compiler ABI, and the
  selected torch CUDA tag separately.

## Bundled helpers

- [convert_jsonl_to_rwkv_binidx.py](scripts/convert_jsonl_to_rwkv_binidx.py)
  creates a new `.bin/.idx` pair from JSONL and validates the round trip.
- [compute_magic_prime.py](scripts/compute_magic_prime.py) reads a binidx
  prefix or an explicit token count and prints the largest valid prime below
  `token_count // ctx_len - 1`.

These helpers are adapted from the repository's data utilities and do not
require the original checkout's hard-coded paths.

## Handoff

After data and command construction, route model generation or prompt sampling
to `inference-evaluation`. Route tensor names, checkpoint conversion, or
context-parallel state questions to `architecture-reference`. Route ROSA
experiments to `rosa-experiments`.
