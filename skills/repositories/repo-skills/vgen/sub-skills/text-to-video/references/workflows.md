# VGen text-to-video workflows

This reference distills the VGen text-to-video surfaces so a future agent can route work without reopening the source files. Paths below are repo-relative command/config names, not links to the original checkout.

## Dispatch mechanics

VGen dispatches almost entirely from YAML:

- Training command: `python train_net.py --cfg <config.yaml>`.
- Inference command: `python inference.py --cfg <config.yaml>`.
- `utils.config.Config` loads `configs/base.yaml`, the requested YAML, command-line `opts`, and parser fields.
- `train_net.py` calls `ENGINE.build(dict(type=cfg_update.TASK_TYPE), cfg_update=cfg_update.cfg_dict)`.
- `inference.py` calls `INFER_ENGINE.build(dict(type=cfg_update.TASK_TYPE), cfg_update=cfg_update.cfg_dict)`.
- Many inference entrypoints call `assign_signle_cfg(cfg, cfg_update, 'vldm_cfg')` first; if `vldm_cfg` points to a training YAML, the train YAML supplies the base model/diffusion structure and the inference YAML then overrides it.
- Entrypoints mutate the module-global `tools.modules.config.cfg`, then set CUDA/distributed state, build registry objects, and run the workflow.

### CLI override caveat

The bare positional overrides after `--cfg` are not type-aware for the common no-`_BASE` VGen YAMLs. For example:

```bash
python inference.py --cfg configs/t2v_infer.yaml test_list_path data/prompts.txt test_model models/model.pth
```

is safe because both values are strings, and `seed` is cast by several entrypoints. Numeric/list/dict overrides such as `guide_scale 7.5`, `max_frames 32`, `partial_keys ...`, or booleans can remain strings and break later math. Prefer a copied temporary YAML for numeric, list, dict, and boolean edits.

## Entrypoint file map

- `tools/train/train_t2v_enterance.py` registers `train_t2v_entrance`, the generic ModelScope T2V trainer that builds the configured `UNet` and `DiffusionDDIM` over `vid_dataset`/`img_dataset`.
- `tools/train/train_videolcm_t2v_entrance.py` registers `train_videolcm_t2v_entrance`, the VideoLCM distillation trainer with current/teacher/target UNets and diffusers schedulers.
- `tools/inferences/inference_text2video_entrance.py` registers `inference_text2video_entrance` for ModelScope T2V prompt sampling.
- `tools/inferences/inference_higen_entrance.py` registers `inference_higen_entrance` for HiGen spatial-prior plus temporal sampling.
- `tools/inferences/inference_tft2v_entrance.py` registers `inference_tft2v_entrance` for TF-T2V prompt sampling.
- `tools/inferences/inference_tft2v_vcomposer_entrance.py` registers `inference_tft2v_vcomposer_entrance` for TF-T2V VideoComposer-style conditioning.
- `tools/inferences/inference_videolcm_entrance.py` registers `inference_videolcm_entrance` for VideoLCM low-step prompt sampling.
- `tools/inferences/inference_videolcm_vcomposer_entrance.py` registers `inference_videolcm_vcomposer_entrance` for VideoLCM VideoComposer-style conditioning.
- `tools/inferences/inference_sr600_entrance.py` and `tools/inferences/inference_tft2v_sr600_entrance.py` register SR600 upscaling entrypoints for prompt-list and vcomposer-derived low-res videos.

## Family map

