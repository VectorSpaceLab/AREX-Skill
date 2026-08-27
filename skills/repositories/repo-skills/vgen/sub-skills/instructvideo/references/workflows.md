# InstructVideo Workflows

This reference distills the InstructVideo evidence used for reward fine-tuning and evaluation. Use the bundled scripts in `../scripts/` for commands; do not rely on the original source shell snippets directly.

## Route summary

| Task | Runtime entry | Primary config | Notes |
| --- | --- | --- | --- |
| Reward fine-tuning | `train_net.py` -> `TASK_TYPE: t2v_instructvideo_entrance` | `configs/instructvideo/train/reward_webvid_ani45_20_reg_vidldm_LoRA_TSNExp16Diffreward_Partial06_Trunc1_Check_ddim20.yaml` | LoRA reward fine-tuning over WebVid/custom video-text pairs. |
| LoRA inference/eval | `inference.py` -> `TASK_TYPE: inference_instructvideo_entrance` | `configs/instructvideo/eval/instructvideo_infer_UNetSD_t2v_webvid_LoRA_*.yaml` | Loads fine-tuned InstructVideo checkpoint and merges LoRA before sampling. |
| Base comparison eval | `inference.py` -> `TASK_TYPE: inference_instructvideo_entrance` | `configs/instructvideo/eval/modelscopet2v_infer_UNetSD_t2v_ddim20_*.yaml` | Uses the base ModelScope checkpoint with `UNet.use_lora: False`. |

The source training shell points to the current train config. The source eval shell contains stale LoRA filenames such as `configs/instructvideo/eval/infer_UNetSD_t2v_webvid_LoRA_webvid_ddim50_in-domain.yaml`; the actual repo files are prefixed with `instructvideo_infer_...`. The bundled `run_eval.sh` normalizes this.

## Environment and assets

The InstructVideo docs require the normal VGen environment plus InstructVideo reward extras. The assigned installed-package evidence already verified CUDA PyTorch and these important packages: `xformers`, `open-clip-torch`, `fairscale`, `diffusers`, `transformers`, `piq`, `scikit-image`, and OpenCV-compatible NumPy. The InstructVideo-specific requirements file also lists `piq` and `image-reward`; the implemented reward path imports the repo's `utils.reward.open_clip` wrapper and loads HPSv2 weights from disk.

Expected model assets after downloading `iic/InstructVideo` and moving its contents into `models/`:

- `models/model_scope_v1-4_0600000.pth` — base pre-trained ModelScope/VGen checkpoint used by training and base eval configs.
- `models/instructvideo-finetuned/ddim20_1102-18-52_non_ema_0620000.pth` — fine-tuned checkpoint used by the LoRA eval configs.
- `models/HPS_v2.pt` — HPSv2 reward checkpoint loaded by `DiffRewardModel`.
- `models/stable-diffusion-v/open_clip_pytorch_model.bin` — OpenCLIP embedder checkpoint referenced by InstructVideo train/eval configs.
- `data/stable_diffusion_image_key_temporal_attention_x1.json` — key map referenced by the train config's `Pretrain` block.

Run no fine-tuning until the checkpoint and data paths in the selected config exist.

## Prepare WebVid or custom reward fine-tuning data

The training config defines:

```text
vid_reward_dataset.data_list     = ['data/instructvideo/webvid_simple_animals_2_selected_20_train_file_list/00000.txt']
vid_reward_dataset.data_dir_list = ['data/instructvideo/train/']
vid_reward_dataset.get_first_frame = True
frame_lens = [16, 16, 16, 16]
sample_fps = [8]
```

The training dataset expects each list row to have exactly two fields:

```text
relative/path/to/video.mp4|||caption text
```

The relative path is joined with the corresponding `data_dir_list` entry. For the default config, a row such as `135751_135800/23726005_02_32.mp4|||cute cat` resolves under `data/instructvideo/train/135751_135800/23726005_02_32.mp4`.

