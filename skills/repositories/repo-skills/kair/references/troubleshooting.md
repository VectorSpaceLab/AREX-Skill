# KAIR troubleshooting index

Use this root page to route failures to the right sub-skill. For detailed procedures, open the linked sub-skill reference.

## Fast routing table

| Symptom or request | Route |
| --- | --- |
| Option JSON parse error, DDP launch mismatch, checkpoint auto-resume, GAN config mismatch | `sub-skills/image-training/references/troubleshooting.md` |
| Missing image checkpoint, no output images, SwinIR OOM, hard-coded image testing script edits | `sub-skills/image-testing/references/troubleshooting.md` |
| VRT/RVRT task ID, tile/OOM, custom CUDA extension, missing video data, VRT static-graph resume | `sub-skills/video-restoration/references/troubleshooting.md` |
| Dataset folder depth, image/video pair mismatches, LMDB meta-info/key issues, destructive prep scripts | `sub-skills/data-preparation/references/troubleshooting.md` |
| Missing dependencies, CUDA unavailable, `nvcc`/`ninja` problems, source import checks | `references/setup-and-environment.md` and `scripts/kair_check_environment.py` |
| Checkpoint download source/path selection | `references/model-zoo-and-downloads.md` and `scripts/kair_download_models.py` |

## Cross-cutting fixes

### Always confirm the working directory

Most KAIR scripts assume the current working directory is the checkout root. If a user runs a script from another directory, defaults such as `model_zoo`, `testsets`, `trainsets`, and `results` may resolve incorrectly.

### Avoid hidden downloads during diagnosis

Before running scripts that may auto-download checkpoints or datasets, run a dry-run checkpoint plan:

```bash
python skills/disco/kair/scripts/kair_download_models.py --models "<group-or-file>"
```

Then ask the user whether to download with `--execute`.

### Separate command construction from execution

For command planning, prefer bundled dry-run helpers:

```bash
python skills/disco/kair/sub-skills/image-testing/scripts/build_image_test_command.py --help
python skills/disco/kair/sub-skills/video-restoration/scripts/build_video_restoration_command.py --help
python skills/disco/kair/sub-skills/image-training/scripts/validate_training_config.py --config <option.json>
python skills/disco/kair/sub-skills/data-preparation/scripts/check_dataset_layout.py --help
```

These helpers do not import KAIR or start inference/training.

### Treat CPU-only success as partial

CPU-only parser checks can be useful, but they do not verify full KAIR runtime for:

- VRT/RVRT video transformer inference/training.
- RVRT guided deformable attention custom CUDA extension.
- Face enhancement custom op path.
- Large SwinIR or challenge SR workloads.

For those workflows, require a CUDA-capable PyTorch build and, for custom ops, `nvcc` and `ninja`.

### Preserve partial outputs and checkpoints

If training or downloads fail with a transient network, capacity, or CUDA error, do not delete partial experiment folders by default. KAIR training can resume from numbered checkpoints in the derived `models/` directory. Diagnose the error, then resume deliberately with the same option JSON or change the `task`/experiment root to start fresh.

## Known KAIR quirks

- Option JSON files can contain `//` comments. The parser strips text after `//` per line before JSON loading, so URLs or strings containing `//` can be corrupted if inserted naively.
- `gpu_ids` in option JSON becomes `CUDA_VISIBLE_DEVICES`; for DDP, match the list length with `--nproc_per_node`.
- Some image testing scripts are hard-coded instead of argparse-driven. Treat them as templates and either edit a copy or use the relevant reference table.
- `main_test_swinir.py`, `main_test_vrt.py`, and `main_test_rvrt.py` can auto-download missing assets.
- `network_faceenhancer.py` imports `op` as a top-level module, so a wrapper may need `PYTHONPATH=$PWD/models:$PWD`.
- RVRT can fail at custom extension build time even when VRT and standard PyTorch CUDA work.
- Several data preparation scripts move, copy, delete, or create many files. Use the data-preparation checker/planner first and run destructive scripts only on reviewed data copies.
