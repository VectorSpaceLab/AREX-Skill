# Recipe Workflows

This reference distills the torchtune recipe registry, docs, recipe scripts, and recipe tests into safe selection guidance. It assumes agents use the `tune` CLI entry points rather than importing `recipes` as a package.

## Built-In Training Recipe Taxonomy

The verified registry contains 22 total recipes; the training-relevant subset is below. Generation, evaluation, and quantization recipes are owned by the inference/eval/quantization sub-skill.

| Goal | Recipe names | Distributed support | Common config patterns |
| --- | --- | --- | --- |
| Full supervised finetune | `full_finetune_single_device`, `full_finetune_distributed` | Single-device recipe is not distributed; distributed recipe supports torchrun | `*_full_single_device`, `*_full`, low-memory variants, large-model multi-node variants |
| LoRA / QLoRA / DoRA supervised finetune | `lora_finetune_single_device`, `lora_finetune_distributed` | Single-device recipe is not distributed; distributed recipe supports torchrun | `*_lora_single_device`, `*_lora`, `*_qlora_single_device`, `*_qlora`, `*_dora*`, `*_qdora*` |
| DPO preference training | `lora_dpo_single_device`, `lora_dpo_distributed`, `full_dpo_distributed` | LoRA single-device is not distributed; LoRA/full distributed recipes support torchrun | `llama*_lora_dpo_single_device`, `llama*_lora_dpo`, `llama3_1/8B_full_dpo` |
| PPO RLHF training | `ppo_full_finetune_single_device` | Not distributed | low-memory Mistral and Llama configs using policy, value, reward, and reference checkpointers |
| Knowledge distillation | `knowledge_distillation_single_device`, `knowledge_distillation_distributed` | Single-device recipe is not distributed; distributed recipe supports torchrun | teacher/student configs such as `qwen2/1.5_to_0.5B_KD_lora_*` and `llama3_2/8B_to_1B_KD_lora_*` |
| Quantization-aware training | `qat_single_device`, `qat_distributed`, `qat_lora_finetune_distributed` | Single-device recipe is not distributed; distributed QAT recipes support torchrun | full QAT configs and QAT+LoRA configs with a QAT quantizer |
| Experimental GRPO / early-exit | `dev/grpo_full_finetune_distributed`, `dev/async_grpo_full_finetune_distributed`, `dev/early_exit_finetune_distributed`, `dev/lora_finetune_distributed_multi_dataset` | Most `dev/*_distributed` recipes support torchrun; async GRPO is registry-marked non-distributed | `dev/*` configs; async RL may require extra dependencies |

Selection rule: choose the recipe whose name matches the training strategy and launch shape, then choose a registry config from `tune ls <recipe>` or the closest family/model config from `tune ls`.

## Safe CLI Workflow

1. Discover available recipe/config pairs:

   ```bash
   tune ls
   tune ls lora_finetune_distributed
   ```

2. Inspect a config without training:

   ```bash
   tune cat llama3_2/3B_lora
   ```

3. Copy before major edits:

   ```bash
   tune cp llama3_2/3B_lora ./custom_3B_lora.yaml --make-parents
   ```

4. Validate copied YAML shape before planning a run:

   ```bash
   tune validate ./custom_3B_lora.yaml
   ```

5. Build a dry command and ask for explicit execution approval:

   ```bash
   python sub-skills/post-training-recipes/scripts/build_tune_command.py \
     lora_finetune_distributed ./custom_3B_lora.yaml \
     --nproc-per-node 4 \
     --override max_steps_per_epoch=20 \
     --override output_dir='./runs/lora-smoke'
   ```

6. Only after approval, run the printed `tune run ...` command.

## Training Method Choices

### Full Finetune

Use full finetune when the user wants all model weights updated and has enough memory. Prefer `full_finetune_single_device` for one accelerator or CPU experiments and `full_finetune_distributed` for FSDP or multi-node launches. Full finetune usually needs more memory than adapter methods but avoids adapter-only checkpoint management.

Common safe overrides:

```bash
batch_size=1 gradient_accumulation_steps=8 max_steps_per_epoch=20
checkpointer.checkpoint_dir='<checkpoint-dir>' output_dir='<output-dir>'
```

