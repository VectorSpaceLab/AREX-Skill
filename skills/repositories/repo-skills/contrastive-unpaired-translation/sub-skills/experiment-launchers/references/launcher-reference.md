# Launcher reference

This page summarizes the launcher command families and the safe bundled alternative.

## Native launcher CLI shape

```bash
python -m experiments <name> <cmd> <id...> [--which_epoch EPOCH] [--continue_train] [--gpu_id GPU]
```

- `<name>` selects a launcher module such as `grumpifycat`, `pretrained`, or `singleimage`.
- `<cmd>` selects behavior: `run`, `train`, `test`, `run_test`, `launch`, `launch_test`, `print_names`, `print_test_names`, `close`, or `stop`.
- `<id...>` selects one or more command ids, or `all` for some test paths.

## Safe bundled command listing

Prefer the bundled helper for inspection:

```bash
python scripts/list_experiment_commands.py --family grumpifycat --kind train
python scripts/list_experiment_commands.py --family pretrained --kind test --ids all
```

The helper only prints strings and is safe to run in any directory.

## grumpifycat family

| ID | Kind | Command |
| --- | --- | --- |
| 0 | train | `python train.py --gpu_ids 0 --dataroot ./datasets/grumpifycat --name grumpifycat_CUT --CUT_mode CUT` |
| 1 | train | `python train.py --gpu_ids 0 --dataroot ./datasets/grumpifycat --name grumpifycat_FastCUT --CUT_mode FastCUT` |
| 0 | test | `python test.py --gpu_ids 0 --dataroot ./datasets/grumpifycat --name grumpifycat_CUT --CUT_mode CUT --phase train` |
| 1 | test | `python test.py --gpu_ids 0 --dataroot ./datasets/grumpifycat --name grumpifycat_FastCUT --CUT_mode FastCUT --phase train` |

## pretrained family

| ID | Kind | Command |
| --- | --- | --- |
| 0 | test | `python test.py --gpu_ids 0 --dataroot datasets/cityscapes/cityscapes_val/ --direction BtoA --phase val --name cityscapes_cut_pretrained --CUT_mode CUT --num_test 500` |
| 1 | test | `python test.py --gpu_ids 0 --dataroot ./datasets/cityscapes_unaligned/cityscapes/ --direction BtoA --name cityscapes_fastcut_pretrained --CUT_mode FastCUT --num_test 500` |
| 2 | test | `python test.py --gpu_ids 0 --dataroot ./datasets/horse2zebra/ --name horse2zebra_cut_pretrained --CUT_mode CUT --num_test 500` |
| 3 | test | `python test.py --gpu_ids 0 --dataroot ./datasets/horse2zebra/ --name horse2zebra_fastcut_pretrained --CUT_mode FastCUT --num_test 500` |
| 4 | test | `python test.py --gpu_ids 0 --dataroot ./datasets/afhq/cat2dog/ --name cat2dog_cut_pretrained --CUT_mode CUT --num_test 500` |
| 5 | test | `python test.py --gpu_ids 0 --dataroot ./datasets/afhq/cat2dog/ --name cat2dog_fastcut_pretrained --CUT_mode FastCUT --num_test 500` |

The pretrained family also defines matching `train` commands for the same option rows, but its documented use is primarily testing downloaded pretrained weights.

## singleimage family

| ID | Kind | Command |
| --- | --- | --- |
| 0 | train | `python train.py --gpu_ids 0 --name singleimage_monet_etretat --dataroot ./datasets/single_image_monet_etretat --model sincut` |
| 0 | test | `python test.py --gpu_ids 0 --name singleimage_monet_etretat --dataroot ./datasets/single_image_monet_etretat --model sincut` |

## Launcher implementation details

- The launcher's `Options` object starts with `gpu_ids=0` and appends `--key value` pairs.
- `TmuxLauncher.refine_command` can prepend `CUDA_VISIBLE_DEVICES=...` and append `--epoch ...` or `--continue_train`.
- `run` and `run_test` execute commands directly.
- `launch` and `launch_test` send commands to tmux panes.
- `print_names` and `print_test_names` inspect command names without running the commands.

## Verified behavior

Safe inspection checks passed for:
- `python -m experiments grumpifycat print_names 0`
- `python -m experiments singleimage print_names 0`
- `python -m experiments pretrained print_test_names 0`

The `dry` action is not a safe inspection fallback in this checkout; see troubleshooting.
