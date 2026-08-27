# Model Zoo And Artifacts

This reference covers CleanRL's saved-model layout and Hugging Face sharing behavior. It is distilled from the CleanRL evaluation utilities, Hugging Face helper, model-zoo documentation, experiment-tracking documentation, README model-sharing sections, training script save/upload flags, and the inspection environment report.

## Safety Model

- Local inspection is safe: checking `runs/`, `.cleanrl_model` files, TensorBoard event files, and local video folders does not require credentials or network.
- `cleanrl_utils.enjoy` is not local-only: it calls `hf_hub_download` to fetch `<exp_name>.cleanrl_model` from a Hugging Face repository.
- `cleanrl_utils.huggingface.push_to_hub` performs write operations: it creates or reuses a model repository, deletes prior TensorBoard event and `.mp4` files in that repository, writes a model card, uploads the local run folder, uploads the training source file, and uploads project lock/config files.
- `--upload-model` must be treated as a credential-backed network action; do not run it unless the user explicitly approves sharing and has handled authentication.
- `--track` is W&B tracking, while `--upload-model` is Hugging Face model sharing. Do not conflate the two integrations.

## Local Run Layout

Most supported saving scripts build the run name as:

```text
<env_id>__<exp_name>__<seed>__<timestamp>
```

Common local paths:

```text
runs/<run_name>/
runs/<run_name>/<exp_name>.cleanrl_model
runs/<run_name>/events.out.tfevents...
videos/<run_name>/
videos/<run_name>-eval/
```

Training scripts write TensorBoard logs under `runs/<run_name>`. When `--save-model` is enabled, they save the model as `runs/<run_name>/<exp_name>.cleanrl_model`. When video capture is enabled, training videos are usually under `videos/<run_name>`, and upload/eval video folders commonly use `videos/<run_name>-eval`.

## Save And Upload Flags

CleanRL training scripts with model sharing support commonly expose these flags:

| Flag | Meaning | Safe default |
| --- | --- | --- |
| `--save-model` | Save a local `.cleanrl_model` file under the run directory. | Safe when training itself is already intended. |
| `--upload-model` | After saving/evaluating, call Hugging Face upload helper. | Network/credential side effect; require approval. |
| `--hf-entity` | Prefix the default Hugging Face repository id with a user or org. | Safe to reason about; do not authenticate automatically. |
| `--capture-video` | Record gameplay videos under `videos/`. | May require rendering/video dependencies. |
| `--track` | Send W&B experiment tracking data. | Separate network side effect; require approval. |

The default upload repository name is usually:

```text
<env_id>-<exp_name>-seed<seed>
```

If `--hf-entity` is set, the upload helper receives:

```text
<hf_entity>/<env_id>-<exp_name>-seed<seed>
```

The `cleanrl_utils.enjoy` loader defaults to entity `cleanrl`, so its derived download repository is:

```text
cleanrl/<env_id>-<exp_name>-seed<seed>
```

Use `--hf-repository <owner>/<repo>` to override that derived id when a model lives under another owner or a nonstandard repo name.

## Upload Contents

The Hugging Face helper prepares a model repository by adding:

- `README.md` model card with evaluation metadata and a reproduction command.
- All immediate files in the local `runs/<run_name>` folder, including the saved model and event files.
- Optional `.mp4` files from the provided video folder, plus a root `replay.mp4` preview selected from the latest numbered video.
- The training script that launched the run.
- Project dependency metadata files used by CleanRL's reproduction instructions.

Before adding new files, the helper deletes existing TensorBoard event files and `.mp4` files in the remote repository. This is another reason uploads need explicit user approval.

## Supported Surfaces

`cleanrl_utils.enjoy` is a thin model-zoo downloader/evaluator. It looks up `cleanrl_utils.evals.MODELS[exp_name]`, downloads `<exp_name>.cleanrl_model`, then calls the mapped evaluation function. At the evidence snapshot, `MODELS` includes these `exp_name` values:

- `dqn`, `dqn_atari`, `dqn_jax`, `dqn_atari_jax`
- `c51`, `c51_atari`, `c51_jax`, `c51_atari_jax`
- `ppo_atari_envpool_xla_jax_scan`

The `cleanrl_utils.evals` package also contains standalone evaluation modules for continuous-control algorithms such as DDPG, TD3, and PPO, but those are not all routed through `cleanrl_utils.enjoy`. Use direct eval-function imports for local or unsupported-by-router evaluation.

## Artifact Inspection

Use the bundled checker for local-only validation:

```bash
python sub-skills/evaluation-and-sharing/scripts/check_cleanrl_artifact.py --runs-dir runs --exp-name dqn --env-id CartPole-v1 --seed 1
python sub-skills/evaluation-and-sharing/scripts/check_cleanrl_artifact.py --run-dir runs/CartPole-v1__dqn__1__1234567890 --exp-name dqn
```

The checker only reads local files. It reports expected model paths, run-name mismatches, likely TensorBoard event files, local video folders, derived Hugging Face repository names, and whether an `exp_name` is available through `cleanrl_utils.enjoy`.
