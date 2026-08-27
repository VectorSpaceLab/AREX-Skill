# KITTI inputs and outputs

## Dataset root

The data root is a KITTI Object Detection tree:

```text
<dataset-root>/
  training/
    calib/       # 000000.txt, ...
    image_2/     # 000000.png, ...
    label_2/     # 000000.txt, ...
    velodyne/    # 000000.bin, ...
  testing/
    calib/
    image_2/
    velodyne/
```

The repository's preparation code uses the `training` split for both train and
validation frustums. Index files contain one integer frame id per line. Check
that every selected id has the corresponding image, calibration, Velodyne, and
(for labeled branches) label files.

## RGB detector rows

`read_det_file` expects whitespace-separated rows:

```text
image_path type_id confidence xmin ymin xmax ymax
```

The source maps type ids `1 -> Pedestrian`, `2 -> Car`, and `3 -> Cyclist`.
The image basename supplies the numeric frame id. Coordinates are floating
point image pixels; confidence is a floating point score. Reject blank,
non-numeric, reversed, or non-finite boxes before conversion.

RGB-detection preparation writes a pickle stream containing, in order:
`id_list`, `box2d_list`, `input_list`, `type_list`, `frustum_angle_list`, and
`prob_list`. Labeled preparation writes nine sequential objects: ids, 2D boxes,
3D boxes, frustum point arrays, point labels, types, headings, box dimensions,
and frustum angles. It is not a single portable dictionary.

## Geometry and filters

Point clouds are transformed into rectified camera coordinates while intensity
is kept as the fourth channel. Frustums are selected by projecting points into
the image and intersecting a 2D box. Labeled extraction rejects boxes shorter
than 25 pixels or with no positive points. RGB extraction defaults to a
25-pixel image-height threshold and a five-point minimum. The center pixel and
a nominal depth of 20 are used to derive a frustum angle; preserve this
convention when comparing outputs.
