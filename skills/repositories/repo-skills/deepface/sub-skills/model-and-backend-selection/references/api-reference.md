# Model And Backend API Reference

## `DeepFace.build_model`

```python
DeepFace.build_model(model_name: str, task: str = "facial_recognition") -> object
```

Valid tasks are `facial_recognition`, `facial_attribute`, `face_detector`, and `spoofing`. DeepFace caches built models in-process. Building a model may download weights, so avoid it during static inspection unless the user approves.

Recognition models include `VGG-Face`, `OpenFace`, `Facenet`, `Facenet512`, `DeepFace`, `DeepID`, `Dlib`, `ArcFace`, `SFace`, `GhostFaceNet`, and `Buffalo_L`.

Demography models are `Emotion`, `Age`, `Gender`, and `Race`; spoofing uses `Fasnet`. Detectors include `opencv`, `mtcnn`, `ssd`, `dlib`, `retinaface`, `mediapipe`, YOLO variants, `yunet`, `fastmtcnn`, and `centerface`.
