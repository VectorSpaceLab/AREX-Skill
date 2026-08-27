# Troubleshooting

Use this file when a data, media, vision, or ML project fails during static review or a safe runtime check.

## Triage order

1. Confirm the current working directory and the target project path.
2. Read the local README, requirements, and notebook cells without running the project.
3. Run scripts/check_heavy_project_requirements.py and note the hazards it reports.
4. Decide whether the task is local conversion, network scraping, camera/audio work, notebook analysis, or model training.
5. If the request is really about deployment or service hosting, hand it to web-network-and-automation.

## Symptom table

| Symptom | Likely cause | First check | Safe fix | When to stop and hand off |
| --- | --- | --- | --- | --- |
| Scraper returns empty data, 403, 429, or SSL errors | Site layout drift, anti-bot throttling, login/consent gates, or missing headers | Re-read the current HTML or a saved fixture; confirm the target URL still exists | Use a cached page or a tiny fixture and update selectors carefully | If live scraping is the core work, keep it here; if it needs auth/session management, move to web-network-and-automation |
| CSV, PDF, or image paths fail | Wrong cwd, spaces, missing files, Unicode path issues, or corrupt input | Resolve the path with Path.resolve() and check exists() before touching it | Copy the input to a safe sample folder and avoid in-place overwrites | If the task is about robust file automation rather than media conversion, hand off appropriately |
| PyPDF2, Pillow, img2pdf, or easygui errors | Bad file bytes, unsupported format, or GUI dialogs in a headless session | Verify the input file type and check whether the environment has a display | Use local copies and avoid GUI prompts in CI or headless shells | Stop if the project is actually a general desktop UI rather than a media utility |
| Audio playback or recording fails | Missing ffmpeg, missing PyAudio/portaudio, no microphone, no speaker, or blocked network lookup | Confirm codec binaries and audio device permissions | Keep the task text-only until a live audio test is explicitly requested | If the user wants a speech app wrapper or deployment, route to web-network-and-automation |
| OpenCV camera or display fails | No webcam, permission issue, headless host, or missing sample video | Check whether VideoCapture(0) is really required and whether cv2.imshow is used | Use a saved image or video fixture and document the quit key | If it is a general desktop GUI app without media focus, use games-gui-and-desktop instead |
| YOLO, torch, or TensorFlow model work fails | Missing weights, blocked download, CUDA mismatch, old pin, or incompatible Keras version | Inspect the requirements file for TensorFlow/Keras pins and the source for .pt/.h5 model names | Use an isolated environment and avoid auto-downloading weights unless asked | If the request is to expose the model through a web app, hand it off to web-network-and-automation |
| Notebook output changes every run | Hidden state, out-of-order execution, or kernel mismatch | Inspect the code cells and kernel metadata before executing anything | Restart the kernel and run cells in order only after the notebook is understood | If the notebook is really a service launcher, hand off to web-network-and-automation |
| xls_to_xlsx fails | Windows COM or Excel is missing, locked, or unsupported on the host | Check for win32com imports and Excel availability | Skip execution on non-Windows hosts and document the limitation | This is a hard platform boundary; do not force a non-Windows run |
| TensorFlow import or training breaks | Conflicting TensorFlow/Keras pins, old CUDA packages, or mixed notebook environments | Compare the requirements file to the imported packages and version pins | Create a fresh environment and avoid mixing old TF 2.1-era pins with modern Keras | If the task is about serving the model, route to web-network-and-automation |

## Specific failure notes

- Network scraping: keep headers, delays, and selector changes isolated. Never assume the first HTML structure is still valid.
- Malformed media: re-encode or copy the input to a clean test folder before retrying. Do not overwrite the source asset.
- Camera and microphone: use sample files or text fallbacks unless the user explicitly requests live hardware behavior.
- GPU or model downloads: treat them as optional. If a project silently downloads weights, report that in the risk note.
- Notebook work: avoid running hidden cells or cached outputs as evidence of correctness.
- Windows COM: close open Excel workbooks, verify the local Excel install, and do not attempt it on Linux or macOS.

## Escalation clues

- The folder wants a Flask or FastAPI host around the model or scraper.
- The main issue is credential storage, session management, or outgoing mail rather than the data/media transformation itself.
- The task depends on hardware that is missing from the current machine and cannot be substituted with a fixture.
