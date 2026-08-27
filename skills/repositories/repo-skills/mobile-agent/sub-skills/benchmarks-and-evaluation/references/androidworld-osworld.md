# AndroidWorld, MiniWoB, and OSWorld

## AndroidWorld / MiniWoB runners

Mobile-Agent v3.5 and v3 both include an `android_world` fork with absl flags. The important flags are:

| Flag | Meaning |
|---|---|
| `--adb_path` | ADB binary path when not found in default SDK locations. |
| `--perform_emulator_setup` | One-time setup flag; do not repeat for normal runs. |
| `--console_port` / `--grpc_port` | Emulator/device control ports, often derived from `adb devices`. |
| `--model`, `--api_key`, `--base_url` | Model endpoint settings. |
| `--suite_family` | `android_world`, `miniwob`, `miniwob++`, Android or information-retrieval task family depending on registry. |
| `--tasks` | Specific task templates to run; omit for all selected suite tasks. |
| `--n_task_combinations` | Instances per task template. |
| `--fixed_task_seed` / `--task_random_seed` | Reproducibility controls. |
| `--checkpoint_dir`, `--output_path`, `--traj_output_path` | Resume/results/trajectory outputs. |
| `--agent_name` | `mobile_agent_v3` or `gui_owl`. |

Use `scripts/build_androidworld_command.py` to generate a command.

## AndroidWorld prerequisites

- A configured Android emulator/device with AndroidWorld prerequisites installed.
- ADB authorization and matching console/grpc ports.
- Model API key/base URL/model.
- Enough runtime budget for task combinations.
- Clean output/checkpoint directories if not resuming.

## OSWorld runners

The OSWorld scripts are VM-based and use flags such as `--path_to_vm`, `--domain`, `--test_all_meta_path`, `--result_dir`, `--num_envs`, `--max_steps`, model/API flags, and per-agent grounding/RAG options. Use `scripts/build_osworld_command.py` to build a safe command without launching the VM.

## OSWorld prerequisites

- VM image/path and OSWorld service dependencies.
- Desktop automation access inside the VM.
- API endpoint and keys.
- Chosen domain/task metadata.
- Output directory with enough disk space.

Do not count command construction as benchmark pass. Record live unavailability as `SKIP_UNSAFE` unless the user has explicitly made benchmark reproduction a required verification target.
