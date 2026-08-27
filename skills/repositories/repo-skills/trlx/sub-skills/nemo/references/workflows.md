# NeMo workflows

These workflows are distilled from the trlX NeMo trainer/model sources, the NeMo installation notes, the NeMo model README, the LLaMA-to-NeMo example README, and the NeMo example scripts. They are guidance only: the current inspection env passed CUDA torch smoke, but NeMo/Apex/Megatron were not installed, so do not claim backend verification.

## 1) Decide whether NeMo is the right backend
Use the NeMo sub-skill only when the task is specifically about:
- `.nemo` checkpoints or rank-sharded Megatron checkpoints
- `NeMoPPOTrainer`, `NeMoILQLTrainer`, `NeMoSFTTrainer`
- `PPOGPT`, `ILQLGPT`, or `SFTGPT`
- tensor/pipeline parallel configuration for Megatron-style training or inference
- converting a Hugging Face LLaMA checkpoint into NeMo format

If the task is ordinary trlX PPO / ILQL / SFT / RFT with Accelerate, or if it mainly concerns reward functions, samples/rewards, PEFT, or sweeps, route to `../training/SKILL.md` instead.

## 2) Minimal setup sequence
1. Confirm the environment actually has a NeMo stack and Apex available.
2. Match the NeMo version to the repository evidence for the target workflow. The source docs disagree on the exact historical pin, so treat the exact version as an environment decision, not a guaranteed constant.
3. Pick a base config with `default_nemo_1_3b_config()`, `default_nemo_2b_config()`, or `default_nemo_20b_config()`.
4. Keep `trainer_kwargs.megatron_cfg` and `trainer_kwargs.pretrained_model` aligned with the checkpoint layout you intend to load.

## 3) Convert a Hugging Face LLaMA checkpoint into NeMo format
The conversion recipe is:
- input: Hugging Face LLaMA checkpoint path
- output: a NeMo checkpoint directory containing weight shards and a matching YAML
- required arguments: `model_path`, `output_folder`, `total_tp`, and `name`

Distilled shape:

```bash
python <converter> \
  --model_path <hf_llama_checkpoint> \
  --output_folder <nemo_output_dir> \
  --total_tp <tensor_parallel_degree> \
  --name <short_model_name>
```

What the converter produces:
- `model_weights.ckpt` for single-shard tensor parallel
- `mp_rank_XX/model_weights.ckpt` when tensor parallel degree is greater than 1
- a matching `megatron_<name>.yaml` that records the parallel sizes and model dimensions

Rules of thumb:
- `total_tp` must match the tensor-parallel degree you plan to use later.
- The generated YAML should be the one passed through `trainer_kwargs.megatron_cfg`.
- After conversion, the NeMo checkpoint directory itself becomes the `pretrained_model` root.

## 4) Train with trlX using a NeMo trainer
Use the same `trlx.train` entrypoint as the Accelerate path, but set the trainer and NeMo kwargs explicitly.

Distilled config shape:

```python
config = default_config.evolve(
    train=dict(
        trainer="NeMoPPOTrainer",   # or NeMoILQLTrainer / NeMoSFTTrainer
        trainer_kwargs=dict(
            megatron_cfg=<yaml_name_or_omega_conf>,
            pretrained_model=<checkpoint_root_or_none>,
        ),
    ),
)
```

Trainer-specific notes:
- `NeMoPPOTrainer` expects a `PPOConfig` method and uses `reward_fn`/`prompts`.
- `NeMoILQLTrainer` expects an `ILQLConfig` method and offline `samples`/`rewards`.
- `NeMoSFTTrainer` expects an `SFTConfig` method and offline `samples`.
- If `megatron_cfg` is a string, the trainer resolves it from the bundled NeMo config directory; if it is an OmegaConf object, it is used as-is.
- `pretrained_model` may be `None`, a NeMo model directory, or a converted `.nemo` directory.

