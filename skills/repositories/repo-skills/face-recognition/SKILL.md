---
name: face-recognition
description: "Use face_recognition to detect faces, extract landmarks and
  encodings, compare identities, run the face_recognition and face_detection
  CLIs, and troubleshoot dlib/model installation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Face Recognition Repo Skill

## Purpose

Use this skill when the task involves the `face_recognition` Python package or
its installed console tools:

- detecting faces in photos or image folders;
- extracting face landmarks or 128-dimensional encodings;
- comparing known and unknown faces with distances or tolerance thresholds;
- running the `face_recognition` or `face_detection` command-line tools;
- adapting the repository's image, webcam/video, KNN/SVM, Flask, Raspberry Pi,
  Docker, or CUDA guidance without depending on the original checkout;
- debugging `dlib`, `face_recognition_models`, model-file, CLI, optional
  dependency, or headless-display failures.

Read [repo provenance](references/repo-provenance.md) before relying on
version-sensitive facts or refreshing this skill for a newer checkout.

## Install and quick checks

For normal package use, install the public distribution and verify imports:

```bash
python -m pip install face_recognition
python - <<'PY'
import face_recognition
print(face_recognition.__version__)
PY
```

For editable repository development, install the checkout with its package
metadata (`python -m pip install -e .`) and match a Python version supported by
the current repo/tests when practical. The core runtime dependencies are
`dlib`, `face_recognition_models`, `numpy`, `Pillow`, and `Click`.

Run [scripts/check_install.py](scripts/check_install.py) when installation,
model loading, or console scripts are uncertain:

```bash
python scripts/check_install.py
```

If imports fail, or if `face_recognition_models` warns about `pkg_resources`,
read [troubleshooting](references/troubleshooting.md) before changing package
versions.

## Route by task

| If the user needs to... | Read or run |
| --- | --- |
| Use Python functions (`load_image_file`, `face_locations`, `face_landmarks`, `face_encodings`, `compare_faces`, `face_distance`, `batch_face_locations`) | [API reference](references/api-reference.md) and [workflows](references/workflows.md) |
| Try a safe headless API demo on user-provided images | [scripts/showcase_api.py](scripts/showcase_api.py) |
| Recognize identities or detect face boxes from the shell | [CLI reference](references/cli-reference.md) |
| Adapt optional image, video/webcam, KNN/SVM, Flask, Raspberry Pi, or batch/CNN patterns | [workflows](references/workflows.md) |
| Package or deploy an app using Docker, CUDA, cloud hosts, or PyInstaller | [deployment notes](references/deployment.md) |
| Diagnose install/import/runtime problems | [troubleshooting](references/troubleshooting.md) and then `scripts/check_install.py` |
| Decide whether this skill is stale for a checkout | [repo provenance](references/repo-provenance.md) |

## Operating rules

- Do not assume the original repository's `examples/`, `docs/`, `tests/`, or
  image fixtures exist. Use user-provided images or the bundled scripts and
  references in this skill.
- Always guard calls like `face_recognition.face_encodings(image)[0]`; no face
  means an empty list, not a usable encoding.
- Treat coordinates as `(top, right, bottom, left)`. Crop with
  `image[top:bottom, left:right]`.
- The default face detector is CPU-friendly HOG. The CNN detector and
  `batch_face_locations` are useful for accuracy/batch workflows, but CUDA is
  only an optional acceleration path, not a requirement for the core API.
- Use `face_distance` or CLI `--show-distance` to tune tolerance; lower
  tolerance is stricter and can reduce false positives at the cost of more
  false negatives.
- For known-person folders, the CLI uses the image file basename as the label
  and expects one usable face per known image.
- Optional examples that need OpenCV, Flask, scikit-learn, scipy, Raspberry Pi
  camera hardware, GUI display, network streams, or Docker should stay optional
  unless the user explicitly asks for that workflow.
- Face recognition has fairness, age, privacy, consent, and legal constraints.
  The repository documents poorer performance on children and variation across
  demographic groups; surface these caveats in user-facing applications.

## Evidence-backed helper scripts

- [scripts/check_install.py](scripts/check_install.py) checks importability,
  installed versions, core API smoke behavior, and CLI help availability.
- [scripts/showcase_api.py](scripts/showcase_api.py) is a headless adaptation of
  the image detection, landmark, distance, comparison, and batch example
  patterns. It accepts image paths supplied by the user and never reads the
  original repository examples.