### LoRA, QLoRA, And DoRA

Use LoRA recipes for parameter-efficient finetuning. LoRA updates adapter parameters while freezing most base weights. QLoRA uses the same LoRA recipe families with `quantize_base=True` model configs and `qlora` config names. DoRA uses LoRA model builders with `use_dora=True`; QDoRA combines `use_dora=True` and `quantize_base=True` in available configs.

Typical controls:

- `model.lora_attn_modules=[q_proj,k_proj,v_proj,output_proj]`
- `model.apply_lora_to_mlp=True`
- `model.apply_lora_to_output=True`
- `model.lora_rank=32`
- `model.lora_alpha=64`
- `model.lora_dropout=0.0`
- `model.quantize_base=True` for QLoRA or QDoRA-style configs
- `model.use_dora=True` for DoRA/QDoRA-style configs

Do not assume every model family has every LoRA/QLoRA/DoRA config. Use `tune ls` and copy the closest config before editing.

### DPO

Use DPO after supervised finetuning or when aligning on preference data. LoRA DPO recipes use adapter-capable model builders and a DPO loss component. Full DPO uses full model weights and a reference checkpointer. DPO configs normally require a paired/preference dataset and both policy and reference-model checkpoint decisions.

Safe questions before execution:

- Is the input dataset a preference dataset with chosen/rejected responses?
- Should the policy start from an SFT checkpoint or base instruct checkpoint?
- Should the reference model remain the original base/SFT model?
- Are `checkpointer` and `ref_checkpointer` intentionally different or intentionally the same source?

### PPO

Use `ppo_full_finetune_single_device` for RLHF PPO. It is more stateful than SFT/DPO and uses policy, reference policy, value, and reward components. Many provided low-memory PPO configs use optional `bitsandbytes` optimizers and require output subdirectories for policy/value checkpoints.

Preflight carefully: PPO is expensive, GPU-heavy, and has more checkpoint paths than SFT.

### Knowledge Distillation

Use KD when training a smaller student from a larger or better teacher. KD configs include teacher/student model and checkpointer sections and KD-specific controls such as `kd_ratio`. Start from the closest registry config, then change teacher and student checkpoint paths deliberately.

Common override examples:

```bash
optimizer.lr=1e-3
kd_ratio=0.25
teacher_checkpointer.checkpoint_dir='<teacher-dir>'
checkpointer.checkpoint_dir='<student-dir>'
output_dir='<kd-output-dir>'
```

### Quantization-Aware Training

Use QAT recipes when the user wants to train with fake quantization so later quantized inference quality is better than simple PTQ. QAT training outputs an unquantized/bfloat16 model with QAT-trained weights; actual quantized conversion is a later `quantize` workflow owned by the inference/eval/quantization sub-skill.

QAT configs require a QAT quantizer component, commonly `torchtune.training.quantization.Int8DynActInt4WeightQATQuantizer`. QAT LoRA uses `qat_lora_finetune_distributed` and LoRA model builders.

## Checkpoint And Output Decisions

Before execution, identify:

- `checkpointer.checkpoint_dir`: source model checkpoint directory.
- `checkpointer.checkpoint_files`: source checkpoint shard filenames, if the checkpointer requires them.
- `tokenizer.path` or tokenizer checkpoint path: must match the model family.
- `output_dir`: writable destination for recipe logs, recipe checkpoints, and trained model outputs.
- `resume_from_checkpoint`: set only when resuming from a torchtune recipe output with matching recipe state.
- `adapter_checkpoint` / `recipe_checkpoint`: needed by some LoRA/QAT-LoRA resume flows.

Use `../training-utilities-and-rlhf/SKILL.md` for checkpointer internals and resume troubleshooting.

## Native Evidence-Based Safety Notes

- Recipe tests exercise mocked/tiny recipe paths, checkpoint resume behavior, async checkpointing, QAT quantizer checks, and expected loss sequences. They are not permission to launch real training on user hardware.
- Registry names are the stable user-facing entry points. Recipe file paths and source docs are evidence, not runtime dependencies for this skill.
- Built-in recipes are executed by `tune run` through a path resolved from the registry; custom recipe paths are converted to module dotpaths. Agents should not teach `import recipes`.
