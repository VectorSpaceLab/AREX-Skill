# Multi-Modality Workflows

## Stage2 video-language / audio-language alignment

Stage2 training uses `tasks/pretrain.py` plus a Python config file under `scripts/pretraining/` or `scripts/finetuning/`. The launchers set `MASTER_PORT`, `OMP_NUM_THREADS=1`, `PYTHONPATH`, and then call `srun` or local `torchrun` through `torchrun.sh`.

Checklist before editing or running a Stage2 recipe:

- Confirm the config belongs to the Stage2 branch and model size you want.
- Confirm the vision checkpoint path, especially when the config seeds from InternVL or a Stage2 bootstrap checkpoint.
- Confirm dataset roots and annotation layout; Stage2 configs can point at a list, a corpus alias, or an evaluation split.
- Decide whether `deepspeed` stays enabled for the target run.
- Decide whether the config is pure video-language or audio/video-aware.

Video-only Stage2 configs usually pair a BERT-large text encoder with a `pretrain_internvideo2_*` vision backbone. Audio/video Stage2 configs switch to `model_cls="InternVideo2_Stage2_audiovisual"`, add a `beats` audio backbone, and rely on audio-aware dataset and loss fields.

## CLIP post-pretraining

CLIP branch workflows use `tasks_clip/pretrain.py` for training and `tasks_clip/retrieval.py` for retrieval evaluation. Their config files carry the text/vision checkpoint pairing directly, so `llama_path`, `tokenizer_path`, `vision_ckpt_path`, `text_ckpt_path`, `extra_ckpt_path`, and `pretrained_path` all matter.

Small VideoCLIP variants may swap in MobileCLIP text assets and distilled vision checkpoints. The helper script should only print a launch skeleton; it must not submit a job or copy code.

## Zero-shot retrieval and action evaluation

Stage2 zero-shot evaluation typically runs `tasks/pretrain.py` with `evaluate True` and a `pretrained_path`. CLIP zero-shot retrieval uses `tasks_clip/retrieval.py` with the same evaluation pattern.

Representative dataset families include MSRVTT, LSMDC, DiDeMo, MSVD, ActivityNet, VATEX, K400, K600, K700, UCF101, HMDB51, MiT, SSv2, and Charades. Some configs also set `zero_shot=True`, but the source scripts mostly rely on the evaluation flag plus the checkpoint override.

If `deepspeed` is disabled for evaluation, the docs note that retrieval metrics may shift slightly. Record that choice when comparing numbers.

## Demo retrieval

Demo retrieval uses `demo/internvideo2_stage2_config.py`, `demo/utils.py`, and the notebook example in `demo_video_text_retrieval.ipynb`. The demo guide highlights a relative-import pitfall: the multi-modality folder must be importable via `PYTHONPATH`, or the config and helper modules should be rewritten to use absolute imports rooted at that folder.

Demo setup usually requires:

1. A tokenizer folder for the text encoder.
2. A Stage2 checkpoint file for `pretrained_path` or `vision_encoder.pretrained`.
3. A candidate text list and a small set of decoded frames.

`demo/utils.py` shows how to tokenize candidate text, build frame tensors, load the model, and rank retrieved captions. The demo is intentionally a local inference path, not a job submission path.

## Preprocess / annotation conversion

`preprocess/create_sqlite_db.py` converts a JSON annotation list into a SQLite table named `annos`. Each record should contain the media key (`image` or `video`) plus `caption`.

The conversion pattern is useful as schema evidence, but it is not a good default runtime action. Validate the JSON list and the destination path before any destructive conversion.

## Launcher layers

`tools/run.py` is the source launcher abstraction. It chooses SLURM or local mode, stages code under `VL_EXP_DIR/<jobname>/code`, writes `cmd.txt`, and forwards the selected Python entry point through `tools/submit.sh` and `torchrun.sh`.

The source shell launchers are thin wrappers around that idea:

- set `MASTER_PORT` and `OMP_NUM_THREADS`;
- export `PYTHONPATH` so config/model/utils imports resolve;
- choose `tasks/pretrain.py` or `tasks_clip/*.py`;
- pass the config file and `output_dir` plus overrides such as `evaluate True` and `pretrained_path`.

For review or command construction, prefer the bundled helper rather than the source submitter.
