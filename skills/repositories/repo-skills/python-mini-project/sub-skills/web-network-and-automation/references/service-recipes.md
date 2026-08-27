# Service Recipes — Web, Network, and Automation

Use these recipes after the static checker has classified the target folder. Commands are examples for a future checkout; run them only after dependency and credential requirements have been reviewed.

## General service rules

| Rule | Why it matters | Safe practice |
| --- | --- | --- |
| Use the project folder as cwd | Templates, SQLite files, `.env`, and relative imports are usually cwd-relative. | `cd <repo>/<folder>` before Flask/FastAPI/socket runs. |
| Install per project | The repository root is a gallery of independent projects, not one package. | Create a small disposable env for the selected folder; avoid installing root requirements. |
| Prefer static checks first | Several scripts start servers, log in to accounts, send messages, or shut down the host at import time. | Run `scripts/check_service_project.py` before executing any project code. |
| Bind locally for development | Some examples bind `0.0.0.0` or scan remote hosts. | Use loopback (`127.0.0.1` or `localhost`) and a non-conflicting port unless the task explicitly requires exposure. |
| Time-box long-running services | Socket servers and web dev servers do not exit by themselves. | Use an explicit terminal, timeout wrapper, or subprocess supervision when testing. |
| Keep credentials out of source | Firebase, Bitly, SMTP, IMAP, WhatsApp, Spotify, and PostgreSQL examples need secrets or logged-in sessions. | Use environment variables, `.env` kept out of commits, disposable accounts, and redacted logs. |

## Flask web apps

| Project | Shape | Local operation recipe | Safe verification approach | Notes and hazards |
| --- | --- | --- | --- | --- |
| `Crud_in_flask` | Flask app in `main.py`, SQLite helper `create_db.py`, templates/static files. | From `Crud_in_flask`: install Flask, run `python create_db.py` to create `database.db`, then run with Flask using app module `main:app` or equivalent. | Static parse; optionally create DB in a temporary copy, then import or route-test with Flask's test client if Flask is installed. | `main.py` has no `app.run`; wrong cwd causes missing `database.sql`, missing `database.db`, or template errors. Uses placeholder secret key. |
| `Todo_App` | Single-file Flask app with `flask_bootstrap` and in-memory list. | From `Todo_App`: install Flask and Flask-Bootstrap, then run the script only when intentionally starting the dev server. | Static only by default; if testing, run as a subprocess with timeout rather than importing it. | `app.run(debug=True)` is top-level, so importing `main.py` starts a server. State is not persistent. |
| `Firebase_Authentication_Using_Flask` | Flask app split across `main.py`, `db.py`, and `run.py`; Firebase config from env. | From the folder: install listed requirements, set `FIREBASE_*` environment variables from a test Firebase project, then run `python run.py`. | Static parse and environment-variable presence check; route tests need Firebase mocked or a disposable Firebase project. | `main.py` imports `auth` from `db.py`; missing env values can produce Firebase initialization or login errors. Do not use production Firebase credentials. |
| `website-builder` | Flask factory in `app/__init__.py`, blueprint in `app/routes/portfolio_routes.py`, launcher `run.py`. | From `website-builder`: install a minimal Flask/Jinja stack first; provide the missing `config.py` with `DevelopmentConfig` and `ProductionConfig` before running. | Static parse; factory import only after adding/mocking `config.py`. | The requirements file is broad and heavyweight for this small app. `app/__init__.py` imports `config` that is not present in the checkout, so the app is incomplete as-is. |

## FastAPI RSS app

| Project | Shape | Local operation recipe | Safe verification approach | Notes and hazards |
| --- | --- | --- | --- | --- |
| `RSS_Manager` | FastAPI app in `main.py`; SQLite and feed parsing in `utils.py`; templates folder; `pyproject.toml` declares `fastapi[all]`, `uvicorn[standard]`, `sqlalchemy`, `jinja2`, `python-multipart`, and `feedparser`; Python `>=3.11`. | From `RSS_Manager`: install the pyproject dependencies in a disposable env, then run `uvicorn main:app --host 127.0.0.1 --port 8000` for local development. | Static parse by default. Optional import smoke may create `subscriptions.db`; use a temporary project copy or temp cwd. Network behavior should be tested with a local/mock RSS fixture, not a live feed. | `Jinja2Templates(directory="templates")` and SQLite URL are cwd-relative. `utils.py` creates SQLite tables at import. `Feed` calls `feedparser.parse(url)`, so add/list article flows can call the network. |

## Socket and local HTTP services

