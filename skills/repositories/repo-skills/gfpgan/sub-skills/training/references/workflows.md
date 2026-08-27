# GFPGAN Training and Support Workflows

## Purpose

Read this for operational GFPGAN training, dataset preparation, landmark parsing, validation, and checkpoint conversion workflows.

## Workflow 1: Choose Simple vs Full Training Config

Use the simple config when:

- The user has high-quality face images but no component landmark file.
- They need a smaller setup surface for experimentation.
- They do not need facial component discriminators or identity loss.

Use the full config when:

- `crop_components: true` is desired.
- The user has `FFHQ_eye_mouth_landmarks_512.pth` or can generate it.
- Identity loss and component discriminators are part of the objective.

## Workflow 2: Prepare FFHQ-Style Data

1. Collect high-quality 512x512-ish face images.
2. Choose disk or LMDB backend.
3. If using disk, configure `dataroot_gt` as a folder of images.
4. If using LMDB, ensure `dataroot_gt` ends with `.lmdb` and contains `meta_info.txt`.
5. Decide whether component crops are enabled.
6. If component crops are enabled, generate or download a compatible landmark `.pth` file.

Validate layout with a tiny fixture before full training.

## Workflow 3: Parse Landmarks

```bash
python sub-skills/training/scripts/parse_ffhq_landmarks.py \
  --json-path ffhq-dataset-v2.json \
  --save-path FFHQ_eye_mouth_landmarks_512.pth \
  --scale 0.5 \
  --enlarge-ratio 1.4
```

The parser reads FFHQ JSON face landmarks and writes a PyTorch `.pth` dictionary containing `left_eye`, `right_eye`, and `mouth` triples for each image entry. Add `--save-crops-dir` only when visual crop previews are explicitly needed.

## Workflow 4: Validate A Config Without Full Training

```bash
python sub-skills/training/scripts/check_env.py --config train_gfpgan_v1.yml --json
```

This validates imports, important signatures, CUDA visibility, and YAML readability. If you need a dataset item smoke, use a tiny local fixture rather than the full FFHQ dataset.

## Workflow 5: Launch Training

The source launcher delegates to BasicSR:

```bash
python -m torch.distributed.launch --nproc_per_node=4 --master_port=22021 \
  -m gfpgan.train -opt train_gfpgan_v1.yml --launcher pytorch
```

Before launching:

- Check `path.pretrain_network_g`, `network_g.decoder_load_path`, and identity/component checkpoint paths.
- Check train/val data paths.
- Confirm GPUs, memory, and distributed backend.
- Decide where logs, checkpoints, and visualizations should be written.

## Workflow 6: Convert A Checkpoint To Clean Format

The FAQ says the clean v1.2 model was converted from a bilinear model; fine-tuning that model should fine-tune the bilinear model and convert afterward.

```bash
python sub-skills/training/scripts/convert_checkpoint_to_clean.py \
  --ori-path source_bilinear_checkpoint.pth \
  --save-path converted_clean_checkpoint.pth \
  --narrow 1 \
  --channel-multiplier 2
```

The converter expects a checkpoint with `params_ema` by default. Use `--param-key params` if the source checkpoint stores weights under a different top-level key.

## Workflow 7: Fine-Tuning Decision Flow

1. Identify the target output style/version.
2. If the target is a clean checkpoint derived from bilinear, fine-tune the bilinear/source architecture first.
3. Keep StyleGAN2 decoder and identity/component checkpoint requirements explicit.
4. Convert only after verifying the source checkpoint contains the expected key patterns.
5. Run a small inference smoke with the converted checkpoint before committing to long training.

## Validation Expectations

- Dataset smoke proves data layout and degradation dependencies.
- 32x32 architecture smoke proves model wiring and CUDA basics.
- Full training proof requires long GPU runs and real data; do not substitute a smoke test for convergence evidence.
