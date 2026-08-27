# Detection And Demography Troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `Face could not be detected` | No face found and `enforce_detection=True`. | Try a better image/detector, adjust alignment/expansion, or explicitly set `enforce_detection=False` if full-image fallback is acceptable. |
| `Invalid action passed` | `actions` contains a value outside `emotion`, `age`, `gender`, `race`. | Normalize form strings to a list and remove unsupported actions. |
| `The color_face can be rgb, bgr or gray` | Invalid `color_face` argument. | Use exactly `rgb`, `bgr`, or `gray`. |
| Optional detector import error | Detector backend needs an extra package such as dlib, mediapipe, ultralytics, facenet-pytorch, insightface, or onnxruntime. | Route to `../model-and-backend-selection/references/optional-dependencies.md`. |
| `Spoof detected` | `anti_spoofing=True` and the spoofing model marked the face as fake. | Do not override silently; ask whether to reject, review manually, or rerun without anti-spoofing for comparison. |
| Landmarks missing or `None` | Detector did not return valid coordinates or coordinates were outside image bounds. | Use bounding box-only downstream logic, choose another detector, or avoid eye-dependent assumptions. |
