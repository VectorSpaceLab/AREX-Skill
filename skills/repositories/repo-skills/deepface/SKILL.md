---
name: deepface
description: "Use DeepFace for face recognition, verification, embeddings, face
  detection, demographic analysis, datastore search, API serving, model
  selection, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DeepFace Repo Skill

Use this skill when a task names `deepface`, `DeepFace`, face verification, facial recognition, face embeddings, face detection, facial attribute analysis, anti-spoofing, DeepFace REST API routes, or DeepFace datastore/database search.

DeepFace is a Python face-recognition and facial-analysis package. It wraps recognition models, detector backends, demographic models, a folder-backed face datastore, database-backed register/search APIs, a Flask/Gunicorn service, and webcam/video streaming helpers.

## Quick Start

Install the public package for application work:

```bash
pip install deepface
python -c "from deepface import DeepFace; print('DeepFace import ok')"
```

If TensorFlow is new enough to use Keras 3 behavior and `from deepface import DeepFace` fails with `No module named 'tf_keras'`, install the compatibility package:

```bash
pip install tf-keras
```

Run the bundled diagnostic before deeper troubleshooting:

```bash
python scripts/check_deepface_environment.py --json
```

The diagnostic prints package versions, supported models/detectors, database backends, and import health. It does not build models, download weights, connect to databases, or require a GPU.

## Route By Task

- **Verification, embeddings, and local folder search**: use `sub-skills/recognition-workflows/SKILL.md` for `DeepFace.verify`, `DeepFace.represent`, `DeepFace.find`, distance metrics, thresholds, confidence, precomputed embeddings, batch representation, local folder datastores, and signed pickle handling.
- **Face extraction, detectors, demographics, and anti-spoofing**: use `sub-skills/detection-and-demography/SKILL.md` for `DeepFace.extract_faces`, `DeepFace.analyze`, detector backend choices, `enforce_detection`, `align`, `expand_percentage`, landmark outputs, age/gender/race/emotion actions, and anti-spoofing failure handling.
- **Database-backed register/search**: use `sub-skills/datastore-search/SKILL.md` for `DeepFace.register`, `DeepFace.search`, `DeepFace.build_index`, exact versus ANN search, Postgres/Mongo/vector database backends, connection details, and optional database client dependencies.
- **REST API and streaming**: use `sub-skills/api-service/SKILL.md` for the Flask/Gunicorn API, `/verify`, `/represent`, `/analyze`, `/register`, `/search`, `/build/index`, bearer auth, JSON/form/file uploads, Docker/service deployment, and `DeepFace.stream` webcam/video guidance.
- **Models, detectors, dependencies, and weights**: use `sub-skills/model-and-backend-selection/SKILL.md` for supported recognition/demography/spoofing/detector model names, optional detector packages, TensorFlow/Keras compatibility, model-weight downloads, CPU/GPU expectations, normalization, and encrypted embeddings.

## Shared References And Helpers

- `references/package-overview.md` summarizes the public API facade, architecture, and cross-skill concepts.
- `references/troubleshooting.md` covers install/import, TensorFlow/Keras, weight cache, input, optional dependency, API, and backend failures that cut across workflows.
- `references/repo-provenance.md` records the source revision, package version, and evidence paths used to create this skill.
- `references/repo-routing-metadata.json` contains structured routing metadata for managed repo-skill import; this creation run did not import the skill.
- `scripts/check_deepface_environment.py` verifies an installed DeepFace environment without model downloads or database connections.

## Common Decision Points

- Use the default `model_name="VGG-Face"`, `detector_backend="opencv"`, and `distance_metric="cosine"` for simple CPU examples unless the user names another model or detector.
- Set `enforce_detection=False` only when the user accepts full-image fallback behavior for hard or non-face inputs; otherwise treat `FaceNotDetected` as a data-quality signal.
- Do not recommend optional detectors such as Dlib, MediaPipe, YOLO, FastMTCNN, or Buffalo_L until the matching optional package is installed and the user accepts model-weight downloads.
- Use folder-backed `DeepFace.find` for local image directories; use database-backed `register/search/build_index` only when the user has a configured database service and optional client dependencies.
- Treat model weights, remote image URLs, and API requests as network operations. Ask before running them in constrained/offline environments.

## Safety And Self-Containment

This generated skill is self-contained. Runtime instructions, references, and helper scripts live inside this skill directory. Original repository files, tests, notebooks, and scripts were used only as evidence and are not runtime dependencies for future agents.
