# API Service Workflows

## Dry-Run A Request

```bash
python sub-skills/api-service/scripts/deepface_api_request.py --endpoint verify --img1 img1.jpg --img2 img2.jpg --dry-run
```

The helper prints a curl command and JSON payload without sending network traffic.

## Environment Variables

- `DEEPFACE_AUTH_TOKEN` enables bearer-token auth.
- `DEEPFACE_DATABASE_TYPE` selects DB backend for database routes.
- `DEEPFACE_CONNECTION_DETAILS` provides API-level DB connection details.
- `DEEPFACE_FACE_RECOGNITION_MODELS` and `DEEPFACE_FACE_DETECTION_MODELS` preload comma-separated models on startup.

## Streaming

```python
DeepFace.stream(db_path="known_faces", model_name="VGG-Face", detector_backend="opencv", source=0, time_threshold=5, frame_threshold=5)
```

Streaming needs camera/video access and GUI/display support. It can trigger model-weight downloads and local folder datastore updates, so ask before running it in offline or read-only contexts.
