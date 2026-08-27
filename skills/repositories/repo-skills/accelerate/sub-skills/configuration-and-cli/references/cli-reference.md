# Accelerate CLI Reference

The top-level command is `accelerate <command> [args]`. The same entry points are often exposed as console scripts such as `accelerate-launch`, and some commands can be run as Python modules, for example `python -m accelerate.commands.launch`.

## Command Inventory

| Command | Purpose | Mutates Files or Runs Work |
| --- | --- | --- |
| `accelerate config` | Interactive config questionnaire. | Writes a config file. |
| `accelerate config default` | Non-interactive basic config creation. | Writes a config file unless one already exists at the target. |
| `accelerate config update` | Rewrites an older config with current recognized defaults. | Updates the selected config file. |
| `accelerate env` | Prints environment and Accelerate config details. | Read-only. |
| `accelerate launch` | Starts a script/module/executable using Accelerate's selected launcher. | Runs user code and may spawn subprocesses. |
| `accelerate test` | Runs Accelerate's built-in distributed smoke script. | Runs subprocesses. |
| `accelerate estimate-memory MODEL` | Estimates model memory from Hub metadata and model config. | May contact the Hub and import model libraries; route memory workflow details to big-model inference. |
| `accelerate merge-weights CHECKPOINT_DIR OUTPUT_PATH` | Merges FSDP sharded weights into one checkpoint. | Reads checkpoint shards and writes output; can remove checkpoint dir with `--remove_checkpoint_dir`. |
| `accelerate to-fsdp2 --config_file CONFIG` | Converts FSDP1 config keys to FSDP2-style keys. | Writes `--output_file`, or overwrites input only with `--overwrite`. |
| `accelerate tpu-config` | Runs TPU VM setup commands before TPU launch. | Can execute remote commands; route TPU meaning to distributed backends. |

Use `scripts/print_accelerate_help_summary.py` to check which commands are available in the current installed Accelerate package without relying on source checkout files.

## Config Commands

Examples:

```bash
accelerate config --config_file configs/train.yaml
accelerate config default --config_file configs/cpu.yaml --mixed_precision no
accelerate config update --config_file configs/train.yaml
accelerate env --config_file configs/train.yaml
```

Notes:

- `config` and `config default` write the selected file. Avoid running them in read-only analysis unless the user asks to create or overwrite a config.
- `config update` errors if the selected file does not exist.
- `env` can load a default config when no `--config_file` is supplied, but explicit config paths are easier to debug.

## Launch Essentials

Basic forms:

```bash
accelerate launch train.py --arg value
accelerate launch --config_file configs/train.yaml train.py --arg value
python -m accelerate.commands.launch --num_processes=2 train.py --arg value
```

Important parser behavior:

- Launcher flags must appear before the training script path or module name.
- Everything after the training script is collected as `training_script_args` and passed to the script.
- Accelerate accepts launch flags with underscores and hyphens, such as `--num_processes` and `--num-processes`. Prefer underscore spellings because CLI help and config keys are underscore-first.
- `--module` makes each process execute the target like `python -m package.module`.
- `--no_python` executes the target directly without prepending Python; use it only for executable shell scripts or binaries.
- `--module` and `--no_python` are mutually exclusive.
- `--quiet` suppresses some launcher stack noise for DeepSpeed and single-process configurations; use `--debug` when you need distributed stack traces.

## Launch Flag Groups

Hardware and resources:

```bash
--cpu
--multi_gpu
--tpu
--mixed_precision no|fp16|bf16|fp8
--num_processes N
--num_machines M
--num_cpu_threads_per_process N
--enable_cpu_affinity
```

Distributed placement:

```bash
--gpu_ids all|0,1
--same_network
--machine_rank R
--main_process_ip HOST_OR_IP
--main_process_port PORT
--rdzv_backend static|c10d
--rdzv_conf key=value,key2=value2
--tee 0|1|2|3
--log_dir logs
```

Training paradigms:

```bash
--use_deepspeed
--use_fsdp
--use_parallelism_config
--use_megatron_lm
```

Do not combine more than one of `--cpu`, `--multi_gpu`, `--tpu`, `--use_deepspeed`, and `--use_fsdp`. Accelerate raises an error before launching. Backend-specific flags are owned by the distributed-backends sub-skill.

## Other Commands

Memory estimate command:

```bash
accelerate estimate-memory bert-base-cased --library_name transformers --dtypes float32 float16
```

Add `--trust_remote_code` only for model repositories the user explicitly trusts because it can execute remote model code. Route interpretation of the memory table and device-map planning to big-model inference.

FSDP merge command:

```bash
accelerate merge-weights path/to/sharded_checkpoint path/to/output_dir
```

Use `--unsafe_serialization` only when the user specifically needs PyTorch `.bin` output instead of safer `safetensors`. Use `--remove_checkpoint_dir` only after confirming the source checkpoint directory can be deleted.

FSDP2 conversion command:

```bash
accelerate to-fsdp2 --config_file configs/fsdp1.yaml --output_file configs/fsdp2.yaml
```

Without `--overwrite`, `--output_file` is required. With `--overwrite`, the input config can be rewritten in place.
