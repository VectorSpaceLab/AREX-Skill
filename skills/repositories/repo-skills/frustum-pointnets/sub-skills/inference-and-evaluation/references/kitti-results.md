# KITTI result format

The source writer emits one text file per frame under a `data/` directory. A
prediction row contains the KITTI object type, placeholder fields, 2D box,
3D dimensions and location, rotation, and confidence. A conventional rendered
row has 15 whitespace-separated fields:

```text
Type truncation occlusion alpha xmin ymin xmax ymax h w l x y z rotation score
```

The validator checks field count, finite numeric values, ordered 2D coordinates,
known object type, and non-empty frame filenames. It cannot prove geometric
correctness or AP.

The source also optionally dumps a Python pickle of model outputs. Treat that
as an experiment artifact tied to the exact Python/pickle environment; do not
assume it is interchangeable with the preparation pickle stream.
