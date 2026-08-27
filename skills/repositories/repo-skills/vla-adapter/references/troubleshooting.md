# Cross-Cutting Troubleshooting

## When to read

Read this when an install/import/backend issue appears before the task clearly
belongs to one sub-skill. Workflow-specific failures are covered in the nearest
sub-skill troubleshooting reference.

## Install and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: prismatic` | Package not installed in the active environment, or command is using the wrong Python. | Install the package in the target environment and rerun `scripts/check_vla_adapter_env.py`. Avoid relying on shell activation when automating; call the target Python explicitly. |
| `ModuleNotFoundError: dlimp` or TensorFlow/RLDS imports fail | RLDS data loader dependency missing or TensorFlow/TFDS/protobuf versions conflict. | Install the documented TensorFlow/TFDS/dlimp stack. Keep TensorFlow 2.15, TFDS 4.9.x, and compatible protobuf/tensorflow-metadata versions together. |
| `pkg_resources` missing during script import | Very new Setuptools removed the compatibility module used by dependencies. | Pin Setuptools below the removal boundary or install the compatibility package in the target environment. |
| `flash_attn` build fails | FlashAttention must match PyTorch, CUDA, Python, and compiler ABI. | Treat FlashAttention as optional unless throughput/training config requires it. Prefer a prebuilt wheel matching CUDA and torch; otherwise skip and document slower training. |
| `libero`, `calvin_agent`, or `rospy` missing | Optional benchmark/robot stack not installed. | Route to setup/evaluation/deployment; install only the needed external stack instead of all optional systems. |

## CUDA and backend issues

- `torch.cuda.is_available() == False` means real training/evaluation/serving is
  not verified. CPU imports are useful only for static planning.
- If TensorFlow logs cuDNN/cuFFT/cuBLAS factory warnings while PyTorch also
  imports CUDA libraries, treat them as warnings unless imports or device
  operations fail.
- If CUDA OOM appears, reduce `batch_size`, increase `grad_accumulation_steps`,
  lower `lora_rank`, disable checkpoint merging during training, or choose a
  smaller profile in `training/scripts/build_finetune_command.py`.
- If action dimensions are wrong, check the robot platform selected by command
  text. ALOHA expects 14D actions and 25-action chunks; LIBERO/CALVIN expect 7D
  actions and 8-action chunks.

## Data and checkpoint issues

- Missing `config.json`, tokenizer/processor files, model code files, or
  `dataset_statistics.json` usually means the checkpoint directory is incomplete
  for VLA action prediction.
- LIBERO RLDS datasets released with a `modified_` prefix may need directory
  names without that prefix to match the training/evaluation path conventions.
- CALVIN workflows need `CALVIN_ROOT` and the ABC→D dataset layout expected by
  the CALVIN environment.
- ALOHA local model setup scripts can patch source files for offline loading;
  do not run patching blindly. Record changed files and know how to restore them
  before mutating a working checkout.

## Safe next steps

1. Run `scripts/check_vla_adapter_env.py --check-optional`.
2. If paths are involved, run
   `sub-skills/setup-and-data/scripts/validate_data_layout.py --help` and then a
   targeted layout check.
3. If checkpoint layout is involved, run
   `sub-skills/package-apis/scripts/check_checkpoint_layout.py --help`.
4. If generating a command, use the command-builder scripts first and inspect
   the printed command before launching anything expensive.
