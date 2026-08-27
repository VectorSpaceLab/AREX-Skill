# Gradio and Docker Operation

This reference covers DreamCraft3D's operator surfaces that start or monitor long-running work. Commands here are user-approved operator actions; do not run them automatically during diagnostics.

## Gradio app command surface

`gradio_app.py` has two top-level operations:

```bash
python gradio_app.py launch [--port 7860] [--listen]
python gradio_app.py watch --pid <pid> --trial-dir <trial-dir> [--alive-timeout 10] [--wait-timeout 10] [--check-interval 1]
```

Behavior by operation:

| Operation | Purpose | Important options | Safety notes |
| --- | --- | --- | --- |
| `launch` | Starts the Gradio web UI and lets a user select a model, edit prompt/seed/guidance/max steps, then run training from the UI. | `--port` defaults to `7860`; `--listen` binds to `0.0.0.0`. | Actual Run starts CUDA training with `python launch.py --config <tempfile> --train --gpu 0 --gradio`. Treat it as a long-running GPU job. `--listen` exposes the UI beyond localhost; use only on trusted networks. |
| `watch` | Companion watchdog for a launched process. It waits for an `alive` file under the trial directory and kills the process if the UI stops refreshing that file. | `--pid`, `--trial-dir`, `--alive-timeout`, `--wait-timeout`, `--check-interval`. | The watcher sends `SIGKILL` when the watched PID disappears or the alive timestamp is stale. Do not point it at an unrelated PID. |

## What the UI launches

When the Run button is pressed, the app:

1. Writes the selected YAML config text to a temporary file.
2. Chooses a trial directory under `outputs-gradio/<model-name>/<timestamp-tag>`.
3. Starts `python launch.py --config <tempfile> --train --gpu 0 --gradio trainer.enable_progress_bar=false` with overrides for `name`, `tag`, `exp_root_dir=outputs-gradio`, `use_timestamp=false`, prompt, guidance scale, seed, and max training steps.
4. Starts `python gradio_app.py watch --pid <training-pid> --trial-dir <trial-dir>`.
5. Polls status once per second while the training process is alive.

The app reads status from files inside the trial directory:

| Repo-relative runtime location | Meaning in the UI |
| --- | --- |
| `outputs-gradio/.../alive` | Timestamp refreshed by UI polling; the watcher uses it to decide whether the job is still being observed. |
| `outputs-gradio/.../logs` | Last ten log lines displayed in the terminal-log accordion. |
| `outputs-gradio/.../progress` | Human-readable progress created by the Gradio progress callback after training setup. |
| `outputs-gradio/.../save/*.png` | Latest validation image displayed as the Image output. |
| `outputs-gradio/.../save/*.mp4` | Latest test video displayed as the Video output. |
| `outputs-gradio/.../save/*export/*.obj` | Latest exported mesh; the app reloads and re-exports it through `trimesh` into a temporary OBJ for `gr.Model3D`. |

The Stop button tries to kill the training PID with `SIGKILL`, cancels the queued Gradio event, and changes the visible button state to Reset. This is abrupt termination; expect partially written checkpoints/logs and verify the trial directory before resuming work manually.

## UI model choices and config caveat

The app's model selector is inherited from a generic threestudio demo surface, with labels such as DreamFusion, TextMesh, Fantasia3D, SJC, and Latent-NeRF. It expects model YAML files under `configs/gradio/*.yaml`. The DreamCraft3D evidence snapshot for this skill contained the four `configs/dreamcraft3d-*.yaml` files but did not include `configs/gradio/`. If a user's checkout also lacks `configs/gradio/`, `python gradio_app.py launch` can fail before reaching DreamCraft3D-specific training.

For DreamCraft3D's documented image-to-3D stages, route users to the `generation-pipeline` sub-skill instead of assuming the Gradio UI can run the four canonical DreamCraft3D configs.

## Docker compose workflow

The repo's compose recipe is an operator convenience around the Dockerfile. The documented sequence is:

```bash
cd docker
docker compose build
docker compose up -d
docker compose exec threestudio bash
# run DreamCraft3D commands inside the container after verifying CUDA and artifacts
exit
docker compose stop
docker compose start
docker compose down
```

Important compose facts:

| Compose field | Distilled behavior |
| --- | --- |
| `build.context: ../` and `dockerfile: docker/Dockerfile` | Build context is the repository root, so the Dockerfile can copy `requirements.txt`. |
| Build args `USER_NAME`, `GROUP_NAME`, `UID`, `GID` | Defaults create a non-root `dreamer` user; host env vars can align container UID/GID with the host user. |
| Volume mount `../:/home/<user>/threestudio` | The live checkout is mounted into the container workdir; host file changes and generated outputs are shared. |
| GPU reservation | Compose requests an NVIDIA GPU device with `capabilities: [gpu]`. This requires NVIDIA Container Toolkit on the host. |
| `shm_size: 4gb` | Increases shared memory for data loading/rendering workloads. |
| `NVIDIA_DISABLE_REQUIRE: 1` | Avoids some strict `nvidia-container-cli` requirement errors, but does not prove CUDA works inside the container. |

## Safe preflight before container or UI use

Run the bundled diagnostic first:

```bash
python skills/disco/dreamcraft3d/sub-skills/interfaces-and-monitoring/scripts/check_dreamcraft3d_environment.py --repo-root . --check-model-paths
```

Then decide:

- If Python or required repo files are missing, fix the checkout before discussing GPUs or Docker.
- If `nvidia-smi` is absent or no visible GPU has enough VRAM, do not start full training or Gradio Run.
- If Docker is absent or `docker compose version` fails, treat the container route as blocked until the user prepares Docker.
- If `configs/gradio/*.yaml` are missing, use direct DreamCraft3D stage commands rather than the generic Gradio demo.
- If model artifacts are missing, route to model-artifact planning instead of launching a run that will fail after expensive initialization.
