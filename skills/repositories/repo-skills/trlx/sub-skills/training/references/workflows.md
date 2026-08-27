# trlX training workflows

This reference gives task-oriented recipes for the Accelerate-backed `trlx.train` stack. It is self-contained and intentionally does not require reopening source examples.

## Before launching any run

1. Confirm the mode:
   - PPO or RFT online: `reward_fn` and `prompts`.
   - ILQL offline: `samples` and `rewards`.
   - SFT causal: `samples` without `rewards`.
2. Start from a default or full YAML config, then run the bundled config inspection helper:

   ```bash
   python scripts/inspect_training_config.py --default ppo
   python scripts/inspect_training_config.py --yaml my_config.yml --json
   ```

3. Check that `config.train.seq_length > config.method.gen_kwargs["max_new_tokens"]` for modes that generate text through `trlx.train`.
4. Set `config.train.tracker = None` for offline, CI, or unauthenticated runs. Default tracking is W&B.
5. For large models, first lower `train.batch_size`, set `train.minibatch_size`, reduce `train.seq_length`, freeze more layers (`model.num_layers_unfrozen=0`), reduce PPO `method.chunk_size`, and consider PEFT.

## Online PPO from reward function and prompts

Use this when rewards are computed from generated text during training.

```python
from typing import Dict, List

import trlx
from trlx.data.default_configs import default_ppo_config

config = default_ppo_config().evolve(
    train=dict(
        total_steps=1000,
        batch_size=8,
        minibatch_size=2,
        seq_length=512,
        checkpoint_dir="ckpts/ppo-run",
        tracker=None,
    ),
    model=dict(
        model_path="gpt2",
        num_layers_unfrozen=2,
    ),
    tokenizer=dict(
        tokenizer_path="gpt2",
        truncation_side="right",
    ),
    method=dict(
        num_rollouts=64,
        chunk_size=8,
        ppo_epochs=4,
        gen_kwargs=dict(max_new_tokens=64, do_sample=True, top_k=0, top_p=1.0),
    ),
)

prompts = [
    {"prompt": "Write a helpful answer about safety:", "category": "safety"},
    {"prompt": "Summarize this article:", "category": "summary"},
]

def reward_fn(
    samples: List[str],
    prompts: List[str],
    outputs: List[str],
    tokenizer=None,
    category=None,
    **metadata,
) -> List[float]:
    # Return one scalar per sample, or one list/tensor of token rewards per sample.
    return [float("helpful" in output.lower()) for output in outputs]

def metric_fn(samples: List[str], prompts: List[str], outputs: List[str], **metadata) -> Dict[str, List[float]]:
    return {"output_chars": [len(output) for output in outputs]}

trainer = trlx.train(
    reward_fn=reward_fn,
    prompts=prompts,
    eval_prompts=prompts[:1],
    metric_fn=metric_fn,
    stop_sequences=["\n\nHuman:"],
    config=config,
)
trainer.save_pretrained("ppo-hf-model")
```

Important online-mode details:

- Prompt items may be strings or dicts. Dicts must contain `"prompt"`; every other key is batched and passed to `reward_fn` and `metric_fn` as metadata.
- `reward_fn` is called with keyword arguments `samples`, `prompts`, `outputs`, `tokenizer`, and prompt metadata. It may return one scalar per generated sample or one token-reward sequence per generated sample.
- `metric_fn` is called during evaluation with the same text arguments and metadata; prefer returning lists of per-sample scalar values.
- `stop_sequences` are stripped from decoded outputs during rollout and evaluation.
- PPO stores `PPORLElement` rows with prompt tokens, response tokens, logprobs, values, and rewards. The trainer clears the rollout store and recollects rollouts after each PPO epoch.

## Online RFT from reward function and prompts

RFT is online like PPO but trains on high-scoring generated completions selected by percentile thresholds. trlX 0.7.0 provides `RFTConfig` and `AccelerateRFTTrainer`, but no `default_rft_config()` factory; construct a `TRLConfig` explicitly or adapt a YAML.

```python
import trlx
from trlx.data.configs import ModelConfig, OptimizerConfig, SchedulerConfig, TokenizerConfig, TrainConfig, TRLConfig
from trlx.trainer.accelerate_rft_trainer import RFTConfig

config = TRLConfig(
    train=TrainConfig(
        seq_length=512,
        epochs=10,
        total_steps=500,
        batch_size=8,
        checkpoint_interval=100,
        eval_interval=50,
        pipeline="PromptPipeline",
        trainer="AccelerateRFTTrainer",
        tracker=None,
    ),
    model=ModelConfig(model_path="gpt2", num_layers_unfrozen=-1),
    tokenizer=TokenizerConfig(tokenizer_path="gpt2", truncation_side="right"),
    optimizer=OptimizerConfig(name="adamw", kwargs=dict(lr=3e-5, betas=(0.9, 0.95), eps=1e-8, weight_decay=1e-6)),
    scheduler=SchedulerConfig(name="cosine_annealing", kwargs=dict(T_max=500, eta_min=3e-5)),
    method=RFTConfig(
        name="RFTConfig",
        n_generations_per_prompt=8,
        start_percentile=0.7,
        end_percentile=0.95,
        n_improve_steps=4,
        gen_kwargs=dict(max_new_tokens=64, do_sample=True, top_k=0, top_p=1.0, temperature=1.0),
    ),
)

trainer = trlx.train(reward_fn=reward_fn, prompts=prompts, eval_prompts=eval_prompts, config=config)
```