For a custom dataset:

1. Place videos under a stable data root, or keep them in place and create a copied config with an updated `vid_reward_dataset.data_dir_list`.
2. Generate a list file with one `relative_video_path|||caption` row per clip. Do not include `|||` inside captions.
3. Keep enough frames for the configured `sample_fps` and `frame_lens`. Short or unreadable videos fall back to zero tensors in the dataset code, which silently harms reward fine-tuning.
4. Start with a small, filtered set. The paper/docs describe using a small WebVid subset to control reward fine-tuning cost.
5. Validate a few paths manually before training; the trainer logs `Loading a vid_diff_reward dataset:<list>` but bad rows can still degrade batches.

## Prepare evaluation caption lists

Inference configs read a caption file from:

```text
<webvid_dir>/<webvid_cap_file>/<webvid_eval_text>.txt
```

The inference entrypoint expects three fields per row:

```text
video_or_placeholder.mp4|||caption text|||frame_count
```

The video field is used for output naming, not as an input video. The default files use frame count `16`. `webvid_test_caps` limits how many rows are sampled; inference saves MP4s plus a stacked `.pt` tensor under `webvid_dir_save` with `webvid_test_caps` appended.

## Reward fine-tuning workflow

Use the bundled wrapper from the repo root or from the skill tree:

```bash
sub-skills/instructvideo/scripts/run_train.sh --repo-root /path/to/VGen --dry-run
sub-skills/instructvideo/scripts/run_train.sh --repo-root /path/to/VGen
```
If the skill is outside the checkout:

```bash
sub-skills/instructvideo/scripts/run_train.sh --repo-root /path/to/VGen
```
Core train-config knobs:

| Knob | Default | Why it matters |
| --- | --- | --- |
| `TASK_TYPE` | `t2v_instructvideo_entrance` | Routes `train_net.py` into the InstructVideo engine. |
| `data_type` | four `vid_diff_reward` entries | Selects reward-video batches in the training worker. |
| `UNet.type` | `UNetSD_LoRA` | Builds the LoRA-capable UNet. |
| `UNet.use_lora` | `True` | Freezes non-LoRA parameters via `freeze_all_except_lora`. |
| `UNet.lora_rank` | `4` | LoRA rank. Blank `lora_alpha:` parses as YAML null/`None`; merge alpha defaults to `1.0`. |
| `Diffusion.type` | `DiffusionDDIMReward` | Enables partial DDIM reward fine-tuning. |
| `ddim_timesteps` | `20` | Training uses the 20-step DDIM schedule listed in `ddim_steps`. |
| `starting_partial` | `0.6` | Starts partial denoising from the configured fraction of the DDIM chain. |
| `truncated_backprop` | `True` | Enables truncated backprop through partial sampling. |
| `trunc_backprop_timestep` | `1` | How much of the partial chain keeps gradient. |
| `reward_precision` | `fp16` | HPSv2/OpenCLIP reward precision. |
| `segments` | `4` | Number of sparse frame segments used for segmental video reward. |
| `selection_method` | `TSN` | Samples one frame per temporal segment. |
| `exponential_TSN` | `True` | Applies temporal attenuation with the shared `lambda_TAR` default. |
| `temporal_offset_noise` | `true` | Adds temporally correlated offset noise before reward denoising. |
| `chunk_size`, `decoder_bs` | `1`, `1` | Keep memory bounded during latent encode/decode and reward scoring. |
| `lr` | `1e-5` | Conservative LoRA reward-fine-tuning rate. |
| `num_steps` | `1000000` | Long run budget; use checkpoints and periodic eval rather than assuming a full run is needed. |

The train entrypoint builds the dataset, freezes non-LoRA weights, builds `DiffRewardModel` for `reward_type: HPSv2`, corrupts real video latents, runs `ddim_sample_loop_partial`, computes the differentiable reward loss, logs every `log_interval`, visualizes every `viz_interval`, and saves `non_ema_<step>.pth` checkpoints under the configured temp workspace.

