# Post-processing and Training

Viseron post-processors run after object detection. They receive object events from the object detector's field-of-view and zone outputs, filter those objects by post-processor `labels`, optionally apply a post-processor mask, and then run face recognition, image classification, or license plate recognition.

## Shared post-processor rules

Post-processor config uses the shared shape:

```yaml
face_recognition:
  cameras:
    front_door:
      labels:
        - person
      mask:
        - coordinates:
            - {x: 0, y: 0}
            - {x: 300, y: 0}
            - {x: 300, y: 300}
            - {x: 0, y: 300}
  labels:
    - person
```

Rules:

- `labels` under a specific camera override the global post-processor `labels` for that camera.
- If no post-processor labels are set, the post-processor runs for all objects emitted by the object detector.
- Only objects tracked by `object_detector.labels` or `object_detector.zones[].labels` can be passed to post-processors.
- The source object also has to pass object-detector filters such as confidence, width/height, masks, zones, and motion-overlap recording gates that affect object relevance.
- Post-processor masks exclude areas from the frame before processing; they do not make the object detector track a missing label.

## Face recognition

Supported face recognition providers:

| Component | Training source | Key settings |
|---|---|---|
| `dlib` | Local `face_recognition_path` folder. | `model` can be `hog` or `cnn`; shared settings include `save_faces`, `save_unknown_faces`, `expire_after`, `labels`, `mask`. |
| `codeprojectai` | Local face folder uploaded to a CodeProject.AI server when `train: true`. | `host`, `port`, `timeout`, `train`, `min_confidence`, face folder and save/expire settings. |
| `deepstack` | Local face folder uploaded to DeepStack when `train: true`. | `host`, `port`, optional `api_key`, `timeout`, `train`, `min_confidence`, face folder and save/expire settings. |
| `compreface` | Local face folder uploaded to CompreFace when `train: true`, or service subjects when `use_subjects: true`. | `host`, `port`, `recognition_api_key`, `det_prob_threshold`, `similarity_threshold`, `limit`, `prediction_count`, `face_plugins`, `status`, `use_subjects`. |

Default face folder structure is strict:

```text
/config/face_recognition/faces/
  person1/
    image1.jpg
    image2.png
  person2/
    image1.jpeg
```

Training notes:

- The folder must contain one subdirectory per person; loose image files at the face-folder root are invalid.
- `unknown` is reserved for unknown-face output and is not used as a training subject.
- CodeProject.AI, DeepStack, and CompreFace training code skips images that contain no face or more than one face.
- `save_unknown_faces: true` helps collect candidate images, but a user must move good unknown snapshots into the correct person's folder and retrain.
- `expire_after` controls how long a face remains considered detected before expiry events/sensors clear.
- `save_faces` and `save_unknown_faces` control database/snapshot persistence, not recognition itself.

Provider-specific behavior:

- `dlib.model: hog` is CPU-friendly and less accurate; `cnn` is more accurate and can use CUDA when the target environment supports it.
- `compreface.similarity_threshold` decides whether a returned subject is treated as known or `unknown`; CompreFace may return the closest subject even for unfamiliar faces.
- `compreface.use_subjects: true` ignores the local folder structure for entities and creates subject entities from the service. If subjects change, update subject entities through Viseron's CompreFace update path.
- External-service timeouts and connection errors are logged and should be treated as service availability problems, not object-detector label failures.

## Image classification

`edgetpu.image_classification` classifies cropped object images after object detection. Common use: detect a coarse object such as `bird`, then classify a more specific type with an image-classification model.

Key settings:

- `labels`: object labels that should trigger classification. These must be labels emitted by the object detector.
- `model_path`: TensorFlow Lite classifier model path. If omitted, Viseron chooses a default EdgeTPU or CPU model based on `device`.
- `device`: `cpu`, `usb`, `usb:<N>`, `pci`, `pci:<N>`, `:<N>`, or a list of devices.
- `label_path`: classifier labels file.
- `crop_correction`: padding in pixels added around the detected object's bounding box before resizing to the classifier input size. Increase it if the object crop is too tight; decrease it if too much background hurts classification.
- `expire_after`: time before a classification result is cleared.

Because image classification returns one or more class labels for an object crop, it should not be used as a substitute for object detection when the first task is locating objects in the whole frame.

## License plate recognition

`codeprojectai.license_plate_recognition` runs as a post-processor over detected objects, usually vehicle-related labels such as `car`, `truck`, `vehicle`, or whatever the selected object model actually emits.

Key settings:

- top-level `codeprojectai.host`, `port`, and `timeout`.
- `license_plate_recognition.cameras.<camera>.labels`: object labels whose crops should be sent to LPR.
- `known_plates`: plate strings that get dedicated binary sensors.
- `min_confidence`: minimum plate confidence from the LPR service.
- `save_plates`: store plate results and snapshots.
- `expire_after`: time before a plate result expires.

LPR crops each matched detected object, sends the crop to CodeProject.AI, converts the plate box back to relative camera coordinates, and marks whether the plate is in `known_plates`.

## Post-processor debugging checklist

1. Confirm the object detector is configured and producing the source object label.
2. Confirm the source object passes object-detector confidence, size, mask, and zone filters.
3. Confirm post-processor `labels` match object labels exactly. A camera-level labels list overrides the global list.
4. Confirm post-processor masks do not hide the face, object crop, or plate region.
5. For face recognition, confirm the training folder exists, contains per-person subdirectories, and each training image has exactly one recognizable face.
6. For external services, confirm host/port/API key/timeout and service module availability from the target Viseron runtime.
7. For EdgeTPU classification, confirm model, label file, and device selection match each other.
8. Distinguish "post-processor did not run" from "post-processor ran but returned unknown/no result" by checking whether source object events are present and whether provider-specific logs show a service/model result.