RFT caveats:

- The implementation uses a causal LM architecture; do not treat it as a general seq2seq trainer.
- It maintains generations per prompt, scores them on the main process, broadcasts scores, selects completions above a percentile threshold, deduplicates `[prompt, output]` pairs, and trains on the selected text.
- `n_generations_per_prompt` can multiply generation cost quickly.

## Offline ILQL from reward-labeled samples

Use this when scalar rewards already exist for prompt/completion or trajectory samples.

```python
from typing import Dict, List

import trlx
from trlx.data.default_configs import default_ilql_config

config = default_ilql_config().evolve(
    train=dict(
        total_steps=1000,
        batch_size=16,
        seq_length=256,
        checkpoint_dir="ckpts/ilql-run",
        tracker=None,
    ),
    model=dict(model_path="gpt2", num_layers_unfrozen=-1),
    tokenizer=dict(tokenizer_path="gpt2", truncation_side="right"),
    method=dict(
        tau=0.7,
        gamma=0.99,
        cql_scale=0.1,
        awac_scale=1.0,
        alpha=0.001,
        beta=0.0,
        steps_for_target_q_sync=5,
        two_qs=True,
        gen_kwargs=dict(max_new_tokens=56, top_k=20, beta=1, temperature=1.0),
    ),
)

samples = [
    ["Question: 1 + 2 Answer:", "3"],
    ["Question: Say hello. Answer:", "Hello!"],
]
rewards = [1.0, 0.8]

def metric_fn(samples: List[str], prompts: List[str], outputs: List[str], **metadata) -> Dict[str, List[float]]:
    return {"length": [len(output) for output in outputs]}

trainer = trlx.train(
    samples=samples,
    rewards=rewards,
    eval_prompts=["Question: 2 + 2 Answer:"],
    metric_fn=metric_fn,
    config=config,
)
```

Offline data details:

- `samples` may be full strings. A string is treated as one output whose prompt is the tokenizer BOS/EOS fallback.
- `samples` may also be an even-length list per sample: `[prompt_0, output_0, prompt_1, output_1, ...]`. Outputs are the odd positions.
- `rewards` must have the same length as `samples`; trlX normalizes returns internally and attaches final reward to the terminal action token sequence.
- Causal ILQL uses `ILQLRolloutStorage`. Seq2seq ILQL uses `ILQLSeq2SeqRolloutStorage` when `model.model_arch_type="seq2seq"`.
- `steps_for_target_q_sync` controls target Q-head synchronization.

## SFT from samples without rewards

Use SFT when the objective is supervised causal language-model fine-tuning.

```python
from typing import Dict, List

import trlx
from trlx.data.default_configs import default_sft_config

config = default_sft_config().evolve(
    train=dict(total_steps=500, batch_size=4, seq_length=1024, checkpoint_dir="ckpts/sft-run", tracker=None),
    model=dict(model_path="gpt2", num_layers_unfrozen=-1),
    tokenizer=dict(tokenizer_path="gpt2", truncation_side="right"),
    optimizer=dict(kwargs=dict(lr=2e-5)),
    scheduler=dict(kwargs=dict(eta_min=2e-5)),
    method=dict(gen_kwargs=dict(max_new_tokens=128, do_sample=True, top_p=0.95)),
)

# Use [prompt, output] pairs when prompt tokens should be ignored in the loss.
samples = [
    ["### Instruction:\nRewrite positively.\n\n### Response:\n", "This is a useful and friendly answer."],
]

def metric_fn(samples: List[str], prompts: List[str], outputs: List[str]) -> Dict[str, List[float]]:
    return {"output_chars": [len(output) for output in outputs]}

trainer = trlx.train(samples=samples, eval_prompts=[samples[0][0]], metric_fn=metric_fn, config=config)
trainer.save_pretrained("sft-hf-model")
```

SFT data details:

- A list of strings trains on every non-padding token in each string.
- A list of dialogue samples such as `[prompt, output]` uses `DialogStore`; prompt tokens receive label `-100`, so only output tokens train.
- Stock Accelerate SFT uses `AutoModelForCausalLM`; seq2seq SFT is not implemented in the verified 0.7.0 surface.

