# CLI and Module Recipes

All commands here use public package modules. Start with `-h` / `--help` when the user is unsure about options.

## 1) Random-action demo

Help check:

```bash
python -m mani_skill.examples.demo_random_action -h
```

No-render or headless smoke-style run:

```bash
python -m mani_skill.examples.demo_random_action -e PickCube-v1 --render-mode none --render-backend none --sim-backend cpu
```

GUI / rendering run, only after display and Vulkan support are known:

```bash
python -m mani_skill.examples.demo_random_action -e PickCube-v1 --render-mode human --shader rt-fast
```

Useful flags:

- `-e`, `--env-id`: task id
- `-o`, `--obs-mode`: observation mode
- `-c`, `--control-mode`: controller mode
- `-r`, `--robot-uids`: robot uid or comma-separated tuple
- `-n`, `--num-envs`: number of parallel envs
- `-b`, `--sim-backend`: `auto`, `cpu`, or `gpu`
- `--render-mode`: `none`, `human`, `rgb_array`, `sensors`, or `all`
- `-rb`, `--render-backend`: `gpu`, `cpu`, or `none`
- `--shader`: `minimal`, `default`, `rt`, `rt-med`, or `rt-fast`
- `--record-dir`: save a video with `RecordEpisode`
- `-s`, `--seed`: seed or seed list

## 2) Robot visualization

Help check:

```bash
python -m mani_skill.examples.demo_robot -h
```

Open a viewer for a robot in an empty scene:

```bash
python -m mani_skill.examples.demo_robot -r panda
```

Useful flags:

- `-r`, `--robot-uid`: robot id
- `-c`, `--control-mode`: controller mode
- `-k`, `--keyframe`: named robot keyframe
- `--random-actions`, `--none-actions`, `--zero-actions`, `--keyframe-actions`: action source
- `--sim-freq`, `--control-freq`: simulation/control frequencies
- `-b`, `--sim-backend`: backend selection

Use this demo for robot/controller inspection, not for training or dataset collection.

## 3) Visual observation demos

Point cloud visualization, display required:

```bash
python -m mani_skill.examples.demo_vis_pcd -e PushCube-v1
```

Segmentation visualization:

```bash
python -m mani_skill.examples.demo_vis_segmentation -e PushCube-v1
python -m mani_skill.examples.demo_vis_segmentation -e PushCube-v1 --id cube
```

Texture visualization:

```bash
python -m mani_skill.examples.demo_vis_textures -e StackCube-v1 -o rgb+depth
python -m mani_skill.examples.demo_vis_textures -e OpenCabinetDrawer-v1 -o rgb+depth+albedo+normal
```

Shared useful flags:

- `--cam-width`, `--cam-height`: override sensor camera size
- `--num-envs`: small parallel test count for segmentation/texture demos
- `-s`, `--seed`: deterministic reset/action seed

Caveat: point-cloud visualization may require a display-compatible visualization stack such as `pyglet<2`.

## 4) Reset distribution visualization

Help check:

```bash
python -m mani_skill.examples.demo_reset_distribution -h
```

Save a reset-distribution video:

```bash
python -m mani_skill.examples.demo_reset_distribution -e PegInsertionSide-v1 --record-dir videos/reset_distributions
```

Open GUI reset inspection:

```bash
python -m mani_skill.examples.demo_reset_distribution -e PegInsertionSide-v1 --render-mode human
```

Useful flags:

- `-n`, `--num-resets`: number of reset samples in non-GUI mode
- `--record-dir`: output directory
- `--shader`: shader pack
- `--render-mode`: `human`, `rgb_array`, or `sensors`
- `-b`, `--sim-backend`: backend selection

## 5) Benchmarking / GPU simulation module

Treat this as help-first and potentially expensive.

Help check:

```bash
python -m mani_skill.examples.benchmarking.gpu_sim -h
```

Only run a benchmark after the backend is known good. If you do run it, keep the initial test small:

```bash
python -m mani_skill.examples.benchmarking.gpu_sim -e PickCube-v1 -n 16 -o state --render-mode rgb_array
```

Useful flags:

- `-e`, `--env-id`: task id
- `-o`, `--obs-mode`: observation mode
- `-c`, `--control-mode`: controller mode
- `-n`, `--num-envs`: parallel env count
- `--cpu-sim`: use CPU simulation; multiple envs use a CPU vector wrapper path
- `--save-video`: save videos; keep off until rendering is verified
- `--save-results`: append benchmark results to CSV
- `--save-example-image`: save sample visual observations
- `--render-mode`: `rgb_array` or `sensors` for saved videos/images
- `--num-cams`, `--cam-width`, `--cam-height`: benchmarking camera controls
- `--control-freq`, `--sim-freq`: frequency overrides

## 6) User-facing asset caveats

Some task ids require assets that are not included in the package. If an environment reports missing assets, use the public asset command for the task id:

```bash
python -m mani_skill.utils.download_asset <ENV_ID_OR_ASSET_ID>
```

For non-interactive smoke checks, prefer no-render built-in tasks and set `MS_SKIP_ASSET_DOWNLOAD_PROMPT=1` so the run fails fast instead of waiting for a prompt.
