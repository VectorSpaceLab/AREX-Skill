# DreamVideo workflows

Use this reference for subject learning, motion learning, joint DreamVideo inference, and the DreamVideo metric helper.

## Route summary

| Task | Runtime entry | Primary config family | Notes |
| --- | --- | --- | --- |
| Subject learning | `train_net.py` -> `TASK_TYPE: train_dreamvideo_entrance` | `configs/dreamvideo/subjectLearning/*.yaml` | Trains an identity/appearance adapter from subject clips. |
| Motion learning | `train_net.py` -> `TASK_TYPE: train_dreamvideo_entrance` | `configs/dreamvideo/motionLearning/*.yaml` | Trains a motion adapter from motion-guidance clips. |
| Subject inference | `inference.py` -> `TASK_TYPE: inference_dreamvideo_entrance` | `configs/dreamvideo/infer/subject_*.yaml` | Loads a subject config plus `identity_adapter_index` or `identity_adapter_path`. |
| Motion inference | `inference.py` -> `TASK_TYPE: inference_dreamvideo_entrance` | `configs/dreamvideo/infer/motion_*.yaml` | Loads a motion config plus `motion_adapter_index` or `motion_adapter_path`. |
| Joint inference | `inference.py` -> `TASK_TYPE: inference_dreamvideo_entrance` | `configs/dreamvideo/infer/joint_*.yaml` | Layers both subject and motion configs before sampling. |
| Metric calculation | `python sub-skills/dreamvideo/scripts/calc_metrics.py --repo-root /path/to/VGen ...` | `metric/cal_metric_DreamVideo.py` evidence | Computes CLIP-T, CLIP-I, DINO-I, and Temporal Consistency. |

## Inference layering

DreamVideo inference performs config layering before model construction:

1. The base inference config is loaded.
2. If `subject_cfg` exists, the subject-learning config is merged first.
3. If `motion_cfg` exists, the motion-learning config is merged next.
4. The main inference config then applies its own fields.
5. If `use_textInversion` is needed, the subject route sets it when a subject config is present.

That layering matters because `subject_cfg` and `motion_cfg` can each point at separate log trees and checkpoints.

## Key inference knobs

Observed config fields:

- `base_model`: the core VGen checkpoint, commonly `models/model_scope_v1-5_0632000.pth`.
- `test_list_path`: custom inference list, usually an `image|||prompt` file.
- `test_data_dir`: image root for the custom list files.
- `subject_cfg` / `motion_cfg`: path to the adapter-training config used to locate checkpoint subdirectories.
- `identity_adapter_index` / `motion_adapter_index`: step number used to choose `adapter_XXXXXXXX.pth` from the corresponding training log.
- `identity_adapter_path` / `motion_adapter_path`: direct adapter checkpoint override.
- `appearance_guide_strength_cond` / `appearance_guide_strength_uncond`: appearance guidance strength during joint inference.
- `inverse_noise_strength`: optional reverse-noise mixing used by some inference variants.
- `guide_scale`, `noise_strength`, `chunk_size`, and `decoder_bs`: standard sampling and memory knobs.

The inference entrypoint raises an explicit error if both the index and path form of the same adapter are set at once.

## DreamVideo custom list format

The custom DreamVideo inference lists use exactly two fields separated by `|||`:

```text
00.jpg|||a * eating pizza
01.jpg|||a * is playing guitar
```

Rules:

- The left field is the image filename relative to `test_data_dir`.
- The right field is the prompt text.
- Keep the placeholder token `*` if the subject-learning config expects it.
- For motion inference, the image directory usually contains a motion-reference image set rather than a subject-token dataset.

## Training workflow

### Subject learning

Use a subject-learning config when the goal is to learn an appearance adapter for a new subject.

Typical steps:

1. Copy the nearest subject-learning YAML.
2. Point the data list and image directory at the new subject assets.
3. Keep the base model and learning-rate schedule aligned with the original config family.
4. Launch `train_net.py` through the bundled wrapper or the repo dispatcher.
5. Retrieve the adapter checkpoint from the experiment log directory and record the step index used for inference.

### Motion learning

Use a motion-learning config when the goal is to learn motion behavior separate from the subject identity.

Typical steps:

1. Copy the nearest motion-learning YAML.
2. Point the video list at the new motion clips.
3. Keep the subject-token settings off unless the motion experiment intentionally uses them.
4. Launch training and save the adapter checkpoints under the motion log tree.

### Joint inference

1. Verify the subject and motion configs were both trained against the same base model family.
2. Confirm the `test_data_dir` matches the subject image root.
3. Choose either adapter indices or direct adapter paths, but not both forms for the same adapter type.
4. Run the joint config.
5. Inspect whether the appearance guidance and motion guidance strengths need adjustment.

## Metric workflow

`metric/cal_metric_DreamVideo.py` expects the following prompt file format:

```text
video_filename|||reference_img_folder|||text_prompt
```

Each prompt row pairs a generated video with a folder of reference images and the text prompt used for the sample. The metric helper computes:

- CLIP-T
- CLIP-I
- DINO-I
- Temporal Consistency

The bundled `scripts/calc_metrics.py` asks for an explicit CLIP/DINO setup so the placeholder path in the source metric file does not leak into runtime use.

Example invocation:

```bash
python sub-skills/dreamvideo/scripts/calc_metrics.py \
  --repo-root /path/to/VGen \
  --videos-dir-path metric/examples/videos \
  --prompts-path metric/examples/test_prompts.txt \
  --dino-checkpoint-path /path/to/dino_deitsmall16_pretrain.pth
```

## Adapter-key helper

The bundled `scripts/dump_adapter_keys.py` recreates the repository's temporal/spatial parameter selection logic in a configurable way.

Example invocations:

```bash
python sub-skills/dreamvideo/scripts/dump_adapter_keys.py --repo-root /path/to/VGen --config configs/dreamvideo/subjectLearning/dog2_subjectLearning_step2.yaml --mode spatial
python sub-skills/dreamvideo/scripts/dump_adapter_keys.py --repo-root /path/to/VGen --config configs/dreamvideo/motionLearning/carTurn_motionLearning.yaml --mode temporal --output /tmp/dreamvideo_keys.json
python sub-skills/dreamvideo/scripts/dump_adapter_keys.py --repo-root /path/to/VGen --config configs/dreamvideo/infer/joint_dog2_carTurn.yaml --mode both --quiet
```

The helper can inspect a subject-learning, motion-learning, or joint inference config. When you pass a joint inference YAML, it layers the referenced subject and motion configs before exporting the parameter names. Use it when you need to inspect or export the keys that belong to DreamVideo's adapter-bearing blocks before fine-tuning or packaging a checkpoint.

## Evidence-backed examples

- Subject inference: `configs/dreamvideo/infer/subject_dog2.yaml`
- Motion inference: `configs/dreamvideo/infer/motion_carTurn.yaml`
- Joint inference: `configs/dreamvideo/infer/joint_dog2_playingGuitar.yaml`
- Subject training: `configs/dreamvideo/subjectLearning/dog2_subjectLearning_step2.yaml`
- Motion training: `configs/dreamvideo/motionLearning/playingGuitar_motionLearning.yaml`