## Seq2seq/T5 PPO and ILQL

Use seq2seq for T5-style translation, summarization, or conditional generation. Set both model and tokenizer choices explicitly.

```python
config = default_ppo_config().evolve(
    train=dict(seq_length=612, batch_size=4, total_steps=1000, pipeline="PromptPipeline", trainer="AcceleratePPOTrainer"),
    model=dict(model_path="google/flan-t5-large", model_arch_type="seq2seq", num_layers_unfrozen=2),
    tokenizer=dict(tokenizer_path="google/flan-t5-large", padding_side="right", truncation_side="right"),
    method=dict(
        chunk_size=4,
        gen_kwargs=dict(max_new_tokens=100, do_sample=True, top_k=50, top_p=0.95),
        gen_experience_kwargs=dict(max_new_tokens=100, do_sample=False, num_beams=4, temperature=1.0),
    ),
)

prompts = [{"prompt": "Summarize: ...", "reference_summary": "..."}]

def reward_fn(samples, prompts, outputs, reference_summary, **kwargs):
    return [overlap_score(output, ref) for output, ref in zip(outputs, reference_summary)]
```

Seq2seq guidance:

- PPO and ILQL wrappers support `AutoModelForSeq2SeqLMWithHydraValueHead` and `AutoModelForSeq2SeqLMWithILQLHeads`.
- `PromptPipeline` adds special tokens for seq2seq through `trlx.train`.
- For PPO seq2seq, `outputs` are decoded decoder-side generations. For combined `samples`, trlX uses `prompt + tokenizer.sep_token + output`.
- For ILQL seq2seq, pass `[source, target]` sample pairs with one reward per pair.
- Avoid `num_value_layers_unfrozen > 0` for seq2seq value heads; the wrapper marks seq2seq value branching as unsupported.
- Avoid seq2seq SFT and RFT unless you are extending the trainer code outside this skill.

## PEFT and memory-reduction workflow

Use PEFT when full-model fine-tuning is too large or a LoRA/prompt/prefix adapter is desired.

```python
config.model.peft_config = {
    "peft_type": "LORA",
    "task_type": "CAUSAL_LM",      # use "SEQ_2_SEQ_LM" for T5-style models
    "r": 8,
    "lora_alpha": 32,
    "lora_dropout": 0.05,
}
config.model.num_layers_unfrozen = -1  # ignored when PEFT is enabled; keep explicit for readability
config.train.batch_size = 1
config.train.minibatch_size = 1
```

Operational facts:

- `peft_config` may be a PEFT config object or a dict accepted by `peft.get_peft_config`.
- PPO and ILQL wrappers save trainable value/ILQL heads alongside PEFT adapter files. A PEFT PPO/ILQL checkpoint should contain adapter files plus a compact `pytorch_model.bin` for extra heads, not a full base-model dump.
- `num_layers_unfrozen` is ignored when PEFT is active to avoid confusing full-model unfreezing with adapter training.
- LoRA is the safest PEFT choice for seq2seq. Prefix/prompt tuning has special bypass logic during generation and is less broadly verified.
- Model loading in 8-bit is explicitly not supported by the trlX wrapper classes. Bitsandbytes optimizer names are available, but they are separate from loading the model itself in 8-bit.

## Checkpointing, evaluation, and resume

Key fields:

```python
config.train.checkpoint_dir = "ckpts/run-name"
config.train.checkpoint_interval = 100
config.train.eval_interval = 50
config.train.save_optimizer = True
config.train.save_best = True
config.train.resume_from_checkpoint = "ckpts/run-name/checkpoint_100"  # must exist to load
```

Expected behavior:

- Intermediate checkpoints are written below `checkpoint_dir` as `checkpoint_<step>` directories. Padding of `<step>` depends on `total_steps` length.
- Each checkpoint includes an `hf_model` subdirectory from `trainer.save_pretrained(...)`.
- If `save_optimizer=True`, Accelerate optimizer/scheduler/model state is also saved.
- `best_checkpoint` is updated when evaluation reward or `metrics/reward` improves and `save_best=True`.
- `resume_from_checkpoint` is loaded by `trlx.train` only when the path exists.
- `trainer.save_pretrained("output-dir")` saves a Hugging Face-loadable model/tokenizer artifact; for PEFT PPO/ILQL it also preserves the extra value/ILQL heads.

Evaluation facts:

- `eval_prompts` defaults to a batch of BOS tokens for offline modes and to the first prompt batch for online modes if omitted; passing explicit `eval_prompts` is clearer.
- `metric_fn` is called during evaluation with `samples`, `prompts`, `outputs`, and prompt metadata. Return a dict of metric names to lists of scalar values; aggregate scalars can be fragile across table logging.
- If exactly one value in `config.method.gen_kwargs` is a list, evaluation sweeps that generation kwarg over its values and suffixes logged metric keys with `@name=value`.

