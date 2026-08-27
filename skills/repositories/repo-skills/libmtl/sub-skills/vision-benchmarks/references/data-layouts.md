# Vision Data Layouts

## NYUv2

The preprocessed NYUv2 example expects this tree:

```text
nyuv2/
├── train/
│   ├── depth/
│   ├── image/
│   ├── label/
│   └── normal/
└── val/
    ├── depth/
    ├── image/
    ├── label/
    └── normal/
```

Notes:

- Files are stored as `.npy` arrays.
- The bundled NYUv2 layout checker in this skill assumes this layout.
- The benchmark treats NYUv2 as a single-input task, so one dataloader yields
  `(image, {task: label})`.

## Cityscapes

The preprocessed Cityscapes example expects this tree:

```text
cityscapes2/
├── train/
│   ├── depth/
│   ├── image/
│   └── label/
└── val/
    ├── depth/
    ├── image/
    └── label/
```

Notes:

- Files are also stored as `.npy` arrays.
- The benchmark uses the preprocessed Cityscapes variant described in the repo
  docs, not the raw segmentation release.
- The Cityscapes workflow reuses the NYUv2 helper modules via a sibling
  import path.

## Minimal validation idea

A valid data root should at least have non-empty `train/image` and `val/image`
folders, plus the matching task label folders for the selected benchmark.
