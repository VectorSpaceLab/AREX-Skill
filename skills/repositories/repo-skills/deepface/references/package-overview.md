# DeepFace Package Overview

Read this when you need the repo-wide mental model before choosing a sub-skill.

## Public Facade

The public import is `from deepface import DeepFace`.

| Function | Primary owner | Purpose |
|---|---|---|
| `DeepFace.verify` | `recognition-workflows` | Compare two face inputs or two precomputed embeddings. |
| `DeepFace.represent` | `recognition-workflows` | Produce face embeddings and optional encrypted embeddings. |
| `DeepFace.find` | `recognition-workflows` | Search a local folder of images using a pickle-backed datastore. |
| `DeepFace.extract_faces` | `detection-and-demography` | Detect, align, crop, and normalize faces. |
| `DeepFace.analyze` | `detection-and-demography` | Estimate age, gender, race, and emotion. |
| `DeepFace.register`, `DeepFace.search`, `DeepFace.build_index` | `datastore-search` | Store/query embeddings in configured database backends. |
| `DeepFace.stream` | `api-service` | Run webcam/video recognition and demographic overlays. |
| `DeepFace.build_model` | `model-and-backend-selection` | Build and cache a recognition, detector, demography, or spoofing model. |

DeepFace also installs a Python Fire console script named `deepface`. For reliable automation, prefer explicit Python snippets or the REST API unless the user specifically asks for CLI usage.

## Architecture Map

- **Facade**: `DeepFace` normalizes public function arguments and delegates to modules.
- **Model management**: model inventory and singleton-style cache load recognition, detector, demography, and spoofing models.
- **Analysis engine**: detection, preprocessing, representation, verification, recognition, demography, normalization, and encryption modules implement the core workflows.
- **External integrations**: Flask routes and streaming functions expose the same workflows over HTTP or video frames.
- **Persistence**: local folder search stores pickle datastores; database search stores embeddings in SQL, document, graph, vector, or hosted vector services.

## Inputs And Outputs Shared Across Workflows

DeepFace commonly accepts image paths, URLs, base64 data URIs, NumPy arrays, file-like binary objects, and batched lists. Recognition verification also accepts flat lists of precomputed floats as embeddings.

Most image-loading paths use OpenCV-style BGR arrays internally. Some extracted face outputs can be returned as RGB, BGR, or gray depending on `color_face`.

## Backend And Dependency Model

The base package includes the default CPU-friendly path, TensorFlow/Keras dependencies, OpenCV, Flask, MTCNN, RetinaFace, LightPHE, LightDSA, and common utilities. Optional detectors, recognizers, database clients, GPU runtimes, and services are separate decisions; route them to `sub-skills/model-and-backend-selection/` or `sub-skills/datastore-search/`.

DeepFace may download model weights on first model build. Keep that side effect explicit and avoid triggering it during offline or static checks.
