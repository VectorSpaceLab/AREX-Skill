# DPKD workflows

DPKD is the direct-preference distillation branch in this sub-skill. Use it for
DPKD training, evaluation, and DPO-style distillation variants. Use the MiniLLM
reference when the request is purely MiniLLM, and use the Tuna reference when
the request is ranking-data finetuning.

## Environment expectations

The documented DPKD setup uses Python 3.11 plus the repository install script.
The runtime imports DeepSpeed, a compatible Transformers fork, PEFT, ROUGE
helpers, tensorboard logging, accelerate, torch, yaml, and related training
utilities. Treat a stock Transformers install as suspect if model-parallel
helpers or DPKD-specific model branches are missing.

## Runner topology

DPKD provides paired train and evaluation runners. The train runner launches the
training entry point; the evaluation runner launches the evaluation entry point.
Both runners share the same planning variables:

- base project path
- student checkpoint name and path
- teacher checkpoint name and path when distilling
- processed data directory
- batch size and eval batch size
- learning rate, weight decay, warmup, and scheduler choice
- max sequence length and max prompt length
- DeepSpeed config path
- random seed and save root

The GPT-2 base recipe uses `torchrun`, sets a single local node by default, and
passes `--type kd`. Training uses `--do-train` and validation; evaluation uses
`--do-eval` and validation. Both enable generation-style evaluation flags.

## Argument groups

DPKD reuses the MiniLLM-style argument layout and extends the model group with
preference-distillation options.

| Group | Important fields |
| --- | --- |
| model | `model-path`, `ckpt-name`, `model-type`, teacher model fields, model-parallel flags, `fp32`/`fp16`/`bf16`, `padding-left`, `seqKD-DPO`, `ipo`, `DPOP`, `reference-free`, `label-smoothing`, `dpo-beta`, `kd-ratio`, `DPOP-lambda`, `db-tmax`, `save-every-epoch`, `LMPTdata`, `simpo` |
| runtime | `type`, train/eval toggles, `base-path`, `load`, `save`, logging and interval flags, `local_rank`, rollout saving, exposure-bias sample count |
| data | raw/processed data paths, force-processing switches, split sizes/ratios, data names, prompt type, workers, JSON/bin/txt mode flags, prompt/lm data dirs, eval switches |
| hp | batch sizes, gradient clipping, max length, seeds, epochs, gradient accumulation, checkpointing, learning rate, scheduler, warmup, weight decay |
| ppo/minillm | rollout counts, clipping, gamma, length normalization, single-step regularization, teacher-mixed alpha, LM coefficient |
| generation | `top-k`, `top-p`, `do-sample`, no-repeat n-gram size, repetition penalty, beams, temperature |
| peft | PEFT mode, LoRA hyperparameters, student and teacher PEFT names/paths |

## Stage semantics

Common `--type` values are:

- `lm`: supervised or language-model style training
- `kd`: teacher/student distillation with DPKD preference flags
- `gen`: generation-only path
- `minillm`: MiniLLM-like rollout stage with LM coefficient
- `eval_main`: generation-quality evaluation
- `eval_exposure_bias`: exposure-bias comparison

DPKD-specific switches layer on top of these stages. For example, the GPT-2
base runner combines KD with `seqKD-DPO`, bfloat16, KD ratio, dynamic beta max,
per-epoch saving, LMPT/LM coefficient settings, and stochastic generation.

## Checkpoint and output conventions

The source argument parser rewrites save paths by embedding the stage, checkpoint
names, batch size, learning rate, gradient accumulation, GPU/node count,
model-parallel size, LoRA fields, DPKD flags, DPO beta, label smoothing, seed,
and LM coefficient. If the output path is surprising, inspect the resolved
arguments rather than only the caller-supplied `--save` root.

Model-family reminders:

- GPT-2 has left/right padding and position-id branches.
- Qwen-related branches prefer bfloat16 behavior in source code.
- Tensor-parallel conversion support differs between MiniLLM and DPKD; use
  `scripts/model_parallel_conversion_plan.py` before planning a conversion.

## Practical planning checklist

Before a DPKD run, confirm:

1. The student and teacher checkpoints are compatible model families.
2. The selected `model-type` is supported by the installed Transformers fork.
3. The processed data directory matches the model family and prompt format.
4. The precision flags match the DeepSpeed config.
5. The DPKD switches are intentional: `seqKD-DPO`, `ipo`, `DPOP`,
   `reference-free`, `simpo`, and `LMPTdata` change the objective.
6. The save path will not overwrite a desired checkpoint.
