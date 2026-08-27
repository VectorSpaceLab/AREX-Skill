# API Endpoint Reference

DeepFace's Flask app factory is `deepface.api.src.app:create_app`. With Gunicorn installed:

```bash
gunicorn --workers=1 --timeout=3600 --bind=0.0.0.0:5005 "deepface.api.src.app:create_app()"
```

Routes: `/` (GET), `/represent`, `/verify`, `/analyze`, `/register`, `/search`, and `/build/index` (POST). Requests may be JSON, form data, or multipart file upload. JSON/form image values may be server-visible paths, URLs, or base64 data URIs.

| Route | Required image keys | Underlying workflow |
|---|---|---|
| `/represent` | `img` | `DeepFace.represent` |
| `/verify` | `img1`, `img2` | `DeepFace.verify` |
| `/analyze` | `img` | `DeepFace.analyze` |
| `/register` | `img` plus DB config | `DeepFace.register` |
| `/search` | `img` plus DB config | `DeepFace.search` |
| `/build/index` | DB config | `DeepFace.build_index` |

If `DEEPFACE_AUTH_TOKEN` is set, include `Authorization: Bearer <token>`.
