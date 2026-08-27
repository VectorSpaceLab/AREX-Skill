# trlX training configuration guide

trlX training is controlled by a `TRLConfig` containing `train`, `model`, `tokenizer`, `optimizer`, `scheduler`, and `method` sections. Use this guide before launching training, sweeps, or distributed jobs.

## Pick the smallest correct starting config

| Task | Recommended start | Required call shape |
| --- | --- | --- |
| PPO online RLHF | `default_ppo_config()` | `trlx.train(reward_fn=..., prompts=..., config=config)` |
| RFT online rejection fine-tuning | Explicit `TRLConfig(..., method=RFTConfig(...), trainer="AccelerateRFTTrainer")` | `trlx.train(reward_fn=..., prompts=..., config=config)` |
| ILQL offline RL | `default_ilql_config()` | `trlx.train(samples=..., rewards=..., config=config)` |
| Causal SFT | `default_sft_config()` | `trlx.train(samples=..., config=config)` |
| T5/seq2seq PPO or ILQL | PPO/ILQL default evolved with `model_arch_type="seq2seq"` | PPO uses prompts/reward function; ILQL uses paired samples/rewards |
| NeMo/Megatron | Not this sub-skill | Route to `../nemo/SKILL.md` |

Use explicit configs in production. The implicit `config=None` path warns and infers PPO/ILQL/SFT from arguments; it is less reproducible.

## Required config sections

A full YAML or dict must contain every top-level section below.

```yaml
train:
  seq_length: 512
  epochs: 10
  total_steps: 1000
  batch_size: 8
  checkpoint_interval: 100
  eval_interval: 50
  pipeline: "PromptPipeline"
  trainer: "AcceleratePPOTrainer"
  tracker: null
  checkpoint_dir: "ckpts/example"

model:
  model_path: "gpt2"
  model_arch_type: "causal"
  num_layers_unfrozen: 2
  peft_config: null
  model_extra_configs: {}

tokenizer:
  tokenizer_path: "gpt2"
  padding_side: "left"
  truncation_side: "right"
  tokenizer_extra_configs: {}

optimizer:
  name: "adamw"
  kwargs:
    lr: 3.0e-5
    betas: [0.9, 0.95]
    eps: 1.0e-8
    weight_decay: 1.0e-6

scheduler:
  name: "cosine_annealing"
  kwargs:
    T_max: 1000
    eta_min: 3.0e-5

method:
  name: "PPOConfig"
  num_rollouts: 64
  chunk_size: 8
  ppo_epochs: 4
  init_kl_coef: 0.05
  target: 6
  horizon: 10000
  gamma: 0.99
  lam: 0.95
  cliprange: 0.2
  cliprange_value: 0.2
  vf_coef: 1.0
  scale_reward: null
  ref_mean: null
  ref_std: null
  cliprange_reward: 10
  gen_kwargs:
    max_new_tokens: 64
    do_sample: true
    top_k: 0
    top_p: 1.0
```

Notes:

- Method names are resolved case-insensitively through a lowercased registry.
- `model_extra_configs` and `tokenizer_extra_configs` are passed to Hugging Face model/tokenizer loading.
- Keep `gen_kwargs.max_new_tokens` present for `trlx.train`; the entrypoint computes max prompt length from it.
- `train.tracker` accepts `"wandb"`, `"tensorboard"`, or `null`/`None`.

## `TRLConfig.load_yaml`, `update`, and `evolve`

### Load a YAML

```python
from trlx.data.configs import TRLConfig

config = TRLConfig.load_yaml("my_config.yml")
```

This reads YAML, converts sections to dataclasses, and resolves `method.name` through the method registry. If loading a custom RFT YAML in a script, import `RFTConfig` before calling `load_yaml` so the method is registered:

```python
from trlx.trainer.accelerate_rft_trainer import RFTConfig  # registers rftconfig
from trlx.data.configs import TRLConfig

config = TRLConfig.load_yaml("rft_config.yml")
```

