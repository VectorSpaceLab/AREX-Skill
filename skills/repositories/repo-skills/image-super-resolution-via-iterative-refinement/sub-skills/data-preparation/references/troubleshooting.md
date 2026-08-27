# Troubleshooting

Scope: dataset roots, image-directory triplets, LMDB keys, and tiny fixture creation.

Use [data-layouts.md](data-layouts.md) first for the expected storage contract. Use [`../scripts/validate_dataset_layout.py`](../scripts/validate_dataset_layout.py) to confirm an `img` layout and [`../scripts/prepare_tiny_dataset.py`](../scripts/prepare_tiny_dataset.py) to generate a clean smoke fixture.

## Common failure modes

| Symptom | Likely cause | What to do next |
| --- | --- | --- |
| `... is not a valid directory` or `... has no valid image file` | `dataroot` points to the wrong root, or the prepared tree is empty / contains no supported image files. | Point the config at the final prepared root, then rerun the validator. |
| `data_type [...] is not recognized` | `datatype` is neither `img` nor `lmdb`. | Match `datatype` to the storage style described in [data-layouts.md](data-layouts.md). |
| Missing `lr_<L>`, `hr_<R>`, or `sr_<L>_<R>` directories | The resize step did not finish, the resolution pair is wrong, or the config points at the unsuffixed source folder. | Rebuild the root, verify the pair `(l_resolution, r_resolution)`, and confirm the final suffixed directory name. |
| Layout validator reports mismatched counts or paths | One tree has a missing sample, a stray file, or different filenames / nesting. | Remove stray files, rebuild the tree, and rerun [`../scripts/validate_dataset_layout.py`](../scripts/validate_dataset_layout.py). |
| Source conversion crashes while opening a file | The preprocessing input tree contains a non-image file or a corrupted image. | Clean the source tree so it contains only real images, then rerun the conversion. |
| LMDB load fails around `length` or a missing sample key | The LMDB write was interrupted, or the keys do not follow `length`, `lr_<L>_<index>`, `hr_<R>_<index>`, `sr_<L>_<R>_<index>`. | Recreate the LMDB from scratch and keep the zero-padded five-digit index convention. |
| Samples loop over random indices in LMDB mode | Some indexed keys are missing, so the loader keeps retrying until it finds a complete sample. | Treat the LMDB as incomplete and rebuild it; do not try to patch a few keys by hand. |
| Colors or channels look wrong | The source data were grayscale, RGBA, or otherwise not RGB. | Re-run preparation on clean RGB inputs; the source converter and loader both normalize to RGB. |
| `mode: HR` still needs SR images | The user expected the loader to ignore `sr_<L>_<R>`. | Keep the SR folder in place; `mode: HR` skips LR, not SR. |

## Quick recovery recipes

### Make a known-good smoke root

```bash
python scripts/prepare_tiny_dataset.py --out ./tiny_fixture --l-resolution 16 --r-resolution 128 --count 3
python scripts/validate_dataset_layout.py --root ./tiny_fixture --l-resolution 16 --r-resolution 128
```

### Check a suspicious image root

```bash
python scripts/validate_dataset_layout.py --root ./candidate_root --l-resolution 64 --r-resolution 512
```

If that fails, inspect the reported missing or mismatched relative paths before trying a full training or inference run.

## When to stop and escalate

Stop after the layout contract is confirmed if the remaining problem is:

- a missing external dataset download,
- a missing checkpoint,
- a broken LMDB that must be rebuilt from the original source data,
- or a source tree that still contains unreadable files after cleanup.

Those are upstream data issues, not layout-routing problems.