Because reward fine-tuning can over-optimize, periodically run an eval preset against in-domain and generalization captions before accepting a checkpoint.

## Evaluation workflow

List the eval presets:

```bash
sub-skills/instructvideo/scripts/run_eval.sh --repo-root /path/to/VGen --list-presets
```
Dry-run the default LoRA 50-step in-domain eval:

```bash
sub-skills/instructvideo/scripts/run_eval.sh --repo-root /path/to/VGen --dry-run --preset lora-ddim50-in-domain
```
Run a generalization eval:

```bash
sub-skills/instructvideo/scripts/run_eval.sh --repo-root /path/to/VGen --preset lora-ddim20-new-animals
```
Evaluation config map:

| Preset | Config | LoRA? | DDIM | Captions (`webvid_eval_text`) | Rows |
| --- | --- | --- | --- | --- | --- |
| `lora-ddim50-in-domain` | `configs/instructvideo/eval/instructvideo_infer_UNetSD_t2v_webvid_LoRA_webvid_ddim50_in-domain.yaml` | yes | 50 | `simple_animals_2_webvid_videos_selected_eval` | 263 |
| `lora-ddim20-in-domain` | `configs/instructvideo/eval/instructvideo_infer_UNetSD_t2v_webvid_LoRA_webvid_ddim20_in-domain.yaml` | yes | 20 | `simple_animals_2_webvid_videos_selected_eval` | 263 |
| `lora-ddim20-new-animals` | `configs/instructvideo/eval/instructvideo_infer_UNetSD_t2v_webvid_LoRA_ddim20_generalization_new-animals.yaml` | yes | 20 | `eval_simple_animals_2_webvid_videos_selected_eval` | 22 |
| `lora-ddim20-non-animals` | `configs/instructvideo/eval/instructvideo_infer_UNetSD_t2v_webvid_LoRA_ddim20_generalization_non-animals.yaml` | yes | 20 | `eval_non-animals_hps_v2_all_eval` | 46 |
| `base-ddim20-in-domain` | `configs/instructvideo/eval/modelscopet2v_infer_UNetSD_t2v_ddim20_in-domain.yaml` | no | 20 | `simple_animals_2_webvid_videos_selected_eval` | 263 |
| `base-ddim20-new-animals` | `configs/instructvideo/eval/modelscopet2v_infer_UNetSD_t2v_ddim20_new-animals.yaml` | no | 20 | `eval_simple_animals_2_webvid_videos_selected_eval` | 22 |
| `base-ddim20-non-animals` | `configs/instructvideo/eval/modelscopet2v_infer_UNetSD_t2v_ddim20_non-animals.yaml` | no | 20 | `eval_non-animals_hps_v2_all_eval` | 46 |

Inference builds a LoRA-capable UNet for every config, loads `infer_checkpoint`, and only merges LoRA weights into a base model when `UNet.use_lora` is true. Use a LoRA preset for checkpoints saved with LoRA keys and a base preset for `models/model_scope_v1-4_0600000.pth`.

## Safe customization pattern

For non-trivial changes, copy the nearest YAML, edit the copy, and invoke the wrapper with `--config path/to/copy.yaml`. Prefer YAML edits over command-line overrides for typed fields because the repo config parser forwards override values as raw strings.

Common safe edits:

- Change `webvid_eval_text`, `webvid_test_caps`, and `webvid_dir_save` in a copied eval config to use a custom caption list.
- Change `infer_checkpoint` to compare several training checkpoints, keeping `UNet.use_lora` consistent with the checkpoint type.
- Reduce `webvid_test_caps`, `decoder_bs`, or `chunk_size` when debugging OOM.
- For reward data, edit `vid_reward_dataset.data_list` and `data_dir_list` together so relative paths still resolve.

Avoid mixing InstructVideo configs with DreamVideo, I2VGen, or generic T2V configs unless the task is explicitly a cross-workflow comparison.
