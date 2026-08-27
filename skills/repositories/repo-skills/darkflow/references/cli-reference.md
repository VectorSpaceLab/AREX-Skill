# CLI Reference

## Purpose

Read this when you need the canonical `flow` command options, default values, and where each flag is used. The source of truth is `darkflow/defaults.py`, with usage examples reinforced by the README and source code.

## Entry point

The package installs a `flow` command that calls `darkflow.cli.cliHandler(sys.argv)`. The handler parses a small custom flag set and creates any missing output folders before dispatching into `TFNet`. If the executable is not on `PATH`, use the skill-owned wrapper `../scripts/flow.py` with the same arguments.

## Flag groups

### Input and model selection

| Flag | Default | Notes |
| --- | --- | --- |
| `--imgdir` | `./sample_img/` | Image directory for prediction and demo output. |
| `--binary` | `./bin/` | Folder that holds `.weights` files. |
| `--config` | `./cfg/` | Folder that holds `.cfg` files and bundled label files. |
| `--model` | empty | Path to the configuration file to load. |
| `--load` | empty | Load from weights path, checkpoint step, or scratch. Integer values are treated as checkpoint steps. |
| `--labels` | `labels.txt` | Custom label file for non-VOC / non-COCO model names. |
| `--pbLoad` | empty | Load a frozen graph instead of a `.cfg` / `.weights` pair. |
| `--metaLoad` | empty | Load the JSON metadata that accompanies `--pbLoad`. |

### Training and checkpoints

| Flag | Default | Notes |
| --- | --- | --- |
| `--train` | `false` | Switch into training mode. |
| `--dataset` | `../pascal/VOCdevkit/IMG/` | Image directory used for training batches. |
| `--annotation` | `../pascal/VOCdevkit/ANN/` | Pascal VOC XML annotation directory. |
| `--trainer` | `rmsprop` | Optimizer name: `rmsprop`, `adam`, `momentum`, `sgd`, and others listed in source. |
| `--momentum` | `0.0` | Used by RMSProp / momentum optimizers. |
| `--lr` | `1e-5` | Learning rate. |
| `--batch` | `16` | Batch size. |
| `--epoch` | `1000` | Number of epochs. |
| `--save` | `2000` | Save checkpoint every N training examples. |
| `--keep` | `20` | Number of checkpoints to retain. |
| `--summary` | empty | TensorBoard summary directory. |

### Inference, demo, and export

| Flag | Default | Notes |
| --- | --- | --- |
| `--threshold` | `-0.1` | Detection threshold. `TFNet` also respects a positive override. |
| `--json` | `false` | Emit prediction JSON instead of drawing boxes. |
| `--demo` | empty | Run camera or video demo. Use `camera` for the webcam. |
| `--queue` | `1` | Batch size for demo frame buffering. |
| `--saveVideo` | `false` | Save demo output to `video.avi`. |
| `--savepb` | `false` | Export a frozen graph and metadata. |
| `--gpu` | `0.0` | Fraction of the TensorFlow GPU memory budget. `0.0` keeps the run on CPU. |
| `--gpuName` | `/gpu:0` | TensorFlow device name for GPU placement. |
| `--verbalise` | `true` | Print build and run progress messages. |

## Parsing notes

- Boolean flags can be passed as bare flags or as explicit `true` / `false` values.
- Numeric flags are type-checked during parsing.
- `--help`, `--h`, and `-h` all print the built-in help text and exit.
- The handler auto-creates the image, binary, backup, and output folders it needs.

## Useful command patterns

```bash
flow --help
python ../scripts/flow.py --help
flow --imgdir <image_dir> --model <model.cfg> --load <weights.weights>
flow --imgdir <image_dir> --model <model.cfg> --load <weights.weights> --json
flow --model <model.cfg> --load <weights-or-checkpoint> --savepb
flow --pbLoad <graph.pb> --metaLoad <graph.meta> --imgdir <image_dir>
```

## When to read next

- Use `api-reference.md` for `TFNet` signatures and return values.
- Use `model-overview.md` when choosing a bundled config or custom label set.
- Use `../sub-skills/inference/SKILL.md` or `../sub-skills/training/SKILL.md` for workflow steps, not just flag meanings.