## Ray Tune sweeps

The sweep CLI is a support workflow; it imports a user training script, runs Ray Tune trials through `AccelerateTrainer`, and can create W&B reports. It is not a safe smoke test.

Training script contract:

```python
def main(hparams={}):
    from trlx.data.configs import TRLConfig
    from trlx.data.default_configs import default_ppo_config

    config = TRLConfig.update(default_ppo_config().to_dict(), hparams)
    # build data/reward_fn, then call trlx.train(..., config=config)
```

Sweep YAML contract:

```yaml
tune_config:
  mode: "max"
  metric: "reward/mean"
  search_alg: "random"     # also supports bayesopt or bohb with extra packages
  scheduler: "fifo"        # hyperband and hyperbandforbohb are recognized
  num_samples: 8

optimizer.kwargs.lr:
  strategy: "loguniform"
  values: [0.000001, 0.001]
method.init_kl_coef:
  strategy: "loguniform"
  values: [0.0001, 0.2]
train.checkpoint_interval:
  strategy: "choice"
  values: [10000000]
```

Recognized search-space strategies include `uniform`, `quniform`, `loguniform`, `qloguniform`, `randn`, `qrandn`, `randint`, `qrandint`, `lograndint`, `qlograndint`, `choice`, and `grid`.

Launch pattern:

```bash
# Optional for an existing cluster; local ray.init() is used if no address is provided.
ray start --head --port=6379

python -m trlx.sweep user_training_script.py \
  --config sweep.yml \
  --accelerate_config accelerate.yml \
  --num_gpus 4 \
  --num_cpus 4 \
  --assume_yes
```

Sweep caveats:

- The CLI prints a warning because it imports the script and all top-level side effects. Keep dataset downloads, model loads, and training inside `main`.
- `--server_address host:port` connects through Ray Client as `ray://host:port`.
- W&B report creation expects W&B access and a valid project/entity context.
- Each trial receives flat dot-path hparams such as `optimizer.kwargs.lr`; use `TRLConfig.update` to merge them.

## Accelerate and DeepSpeed launch patterns

Single node:

```bash
accelerate config
accelerate launch user_train.py
```

Explicit config file:

```bash
accelerate launch --config_file accelerate-zero2-bf16.yaml user_train.py
accelerate launch --num_processes 4 --config_file accelerate-ddp.yaml user_train.py
```

Common config patterns:

- DDP: `distributed_type: MULTI_GPU`, `mixed_precision: bf16` or `fp16`, `num_processes` equal to visible GPUs.
- DeepSpeed ZeRO-2: `distributed_type: DEEPSPEED`, `deepspeed_config.zero_stage: 2`, optional bf16/fp16 mixed precision.
- DeepSpeed ZeRO-3: `zero_stage: 3`, `zero3_init_flag: true`, and `zero3_save_16bit_model: true` when a 16-bit consolidated save is needed.
- trlX disables DeepSpeed fp16 auto-casting of model forward inputs to avoid incompatible argument casts.

Cluster shell wrappers in the source evidence used host-specific conda, SLURM, NCCL/EFA, and Ray assumptions. Treat them as patterns only: define clean environment activation, `CUDA_VISIBLE_DEVICES`, `MASTER_ADDR`, `MASTER_PORT`, node ranks, and scheduler resources for the user's actual cluster rather than copying a hard-coded script.

## Distilled example families

- Random walks: toy graph trajectories as strings. PPO optimizes generated walks with a shortest-path reward/metric; ILQL trains from pre-sampled walks plus reward labels; RFT can generate several candidate walks and keep high-scoring ones. Useful for tiny synthetic usability checks.
- Sentiment: PPO/RFT use a sentiment classifier as `reward_fn`; ILQL uses review labels as rewards; SFT filters to positive examples and trains on text samples. Use small dataset slices for smoke tests.
- T5/seq2seq sentiment, translation, and summarization: set `model_arch_type="seq2seq"`, use right padding/truncation, and pass references through prompt metadata for reward and metric functions.
- Alpaca SFT: build `[prompt, output]` pairs from instruction/input/output rows so prompt tokens are masked and only outputs are trained.
- Helpful/Harmless RLHF: PPO can call a reward model service or local reward model; ILQL maps chosen/rejected completions to positive/negative rewards; SFT trains only selected responses. Full PPO reward-model setups usually require many GPUs and external services.
- Summarization RLHF: staged SFT, reward model, and PPO. Treat full runs as large-GPU workflows with extra metric packages and model checkpoints; for trlX guidance, focus on the PPO prompt metadata/reward function shape.
- Architext-style toy rewards: simple online PPO where `reward_fn` scores generated structured text directly, useful for validating prompt/output/reward flow without external datasets.
