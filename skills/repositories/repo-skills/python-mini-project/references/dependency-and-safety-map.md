# Dependency and safety map

The repository is a collection of independent mini-projects. Do not install every dependency in the checkout just because a task names this repo. Pick the target folder, read its local dependency clues, and install only the packages needed for that folder and verification goal.

## Root dependency rule

- The root `requirements.txt` is UTF-16LE and includes explanatory `Use command ...` lines. Treat it as a historical dependency note, not a clean lockfile for all projects.
- Prefer a project-local `requirements.txt` or `pyproject.toml` when it exists.
- If a folder has no dependency file, inspect imports statically before installing anything.
- Avoid broad installs for optional GUI, model, scraping, database, or automation dependencies unless the user explicitly narrowed the task to that project family.

## Minimum mandatory backend

| Scope | Required backend | Minimum environment | Why |
| --- | --- | --- | --- |
| Repository catalog, contribution guidance, static checks, safe stdlib smoke checks | CPU/any Python | Python 3.10+ with stdlib; `pip` only when installing a target project's own deps | The repo root is not an installable package and mandatory verification uses static inspection plus tiny stdlib-backed checks. |

## Optional dependency families

| Family | Typical packages/imports | Projects | Run only when... | Default verification |
| --- | --- | --- | --- | --- |
| GUI/display | `tkinter`, `customtkinter`, `turtle`, `pygame`, `curses` | GUI/game folders, calculators, flashcards, Othello/Chess/Snake, Tk utilities | A display or terminal UI session is available and the task is about live UI behavior | Static import/asset/requirements inspection. |
| Audio/speech/desktop | `pygame`, `python-vlc`, `pyttsx3`, `speech_recognition`, `pyaudio`, `pyautogui`, `keyboard`, `spotipy` | `Music-Player`, speech/assistant/bot projects, Exercise Timer | The host has speakers/microphone/desktop permissions or mocks | Static inspection and mocked calls. |
| Web/service | `Flask`, `FastAPI`, `uvicorn`, `sqlalchemy`, `feedparser`, `firebase` | Flask/FastAPI CRUD, RSS, URL shortener, website builder, Firebase auth | A disposable port/database/service config is selected | Import/help checks, not live public service calls. |
| Network/scraping/API | `requests`, `beautifulsoup4`, `bs4`, `pandas`, `forex_python`, `googletrans` | scrapers, IP locator, currency/translation tools | The user allows network and target site/API terms are acceptable | Cached fixture or static selector check by default. |
| Documents/images/media | `Pillow`, `PyPDF2`, `img2pdf`, `qrcode`, `pyqrcode`, `pypng`, `moviepy`, `pytube`, `easygui` | PDF/image/QR/audio/video projects | Input fixtures are local copies and GUI dialogs are avoided or available | Static path/type checks; tiny local fixtures when authorized. |
| CV/camera/model | `opencv-python`, `mediapipe`, `ultralytics`, `torch`, `tensorflow`, `keras`, `numpy`, `matplotlib` | object detection, digit recognizers, face/shape/lane/motion demos | Camera/model files/packages are prepared; GPU only if required by the specific task | Static requirement/backend summary; no model/camera run by default. |
| OS-specific automation | `pywin32`, shell commands, shutdown commands, `pexpect` | `xls_to_xlsx`, `Windows_Shutdown`, `PostgreSQL_Dumper` | The OS and external command target are disposable/authorized | Static only by default. |

## Safety classes used by this skill

| Class | Meaning | Examples |
| --- | --- | --- |
| `safe-runnable` | Deterministic, local, short, no credentials/network/display/destructive side effects. | Curated `Cat_command` and `Execute Shell Command` checks. |
| `help-or-static` | Safe for argparse/help, syntax parse, or static AST inspection only. | Most CLI utilities, service startup scripts, GUI checkers. |
| `requires-display` | Needs GUI display, pygame/turtle/Tk/curses, or audio session. | Chess, Snake, Color Game, Tk calculators. |
| `requires-network` | Performs HTTP/API/scraping/translation/download calls. | scrapers, URL shortener, Google Translate, IP locator. |
| `requires-credentials` | Needs tokens, logged-in browser, email account, Firebase/Spotify/WhatsApp credentials. | Firebase auth, SMTP/IMAP, WhatsApp bot, desktop assistant. |
| `requires-heavy-backend` | Needs ML/CV packages, model downloads, camera, GPU, or old TensorFlow stack. | Object Detection, digit recognizers, Motion Detection. |
| `unsafe-destructive` | Can spam, scan unauthorized hosts, dump databases, or shut down the host. | spam bot, port scanner, PostgreSQL dumper, Windows shutdown. |

## Project-specific caution highlights

- `Smart_Calculator/calculator.py` opens a Tk root and mainloop at import time; do not run its unit test in a headless smoke path.
- `Execute Shell Command` uses `subprocess.Popen(..., shell=True)`; only the curated `echo` test is considered safe.
- `Simple_Http_Server/mhttp.py` binds to `0.0.0.0:1997` and loops forever; use static checks or isolate the port before live tests.
- `Object_Detection` uses Ultralytics/PyTorch/OpenCV and may touch webcam/model downloads; no CPU-only import proves webcam detection.
- `digit-recognizer` pins an old TensorFlow/Keras stack and includes Flask app code; prepare a dedicated environment before live use.
- `xls_to_xlsx` depends on Windows COM (`pywin32`); Linux/macOS static inspection is not live validation.
- `Windows_Shutdown` is intentionally never run as a smoke test.