| Family | Configs | Command | `TASK_TYPE` | Model | List/data contract | Notes |
|---|---|---|---|---|---|---|
| ModelScope T2V train | `configs/t2v_train.yaml` | `python train_net.py --cfg configs/t2v_train.yaml` | `train_t2v_entrance` | `UNetSD_T2VBase` | `vid_dataset` uses `data/vid_list.txt` under `data/videos/`; `img_dataset` uses `data/img_list.txt` under `data/images/`; paired rows are `relative_file|||caption`. | Trains mixed image/video batches from `frame_lens` and `sample_fps`. Uses `DiffusionDDIM`, OpenCLIP text/visual embedder, and T2VBase UNet. |
| ModelScope T2V infer | `configs/t2v_infer.yaml` | `python inference.py --cfg configs/t2v_infer.yaml` | `inference_text2video_entrance` | `UNetSD_T2VBase` loaded from `vldm_cfg: configs/t2v_train.yaml` | Prompt list: one caption per line; `#` comments and blanks are skipped. Default demo list is `data/text_img_for_t2v.txt`. | Writes videos under `log_dir/<test-list-stem>/` with sanitized caption filenames. |
| HiGen train config | `configs/higen_train.yaml` | Intended via `train_net.py`, but see note | `train_t2v_higen_entrance` in YAML | `UNetSD_HiGen` | Same train list structure as T2V. | The provided train files do not register `train_t2v_higen_entrance`; use a temporary YAML with `TASK_TYPE: train_t2v_entrance` only after verifying the generic trainer supports the HiGen kwargs, or add a registry alias in code. |
| HiGen infer | `configs/higen_infer.yaml` | `python inference.py --cfg configs/higen_infer.yaml` | `inference_higen_entrance` | `UNetSD_HiGen` loaded from `vldm_cfg: configs/higen_train.yaml` | Prompt rows may be `caption` or `caption|manual_seed`; default list is `data/text_list_for_t2v_share.txt`. | Two-stage sampling: spatial prior/key-frame pass then temporal pass. Uses `motion_factor`, `appearance_factor`, `max_frames: 32`, and high `guide_scale`. |
| TF-T2V text infer | `configs/tft2v_t2v_infer.yaml`, `configs/tft2v_t2v_32frames_infer.yaml` | `python inference.py --cfg <config>` | `inference_tft2v_entrance` | `UNetSD_TFT2V` loaded from `vldm_cfg: configs/t2v_train.yaml` | Prompt-only list. Defaults: `data/text_list_for_tft2v.txt` for 16 frames and `data/text_list_for_tft2v_32frame.txt` for 32 frames. | Appends `positive_prompt`; `video_compositions: ['text', 'image']` but the text-only entrypoint passes text/fps conditioning. |
| TF-T2V VideoComposer-style infer | `configs/tft2v_vcomposer_infer.yaml`, `configs/tft2v_vcomposer_32frames_infer.yaml`, `configs/tft2v_vcomposer_896x512_infer.yaml` | `python inference.py --cfg <config>` | `inference_tft2v_vcomposer_entrance` | `UNetSD_TFT2V` | `video_key|||caption` rows under `data_dir` (default `data/videos`). Captions may end in `|manual_seed`. | Builds conditions from video frames. Config declares `video_compositions` including text, mask, depthmap, sketch, motion, image, local_image, and single_sketch. Default `partial_keys` emit separate outputs for `['y','depth']`, `['y','sketch']`, and `['y','local_image']`. Motion is present in the composition list but the motion-vector extraction path is commented out in the entrypoint. |
| VideoLCM train | `configs/videolcm_t2v_train.yaml` | `python train_net.py --cfg configs/videolcm_t2v_train.yaml` | `train_videolcm_t2v_entrance` | `UNetSD_VideoLCM` | Same train list structure as T2V. | LCM distillation path: builds current, teacher, and target UNets, uses diffusers schedulers, `num_inference_steps: 4`, and a TF-T2V teacher checkpoint in `Pretrain.resume_checkpoint`. |
| VideoLCM text infer | `configs/videolcm_t2v_infer.yaml` | `python inference.py --cfg configs/videolcm_t2v_infer.yaml` | `inference_videolcm_entrance` | `UNetSD_VideoLCM` | Prompt-only list `data/text_list_for_videolcm.txt`. | Uses `LCMScheduler` with default 4 inference steps and appends the VideoLCM positive prompt. |
| VideoLCM VideoComposer-style infer | `configs/videolcm_vcomposer_infer.yaml` | `python inference.py --cfg configs/videolcm_vcomposer_infer.yaml` | `inference_videolcm_vcomposer_entrance` | `UNetSD_VideoLCM` | `video_key|||caption` rows under `data_dir`; optional `|manual_seed`. | Same conditioning scheme and `partial_keys` concept as TF-T2V vcomposer, but samples through the LCM scheduler. |
| SR600 upscaling | `configs/sr600_infer.yaml`, `configs/tft2v_16frames_sr600_infer.yaml`, `configs/tft2v_32frames_sr600_infer.yaml`, `configs/tft2v_vcomposer_32frames_sr600_infer.yaml`, `configs/videolcm_t2v_16frames_sr600_infer.yaml` | `python inference.py --cfg <sr-config>` | `inference_sr600_entrance` or `inference_tft2v_sr600_entrance` | `UNetSD_SR600` | Prompt-list SR configs reconstruct the low-res video filename from `log_dir/<list-stem>/rank_..._<caption>.mp4`. The vcomposer SR config maps `partial_keys` to low-res paths generated by the vcomposer entrypoint. | SR model expects low-resolution videos to exist before it runs. `double_frames_sr: True` duplicates 16-frame inputs to satisfy the 32-frame SR path, then drops duplicate output frames. |

