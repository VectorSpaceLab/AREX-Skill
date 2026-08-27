# RWKV-5 and RWKV-6 compatibility

RWKV-6 is trained through the `RWKV-v5` tree. The repository's RWKV-6 README is
short but explicit: use the RWKV-v5 code and add `--my_testing x060` to the
training command. RWKV-5 final uses x052-style flags; RWKV-6 uses x060; later
launchers sometimes also include x070 experiments in the v5 tree.

## Main flag differences

| Family | Directory | Selector | Head flag | Stage flag | Notes |
| --- | --- | --- | --- | --- | --- |
| RWKV-5 final | `RWKV-v5` | `--my_testing x052` | `--head_size_a` | `--my_pile_stage` | Older v5 code path and CUDA kernels. |
| RWKV-6 | `RWKV-v5` | `--my_testing x060` | `--head_size_a` | `--my_pile_stage` | Use this when the user asks for v6 training. |
| RWKV-7 current | `RWKV-v7/train_temp` | `--my_testing x070` | `--head_size` | `--train_stage` | Preferred reference for current RWKV-7 work. |

Do not mix `--train_stage` from `train_temp` into the v5 script, and do not mix
`--my_pile_stage` into the v7 `train_temp` script.

## Data compatibility

RWKV-v5 utilities can create a `uint16` binidx pair with the v20230424 tokenizer,
which is also relevant for newer 65,536-vocab training. Older Pile checkpoints
and older v4/v4neo examples may use the 20B tokenizer JSON and a 50k vocabulary;
make the tokenizer/vocab_size explicit whenever porting commands.

## Precision and stability

The v5/v6 code warns that fp16 may overflow after long training and recommends
bf16/tf32 where possible. If the user sees spikes, inspect:

- `beta2`, `adam_eps`, `weight_decay`, and `weight_decay_final`.
- Whether weight decay is applied only where intended.
- Whether `lr_init`, `lr_final`, and warmup match model size and data scale.
- Whether the run accidentally loaded an older checkpoint from `proj_dir`.

## When to route elsewhere

- Use `training-data` for v5/v6 data conversion and launch-command questions.
- Use `inference-evaluation` for running checkpoints.
- Use `architecture-reference` when the question is about x052/x060/x070 block
  internals or tensor names.
