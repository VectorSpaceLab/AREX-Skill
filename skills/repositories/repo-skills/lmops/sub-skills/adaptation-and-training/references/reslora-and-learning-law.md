# ResLoRA and Learning Law

## ResLoRA

ResLoRA wraps a base transformer with residual LoRA blocks and a trainer that can swap or merge the low-rank adapters across epochs.

### Core configuration fields

The distilled configuration surface uses these fields:

- `rank`
- `lora_alpha`
- `lora_dropout`
- `start_index`
- `target_modules`
- `lora_num`
- `merge_weights`
- `res_flag`
- `merge_flag`
- `pre_num`
- `merge_4_len`

### Flag meanings

| Field | Meaning |
| --- | --- |
| `res_flag=0` | plain LoRA-like baseline |
| `res_flag=1` | residual variant with merge-aware behavior |
| `res_flag=2` | sequential residual blocks across previous epochs |
| `res_flag=3` | residual block variant with explicit merged behavior |
| `merge_flag=0` | no merge-aware path |
| `merge_flag=3` | bi-directional merge behavior |
| `merge_flag=4` | windowed merge behavior |

### Target-module aliases

The model family chooses alias groups that expand to concrete linear-module names.

| Family | Aliases |
| --- | --- |
| llama | `q`, `k`, `v`, `o`, `f`, `g` |
| mistral | `q`, `k`, `v`, `o`, `f`, `g` |
| roberta | `q`, `k`, `v`, `o` |
| unet | `q`, `k`, `v`, `o` |

### Validation logic to keep

- `merge_flag` should not be used without a residual flag.
- `pre_num` is required for residual modes that chain across epochs.
- Unknown target aliases should be treated as a configuration problem, not silently ignored.
- A model family with no matched target modules should fail early.
- `res_flag` and `merge_flag` combinations that only make sense during evaluation should be called out before training begins.

### Safe helper

Use `scripts/reslora_config_check.py` to validate a proposed configuration and print the expanded target-module plan.

```bash
python scripts/reslora_config_check.py \
  --model-name llama \
  --target-modules q.v \
  --res-flag 1 \
  --merge-flag 3 \
  --pre-num 4
```

## Learning Law

Learning Law optimizes a policy over the learning process itself for two toy families:

- `perceptron`
- `transformer`

### Data families

- `linear` data for the perceptron setting.
- `tinystory` data for the transformer setting.

### Runtime concepts

- The optimization stage learns a gamma policy.
- The evaluation stage replays saved gamma epochs against a chosen policy name.
- The policy-evaluation path can skip CT calculation if requested.
- W&B is optional but present in the trainer surface.
- Distributed execution is expected for the optimization and evaluation trainers.

### Planning checklist

1. Choose the model family: perceptron or transformer.
2. Choose the data family: linear or tinystory.
3. Confirm the data archive has been unpacked into the expected split roots.
4. Choose whether you are optimizing a policy or evaluating an existing one.
5. Confirm whether W&B logging is desired.
6. Confirm the model and data sizes fit the intended GPU budget.

### Important args to track

- `--model-type`
- `--data-names`
- `--opt-gamma`
- `--eval-opt-gamma`
- `--load-gamma`
- `--policy-name`
- `--eval-gamma-epochs`
- `--outer-lr`
- `--outer-epochs`
- `--opt-gamma-wm-steps`
- `--grad-batch-size`
- `--wandb-name`

### Common failure patterns

- The data archive is unpacked to the wrong split names.
- `model_type` is omitted.
- The optimization path and evaluation path are mixed together.
- A gamma checkpoint root is passed to the wrong replay stage.
- W&B is expected but the environment does not permit logging.

## What not to do

- Do not route ResLoRA into the distillation or RL sub-skills.
- Do not claim the Learning Law trainers are heavy production systems; they are toy-but-real optimization loops with explicit data roots and policy files.
- Do not hard-code any private environment location.
