# Detection And Demography API Reference

## `DeepFace.extract_faces`

```python
DeepFace.extract_faces(img_path, detector_backend="opencv", enforce_detection=True, align=True, expand_percentage=0, grayscale=False, color_face="rgb", normalize_face=True, anti_spoofing=False) -> list[dict] | list[list[dict]]
```

Each face dictionary contains `face`, `facial_area`, and `confidence`. `facial_area` includes `x`, `y`, `w`, `h`, `left_eye`, and `right_eye`; some detectors also supply `nose`, `mouth_left`, and `mouth_right`. Invalid landmarks are sanitized to `None`. `color_face` can be `rgb`, `bgr`, or `gray`. `normalize_face=True` divides returned face pixels by 255.

## `DeepFace.analyze`

```python
DeepFace.analyze(img_path, actions=("emotion", "age", "gender", "race"), enforce_detection=True, detector_backend="opencv", align=True, expand_percentage=0, silent=False, anti_spoofing=False) -> list[dict] | list[list[dict]]
```

Valid actions are `emotion`, `age`, `gender`, and `race`. Output dictionaries include `region` and `face_confidence`; keys for actions not requested are absent or `None` in downstream expectations.

## Detectors And Anti-Spoofing

Detector identifiers include `opencv`, `mtcnn`, `ssd`, `dlib`, `retinaface`, `mediapipe`, YOLO variants `yolov8*`, `yolov11*`, `yolov12*`, `yunet`, `fastmtcnn`, and `centerface`. Workflow APIs may also accept `skip` to bypass detection. When `anti_spoofing=True`, face extraction can include `is_real` and `antispoof_score`; consuming workflows can raise `SpoofDetected` for fake faces.
