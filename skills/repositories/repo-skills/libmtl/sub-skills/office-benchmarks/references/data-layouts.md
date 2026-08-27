# Office Data Layouts

## Split files

The split text files are bundled twice so both documentation and runtime code
are self-contained:

```text
references/data_txt/                         # human-readable reference copy
scripts/office_runtime/src/libmtl_office_benchmark/data_txt/  # package data used at runtime
```

Each tree has one subdirectory per dataset family:

```text
office-31/
office-home/
```

Each split file line contains an image path relative to the raw image root and a
label index separated by a space.

## Raw image roots

Point `--dataset_path` at the root directory that contains the actual images for
all domains in the selected dataset family.

- Office-31 domains: `amazon`, `dslr`, `webcam`
- Office-Home domains: `Art`, `Clipart`, `Product`, `Real_World`

## Minimal validation idea

A valid setup should let the split files resolve to actual image files for the
chosen dataset family, and every split should be non-empty. Use:

```bash
python scripts/check_office_data.py office-31 /path/to/office --check-runtime-package
```

to check both the reference split tree and the packaged runtime split tree.