Important mapping behavior:
- `config.train.batch_size` becomes NeMo global batch size after data-parallel scaling.
- `config.train.minibatch_size` becomes the NeMo micro batch size when provided.
- `config.train.seed` is copied into the NeMo model seed.
- `config.optimizer` is copied into `model.optim`.
- `config.scheduler` is copied into `model.optim.sched`.
- PPO validation is disabled inside the NeMo trainer and handled by trlX instead.

## 5) Save, resume, and infer from checkpoints
### Save / resume
Use the NeMo exp manager fields to control logs and checkpoints:
- `exp_manager.explicit_log_dir` sets the output root
- `exp_manager.create_checkpoint_callback` enables checkpointing
- `exp_manager.resume_if_exists` controls auto-resume
- `exp_manager.resume_ignore_no_checkpoint` avoids failing when nothing exists yet

### Load checkpoint layout
The wrappers expect one of these shapes:
- single-shard: `<checkpoint_root>/model_weights.ckpt`
- tensor-parallel shards: `<checkpoint_root>/mp_rank_XX/model_weights.ckpt`

The loading code reshares weights for pipeline parallelism before it loads them into the wrapped NeMo model.

### PPO inference flow
Use the PPO wrapper with reference-model construction disabled when you only want generation:
- build the trainer with `num_nodes=1`
- set `trainer.devices` to `tensor_model_parallel_size * pipeline_model_parallel_size`
- verify data-parallel world size is 1
- construct `PPOGPT(..., build_reference_model=False)`
- call `load_from_pretrained(<checkpoint_root>)`
- generate from BOS-prefixed prompts

### ILQL inference flow
The ILQL inference recipe is stricter:
- load the NeMo YAML
- set `trainer.num_nodes=1`
- set `trainer.devices` to the model-parallel world size
- set `model.resume_from_checkpoint` to the checkpoint root
- initialize model-parallel state, then inject the checkpoint rank into the path before loading
- call `ILQLGPT.load_from_checkpoint(...)`
- disable sequence parallelism and activation checkpointing for inference generation if needed

### SFT load / inference flow
The SFT wrapper follows the same checkpoint-shard logic as ILQL:
- `load_from_pretrained(<checkpoint_root>)` resolves `mp_rank_XX/model_weights.ckpt` when needed
- `generate(...)` reuses the wrapper’s sampling settings and temporarily toggles inference-only behavior

## 6) Default selection workflow
Use the default config helpers as the first choice before editing a raw YAML. The source example recipes often switch between the 1.3B / 2B / 20B presets with an environment variable such as `NEMO_CONFIG`; treat that as a convenience knob, not a requirement.

| Helper | YAML file | Shape cue | Best use |
| --- | --- | --- | --- |
| `default_nemo_1_3b_config()` | `megatron_1.3b.yaml` | 1 node, 8 GPUs, TP=1, PP=1, 2048 context | safest starting point and smallest canonical NeMo path |
| `default_nemo_2b_config()` | `megatron_2b.yaml` | 1 node, 1 GPU, TP=1, PP=1, 4096 context, sentencepiece tokenizer | compact sentencepiece-based variant |
| `default_nemo_20b_config()` | `megatron_20b.yaml` | 4 nodes, 8 GPUs/node, TP=4, PP=1, 2048 context | canonical larger Megatron recipe |
| `megatron_65b.yaml` | scaling template only | TP=8, PP=4, very large model settings | reference for extreme parallelism, not a first verification target |

Note: the source docstring for the 2B helper is stale, but the loader returns the 2B YAML.

## 7) Distilled source recipes that remain reference-only
The following source recipes were distilled into the guidance above and are not bundled as runnable artifacts:
- NeMo sentiment PPO, ILQL, and SFT example recipes
- the LLaMA-to-NeMo conversion helper
- the SLURM distributed launch wrapper
- the NeMo-vs-DeepSpeed comparison recipe, which scales the 1.3B template into larger 6.7B / 13B / 20B / 33B / 66B shapes by editing layer width, attention heads, and parallel degrees

Use them only as pattern evidence for config names, argument names, and parallel-sizing conventions.