### Apply sweep/user hparams with `TRLConfig.update`

Use `update` when incoming overrides are flat dot-path keys, such as Ray Tune sweep parameters.

```python
from trlx.data.configs import TRLConfig
from trlx.data.default_configs import default_ppo_config

base = default_ppo_config().to_dict()
hparams = {
    "optimizer.kwargs.lr": 1e-5,
    "method.init_kl_coef": 0.02,
    "train.save_best": False,
}
config = TRLConfig.update(base, hparams)
```

`update` accepts either flat keys (`"optimizer.kwargs.lr"`) or nested dicts (`{"optimizer": {"kwargs": {"lr": 1e-5}}}`). It returns a new `TRLConfig`. It validates that top-level sections exist, but still inspect the summarized config because deeply nested typos can be ignored if they do not match existing keys.

### Use `evolve` for explicit Python edits

Use `evolve` when starting from an existing `TRLConfig` object and applying nested section edits in Python.

```python
config = default_ilql_config().evolve(
    train=dict(total_steps=2000, batch_size=16, tracker=None),
    model=dict(model_path="gpt2", num_layers_unfrozen=-1),
    optimizer=dict(kwargs=dict(lr=5e-5)),
    method=dict(two_qs=False, gen_kwargs=dict(max_new_tokens=48, top_k=20, beta=1, temperature=1.0)),
)
```

`evolve` deep-merges and returns a new `TRLConfig`; it is usually clearer for hand-written training scripts.

## Valid trainer / method / data combinations

| Mode | `train.trainer` | `method.name` | `train.pipeline` | `trlx.train` arguments | Model arch notes |
| --- | --- | --- | --- | --- | --- |
| PPO | `AcceleratePPOTrainer` | `PPOConfig` / `ppoconfig` | `PromptPipeline` | `reward_fn`, `prompts`, optional `eval_prompts`, `metric_fn` | causal and seq2seq supported |
| RFT | `AccelerateRFTTrainer` | `RFTConfig` / `rftconfig` | `PromptPipeline` | `reward_fn`, `prompts`, optional `eval_prompts`, `metric_fn` | causal only in stock trainer |
| ILQL | `AccelerateILQLTrainer` | `ILQLConfig` / `ilqlconfig` | `PromptPipeline` | `samples`, `rewards`, optional `eval_prompts`, `metric_fn` | causal and seq2seq supported |
| SFT | `AccelerateSFTTrainer` | `SFTConfig` / `sftconfig` | `PromptPipeline` | `samples`, optional `eval_prompts`, `metric_fn` | causal only in stock trainer |

Mismatch symptoms:

- `config.method must be ILQLConfig` from ILQL trainer means the YAML method name or registry import is wrong.
- Missing or wrong `reward_fn`/`samples` mode raises `ValueError` from `trlx.train`.
- `samples` and `rewards` length mismatch raises before training.
- Seq2seq SFT attempts are unsupported because the SFT trainer loads `AutoModelForCausalLM`.

## Train section tuning

| Field | Practical guidance |
| --- | --- |
| `seq_length` | Maximum token context used for prompts/samples. For online generation, prompt length budget is `seq_length - max_new_tokens`. |
| `batch_size` | Per-process training dataloader batch size. Effective online default prompt batch considers `WORLD_SIZE`; memory use still depends on per-process data/model. |
| `minibatch_size` | Optional microbatch size. Must divide `batch_size`; lower it for memory pressure. |
| `epochs` / `total_steps` | Trainers cap computed loop length by `total_steps`. Set both intentionally. |
| `checkpoint_interval` | Save every N optimizer steps and at the final step. Set high during sweeps to reduce storage. |
| `eval_interval` | Evaluation/generation frequency. Lower values improve monitoring but add expensive generations. |
| `save_best` | Saves `best_checkpoint` by reward/metric when true. |
| `save_optimizer` | Saves full Accelerate state when true. Disable only if resumability is not needed. |
| `resume_from_checkpoint` | Loaded only if the path exists. |
| `rollout_logging_dir` | PPO-only rollout text/tensor history export. Directory must already exist. |
| `trainer_kwargs` | Extra kwargs passed to trainer constructor. Use only for known trainer extensions. |

