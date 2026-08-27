# API Service Troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| HTTP 401 with auth message | `DEEPFACE_AUTH_TOKEN` is set and token is missing/wrong. | Add `Authorization: Bearer <token>` or disable auth for local testing. |
| HTTP 400 for image key | Missing `img`, `img1`, or `img2`. | Match endpoint-required image keys. |
| HTTP 400 wrapping DeepFace exception | Underlying model/input/detector workflow failed. | Route error text to the owning sub-skill. |
| Database route says connection details are missing | DB env vars are missing. | Set `DEEPFACE_CONNECTION_DETAILS` or backend-specific env vars. |
| Gunicorn timeout | First request is building/downloading models or processing large inputs. | Preload selected models or increase timeout after approving resource use. |
| Stream window failure | Headless environment or no camera/display. | Use non-streaming APIs or provide display/video backend. |