| Project | Shape | Local operation recipe | Safe verification approach | Notes and hazards |
| --- | --- | --- | --- | --- |
| `Simple_Http_Server` | Raw socket HTTP server in `mhttp.py`; default host `0.0.0.0`, port `1997`; optional served folder argument. | Use only with an explicit temporary content folder. Prefer changing host to loopback or using firewall isolation before exposure. | Static only by default; optional subprocess test should bind a disposable port after patching/configuring port and must terminate the process. | The script binds and enters an accept loop at top level. It may expose files from the chosen folder. |
| `Socket_example` | `server.py` binds `localhost:3000`; `client.py` connects to the same port. | Start server in one controlled process, then run client in another, and terminate server. | Static by default; optional integration test can use subprocesses and a timeout. | Server has an infinite accept loop; port `3000` may conflict with local dev services. |

## HTTP/API client utilities

| Project | Shape | Local operation recipe | Safe verification approach | Notes and hazards |
| --- | --- | --- | --- | --- |
| `Url_Shortener` | CLI prompt, Bitly API POST through `requests`, hard-coded placeholder token. | Refactor or patch to read `BITLY_TOKEN` from environment before real use; run only against a disposable URL/token. | Static parse and credential placeholder detection; mock `requests.post` for tests. | `requirements.txt` lists stdlib `json`; do not treat it as pip-installable. Real runs send data to Bitly. |
| `IP_Locator` | Interactive menu, `requests` to `ip-api.com`, `nslookup` subprocess, local file writes. | Prefer refactoring into callable functions with output path and dry-run controls before use. | Static only by default; mock API and subprocess in tests. | `main.py` starts the menu at import. `LocateIP.py` changes cwd to a Windows Desktop path before writing files. `nslookup` and external API calls are network-dependent. |
| `Port Scanner` | CLI prompt and socket connection attempts over a broad list of ports. | Run only with explicit written authorization for the target host/range. | Static only by default. | Port scanning can violate policy or law; do not scan third-party hosts during routine verification. |

## Email, messaging, and desktop automation

| Project | Shape | Local operation recipe | Safe verification approach | Notes and hazards |
| --- | --- | --- | --- | --- |
| `Automated_Mailing` | Reads recipient CSV, logs in to SMTP, sends one email per row. | Use a test SMTP account/server, a tiny fixture CSV, and a dry-run/mock SMTP path before real sends. | Static parse; unit-test by mocking `smtplib.SMTP` and `pandas.read_csv`. | Top-level code sends mail. Gmail password flows usually require app passwords or OAuth, not ordinary account passwords. |
| `Mail_Checker` | Top-level Gmail IMAP SSL login and subject extraction. | Use a disposable inbox and app password only if real access is explicitly required. | Static parse; mock `imaplib.IMAP4_SSL` for tests. | Top-level login occurs at import. README references old less-secure-app access, which modern Gmail accounts usually do not support. |
| `Whatsapp_Bot` | Prompts for phone/message/time and uses `pywhatkit` to send WhatsApp messages. | Use only with explicit recipient consent, a logged-in browser session, and disposable test contact/group. | Static parse; mock `pywhatkit` functions for tests. | Script can send both scheduled and instant messages; browser/WhatsApp Web state affects results. |
| `desktopassistant` | Voice assistant using microphone, TTS, Wikipedia, browser opening, pyautogui/pywhatkit, Spotify OAuth, and Windows-specific paths. | Treat as interactive desktop automation. Run only on a workstation with audio/mic/browser permissions and non-production accounts. | Static parse by default; unit-test individual functions with mocks after refactoring. | `pyttsx3.init('sapi5')` and `os.startfile` are Windows-specific. The `open google` branch is written so it can trigger unexpectedly. |
| `spam_bot` | GUI automation that types and presses Enter repeatedly. | Do not run on shared hosts or real chat windows. If testing is required, mock `pyautogui`/keyboard or use an isolated text field. | Static parse only. | Designed to spam; can send unwanted messages or modify focused applications. |

## Database and host/system automation

| Project | Shape | Local operation recipe | Safe verification approach | Notes and hazards |
| --- | --- | --- | --- | --- |
| `PostgreSQL_Dumper` | `pexpect` wrapper around `pg_dump`, writes `<db>_<YYYYMMDD>.sql` in cwd. | Use only against a disposable PostgreSQL database with explicit host/user/db/password and `pg_dump` installed. | Static parse; optional test can mock `pexpect.spawn`. | Stores a SQL dump in cwd; wrong credentials or non-terminal environments can fail with pexpect/termios errors. |
| `Windows_Shutdown` | Calls `os.system("shutdown /s /t 0")` and invokes it at import. | Never run during routine work. Review or refactor only. | Static parse only. | Destructive host operation; Windows/admin-specific; importing the module attempts shutdown. |
