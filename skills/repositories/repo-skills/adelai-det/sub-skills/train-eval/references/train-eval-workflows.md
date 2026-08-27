# Training and evaluation workflows

The repository's training entry point follows Detectron2 launch conventions. Use the skill-owned wrapper to validate paths and compose commands.

## Dry-run command

```bash
python scripts/run_train_eval.py --repo-root /path/to/AdelaiDet \
  --config configs/FCOS-Detection/R_50_1x.yaml \
  --num-gpus 1 --dry-run
```

The wrapper checks that `tools/train_net.py` and the config exist, then prints the command.

## Train

```bash
python scripts/run_train_eval.py --repo-root /path/to/AdelaiDet \
  --config configs/BlendMask/R_50_1x.yaml \
  --num-gpus 4 \
  --opts OUTPUT_DIR output/blendmask_r50 SOLVER.IMS_PER_BATCH 16
```

The command maps to:

```bash
python tools/train_net.py --num-gpus 4 --config-file <config> OUTPUT_DIR ...
```

## Resume

```bash
python scripts/run_train_eval.py --repo-root /path/to/AdelaiDet \
  --config configs/BlendMask/R_50_1x.yaml \
  --num-gpus 4 --resume \
  --opts OUTPUT_DIR output/blendmask_r50
```

Resume expects Detectron2 checkpoint artifacts in `OUTPUT_DIR`.

## Evaluation only

```bash
python scripts/run_train_eval.py --repo-root /path/to/AdelaiDet \
  --config configs/FCOS-Detection/R_50_1x.yaml \
  --eval-only --model-weights /path/to/model.pth --num-gpus 1 \
  --opts OUTPUT_DIR output/fcos_eval
```

The wrapper appends `MODEL.WEIGHTS <path>` to the override list.

## Multi-machine launch

Use Detectron2's distributed flags only when you know the rendezvous URL and machine ranks:

```bash
python scripts/run_train_eval.py --repo-root /path/to/AdelaiDet \
  --config configs/CondInst/MS_R_50_1x.yaml \
  --num-gpus 8 --num-machines 2 --machine-rank 0 \
  --dist-url tcp://host0:12345 --dry-run
```

Run the same command with `--machine-rank 1` on the other host.

## Outputs

Typical Detectron2 outputs are controlled by `OUTPUT_DIR`:

- `config.yaml` / copied config
- logs and TensorBoard files
- `model_*.pth` checkpoints
- `model_final.pth`
- evaluation JSON/text files depending on evaluator

## Failure routing

- `No module named ...`, `PIL.Image.LINEAR`, `rapidfuzz.string_metric`, extension import failures → `setup-build`.
- Missing dataset files or unregistered dataset names → `data-prep`.
- Text recognition/evaluation errors → `text-spotting`.
- Checkpoint key mismatch → `export-convert`.
- CUDA out-of-memory → reduce `SOLVER.IMS_PER_BATCH`, image size, workers, or GPU count; keep config/device overrides explicit.