## List-file formats

### Prompt-only T2V lists

Used by `t2v_infer`, `tft2v_t2v_*`, and `videolcm_t2v_infer`:

```text
A video of a duckling wearing a medieval soldier helmet and riding a skateboard.
Astronaut riding a horse.
# comments are skipped
```

HiGen and SR600 also accept a manual seed suffix:

```text
Batman turns his head from right to left|11
A video of a duckling wearing a medieval soldier helmet and riding a skateboard.|2
```

Do not assume every text entrypoint parses the seed suffix; plain TF-T2V text inference treats the entire line as the caption.

### Training video/image paired lists

Used by `vid_dataset` and `img_dataset`:

```text
relative_video.mp4|||caption text
relative_image.jpg|||caption text
```

The file key is joined to the configured `data_dir_list`. The bundled preview script can detect missing demo files and malformed delimiters before a training run.

### VideoComposer-style lists

Used by TF-T2V/VideoLCM vcomposer configs:

```text
10000.mp4|||A boat docked on the beach and the wind picked up
1066674790.mp4|||croissants with icing sugar on a wooden plate sprinkled with almonds slow motion
```

The video key is joined with `data_dir`. Captions can include `|manual_seed` at the end. The entrypoint builds conditions from source video frames, then runs one output per `partial_keys` combination.

## Common staged workflows

### ModelScope T2V quick inference

1. Put one prompt per line in a text list.
2. Validate:

   ```bash
   python sub-skills/text-to-video/scripts/preview_dataset.py \
     --repo-root /path/to/VGen --config configs/t2v_infer.yaml --no-render --strict
   ```

3. Use a temporary YAML or string-safe CLI overrides for `test_list_path`, `test_model`, `round`, `seed`, and `log_dir`.
4. Run:

   ```bash
   python inference.py --cfg configs/t2v_infer.yaml
   ```

### T2V/HiGen training data preview

```bash
python sub-skills/text-to-video/scripts/preview_dataset.py \
  --repo-root /path/to/VGen --config configs/t2v_train.yaml --split vid --max-items 3 --render
python sub-skills/text-to-video/scripts/preview_dataset.py \
  --repo-root /path/to/VGen --config configs/t2v_train.yaml --split img --max-items 3 --render
```
The preview logic fixes stale issues in the repo test helper: it imports `torch`, resolves the repo root explicitly, uses `data/font/DejaVuSans.ttf` when available, avoids `rm -rf`, and writes only a bounded number of GIFs.

### TF-T2V or VideoLCM text inference

1. Choose frame count:
   - 16-frame TF-T2V: `configs/tft2v_t2v_infer.yaml`.
   - 32-frame TF-T2V: `configs/tft2v_t2v_32frames_infer.yaml`.
   - 16-frame low-step VideoLCM: `configs/videolcm_t2v_infer.yaml`.
2. Keep `positive_prompt` unless intentionally comparing raw captions.
3. Run SR600 only after low-res videos exist.

### VideoComposer-style conditioning

1. Validate `video_key|||caption` rows against `data_dir`.
2. Decide `partial_keys`; defaults produce depth, sketch, and local-image condition variants.
3. Watch model-output filenames: each output includes `condition_<keys>_<caption>.mp4`.
4. If running SR for vcomposer, use the matching vcomposer SR config so low-res paths include the same condition-key suffix.

### SR600 upscaling

1. Run the base low-resolution generation first with the same list stem.
2. Confirm the low-res files are in `log_dir/<test-list-stem>/` and have names matching the source entrypoint's sanitized caption scheme.
3. Run the matching SR config:
   - HiGen/shared prompt list: `configs/sr600_infer.yaml`.
   - TF-T2V 16-frame: `configs/tft2v_16frames_sr600_infer.yaml`.
   - TF-T2V 32-frame: `configs/tft2v_32frames_sr600_infer.yaml`.
   - TF-T2V vcomposer 32-frame: `configs/tft2v_vcomposer_32frames_sr600_infer.yaml`.
   - VideoLCM 16-frame: `configs/videolcm_t2v_16frames_sr600_infer.yaml`.

## Environment facts to rely on

The inspection environment used for this skill verified CUDA-capable PyTorch, xformers, open-clip-torch, fairscale, diffusers, transformers, piq, scikit-image, and OpenCV-compatible NumPy. The runtime workflows still require model checkpoints and CUDA hardware; those facts do not prove that checkpoint files are present in a future checkout.