## Model and tokenizer section tuning

- `model.model_path` and `tokenizer.tokenizer_path` should usually match unless using a compatible tokenizer from another checkpoint.
- `model.model_arch_type` must be `"causal"` or `"seq2seq"`.
- `model.num_layers_unfrozen` controls layer freezing when PEFT is not active. `-1` unfreezes all; `0` freezes bottom transformer layers and embeddings; positive values keep only the top N layers trainable.
- `model.peft_config` may be a dict or PEFT config object. Use `task_type="CAUSAL_LM"` for causal and `task_type="SEQ_2_SEQ_LM"` for seq2seq.
- `tokenizer.padding_side` is commonly `"left"` for causal generation and `"right"` for T5/seq2seq examples.
- `tokenizer.truncation_side` controls which side of long prompts/dialogues is truncated.

## Optimizer and scheduler sections

Supported optimizer names are `adam`, `adamw`, `sgd`, `adam_8bit_bnb`, and `adamw_8bit_bnb`.

Supported scheduler names are `cosine_annealing` and `linear`.

Typical settings:

```python
config.optimizer.name = "adamw"
config.optimizer.kwargs = dict(lr=3e-5, betas=(0.9, 0.95), eps=1e-8, weight_decay=1e-6)
config.scheduler.name = "cosine_annealing"
config.scheduler.kwargs = dict(T_max=config.train.total_steps, eta_min=3e-5)
```

Bitsandbytes optimizer names require bitsandbytes to be installed and do not imply 8-bit model loading support.

## Accelerate and DeepSpeed config notes

trlX does not require source-repository accelerate YAMLs. Create a user-owned Accelerate config and launch the user training script.

DDP-style config shape:

```yaml
compute_environment: LOCAL_MACHINE
distributed_type: MULTI_GPU
mixed_precision: bf16
num_processes: 8
num_machines: 1
gpu_ids: all
use_cpu: false
```

DeepSpeed ZeRO-2 shape:

```yaml
distributed_type: DEEPSPEED
mixed_precision: bf16
deepspeed_config:
  zero_stage: 2
  gradient_accumulation_steps: 1
  gradient_clipping: 1.0
  offload_optimizer_device: none
  offload_param_device: none
  zero3_init_flag: false
```

DeepSpeed ZeRO-3 adds:

```yaml
deepspeed_config:
  zero_stage: 3
  zero3_init_flag: true
  zero3_save_16bit_model: true
```

Launch examples:

```bash
accelerate config
accelerate launch user_train.py
accelerate launch --config_file accelerate-zero2-bf16.yaml --num_processes 4 user_train.py
```

For multi-node launchers, provide the scheduler-specific environment and ranks outside trlX. Do not copy host-specific SLURM or shell wrappers; distill their shape into your cluster's own launch mechanism.

## Sweep config notes

Sweep YAMLs are not `TRLConfig` YAMLs. They contain a `tune_config` block and dot-path search spaces. The training script must merge trial hparams into a real `TRLConfig` with `TRLConfig.update`.

```yaml
tune_config:
  mode: "max"
  metric: "reward/mean"
  search_alg: "random"
  scheduler: "fifo"
  num_samples: 32

optimizer.kwargs.lr:
  strategy: "loguniform"
  values: [0.000001, 0.001]
model.num_layers_unfrozen:
  strategy: "choice"
  values: [-1, 2, 6]
train.save_best:
  strategy: "choice"
  values: [false]
```

Use high `checkpoint_interval` and `save_best=false` during broad sweeps unless checkpoint storage is explicitly needed.
