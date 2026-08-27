# COCO Object Classes and `CustomObjects` Names

`ObjectDetection.CustomObjects(...)` creates a boolean filter for COCO classes. The function builds keyword names by taking the loaded object label and replacing spaces with underscores. For example, `traffic light` becomes `traffic_light`, `cell phone` becomes `cell_phone`, and `teddy bear` becomes `teddy_bear`.

Important model-family detail: YOLOv3/TinyYOLOv3 use the 80-label `coco_classes.txt` list. RetinaNet switches internally to `coco91_classes.txt` after `loadModel()`, which includes `unlabeled` and additional COCO91 category names. This affects exact label names such as `motorbike` versus `motorcycle`, `aeroplane` versus `airplane`, `sofa` versus `couch`, `pottedplant` versus `potted_plant`, `diningtable` versus `dining_table`, and `tvmonitor` versus `tv`.

## COCO80 labels used by YOLOv3/TinyYOLOv3

Use these names as `CustomObjects` keyword arguments exactly, replacing spaces with underscores where shown:

```text
person, bicycle, car, motorbike, aeroplane, bus, train, truck, boat,
traffic_light, fire_hydrant, stop_sign, parking_meter, bench, bird, cat,
dog, horse, sheep, cow, elephant, bear, zebra, giraffe, backpack,
umbrella, handbag, tie, suitcase, frisbee, skis, snowboard, sports_ball,
kite, baseball_bat, baseball_glove, skateboard, surfboard, tennis_racket,
bottle, wine_glass, cup, fork, knife, spoon, bowl, banana, apple,
sandwich, orange, broccoli, carrot, hot_dog, pizza, donut, cake, chair,
sofa, pottedplant, bed, diningtable, toilet, tvmonitor, laptop, mouse,
remote, keyboard, cell_phone, microwave, oven, toaster, sink,
refrigerator, book, clock, vase, scissors, teddy_bear, hair_drier,
toothbrush
```

Example:

```python
custom = detector.CustomObjects(car=True, motorbike=True, cell_phone=True)
```

## COCO91 labels used by RetinaNet after load

RetinaNet source reloads the label list from `coco91_classes.txt` inside `loadModel()`. The file contains:

```text
unlabeled, person, bicycle, car, motorcycle, airplane, bus, train, truck,
boat, traffic_light, fire_hydrant, street_sign, stop_sign, parking_meter,
bench, bird, cat, dog, horse, sheep, cow, elephant, bear, zebra, giraffe,
hat, backpack, umbrella, shoe, eye_glasses, handbag, tie, suitcase,
frisbee, skis, snowboard, sports_ball, kite, baseball_bat,
baseball_glove, skateboard, surfboard, tennis_racket, bottle, plate,
wine_glass, cup, fork, knife, spoon, bowl, banana, apple, sandwich,
orange, broccoli, carrot, hot_dog, pizza, donut, cake, chair, couch,
potted_plant, bed, mirror, dining_table, window, desk, toilet, door, tv,
laptop, mouse, remote, keyboard, cell_phone, microwave, oven, toaster,
sink, refrigerator, blender, book, clock, vase, scissors, teddy_bear,
hair_drier, toothbrush, hair_brush
```

Example:

```python
custom = detector.CustomObjects(car=True, motorcycle=True, cell_phone=True)
```

## Practical filtering rules

- Build `CustomObjects` after the detector has enough information to load the model. The method calls `loadModel()` if the model is not already loaded.
- If `CustomObjects` raises `ValueError: object '...' doesn't exist`, check the exact model family label list above and the space-to-underscore rule.
- For a car/motorcycle task:
  - YOLOv3/TinyYOLOv3 COCO: use `car=True, motorbike=True`.
  - RetinaNet COCO: use `car=True, motorcycle=True`.
- For a phone/person task: use `person=True, cell_phone=True`.
- `CustomObjectDetection` does not provide `CustomObjects()`, but its `detectObjectsFromImage(custom_objects=...)` parameter accepts a dictionary with label keys. Build keys from the custom JSON `labels` values with spaces replaced by underscores.
