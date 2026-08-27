# Troubleshooting — Web, Network, and Automation

Start with a static check, then use the section matching the failure. Do not solve these failures by broad-installing every repository dependency or by running unsafe scripts blindly.

## App module and cwd mistakes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Flask says it cannot import the app module. | Command run from the wrong folder, folder name has spaces, or app object/factory path is wrong. | `cd` into the project folder first. Use `main:app` for `Crud_in_flask` and `Firebase_Authentication_Using_Flask/main.py`; use `run.py` or `app:create_app` style only for `website-builder` after its missing config is supplied. |
| Template not found. | Templates are referenced relative to cwd. | Run from the project folder that contains `templates`; do not start from the repository root unless the command sets the template path explicitly. |
| SQLite file missing or wrong data appears. | SQLite paths are relative to cwd. | For `Crud_in_flask`, run `create_db.py` from `Crud_in_flask` or create the DB in a temp copy. For `RSS_Manager`, expect `subscriptions.db` in the `RSS_Manager` cwd. |
| Importing a module unexpectedly starts a server or blocks for input. | Top-level side effects in scripts. | Use AST/static checks first. Avoid importing `Todo_App/main.py`, `Simple_Http_Server/mhttp.py`, `Socket_example/server.py`, `Mail_Checker/mail_checker.py`, `Url_Shortener/url_shortner.py`, `IP_Locator/main.py`, `Windows_Shutdown/shutdown.py`, and spam bot modules unless they have been refactored or isolated. |
| `ModuleNotFoundError: config` in website builder. | `website-builder/app/__init__.py` imports `DevelopmentConfig` and `ProductionConfig` from `config.py`, but that file is absent. | Add a local `config.py` for the task or mock it in tests before importing the factory. Do not install heavy requirements as a substitute for the missing source file. |
| FastAPI RSS pages fail to render. | `Jinja2Templates(directory="templates")` is relative and templates are not found from the current cwd. | Run `uvicorn main:app` from `RSS_Manager`, or patch the template directory to an absolute/project-root-aware path for tests. |

## Port conflicts and accidental exposure

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Address already in use`. | Flask default `5000`, Uvicorn default `8000`, `Socket_example` `3000`, or `Simple_Http_Server` `1997` is already occupied. | Choose a free port and pass it to the server command when possible. For raw socket scripts, patch the constant in a temp copy before running. |
| Service is reachable from other machines unexpectedly. | Script binds `0.0.0.0`, especially `Simple_Http_Server`. | Bind to `127.0.0.1` for local tests and avoid serving sensitive folders. |
| Test hangs forever. | Dev server or socket accept loop is long-running. | Use a supervised subprocess, timeout, and cleanup. Do not run long-lived services as final verification unless the task explicitly needs runtime behavior. |
| Client cannot connect to socket server. | Server not started first, host mismatch, firewall, or wrong port. | Start the server first, confirm both sides use `localhost` and the same port, and terminate the server after the client exchange. |

## Database creation and persistence

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `no such table: products` in `Crud_in_flask`. | `database.db` was not created or was created in a different cwd. | Run `python create_db.py` from `Crud_in_flask`, or use a temp copy and verify `database.sql` is present. |
| RSS subscriptions disappear or appear in the wrong checkout. | `RSS_Manager` uses relative SQLite URL `sqlite:///subscriptions.db`. | Keep the cwd explicit and remove temporary DB files after tests. |
| PostgreSQL dump fails with `pg_dump` not found. | System PostgreSQL client tools are missing. | Install `pg_dump` in the environment or mock `pexpect.spawn`; do not use a production DB as a smoke test. |
| `termios.error` or pexpect interaction fails. | `PostgreSQL_Dumper` expects a terminal-like process. | Run from a real terminal for explicit manual dumps, or unit-test by mocking `pexpect.spawn` instead. |
| SQL dump contains sensitive data. | Real database was dumped into the workspace. | Use disposable DBs, store dumps outside tracked source, redact logs, and delete temporary dumps after validation. |

## Firebase, API keys, and external HTTP clients

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Firebase auth/login fails at startup or request time. | Missing `FIREBASE_*` environment variables, wrong Firebase project, or disabled email/password auth. | Use a test Firebase project, set every required env var, enable email/password auth, and do not log returned user tokens. |
| Firebase dependency conflict with Flask/Werkzeug. | The requirements pins are old/mixed. | Use a disposable env for this folder only. Avoid upgrading a shared env; pin or adjust in the project-local environment. |
| Bitly URL shortener returns authorization errors. | Placeholder API key or invalid token. | Patch the script to read a `BITLY_TOKEN` env var, then test with a disposable token or mock `requests.post`. |
| RSS feed add/list pages fail or hang. | Feed URL is unreachable, malformed, slow, or parsed at request time. | Use local/mock RSS fixtures for tests. Keep live RSS requests out of mandatory verification. |
| IP locator writes files in an unexpected place. | `LocateIP.py` changes cwd to a Windows Desktop path before writing. | Refactor output path before running; mock `requests` and `subprocess` for tests. |
| Network command fails on Linux/macOS/CI. | `cls`, Windows Desktop paths, or `nslookup` availability assumptions. | Replace OS-specific commands with portable helpers or classify the behavior as platform-specific. |

## SMTP, IMAP, and messaging automation

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Gmail SMTP login fails. | Ordinary passwords and less-secure-app access are not accepted by modern Gmail. | Use a disposable account with an app password or a local fake SMTP server. Prefer mocking `smtplib.SMTP` for tests. |
| Automated mailing sends to too many recipients. | `mail.py` loops over every row in the CSV at top level. | Never run against a real CSV during verification. Add dry-run controls or mock SMTP and use a tiny fixture. |
| IMAP login happens during import. | `Mail_Checker/mail_checker.py` creates `IMAP4_SSL` and logs in at top level. | Do not import it directly. Refactor behind a main guard or mock `imaplib.IMAP4_SSL`. |
| WhatsApp message not sent or browser opens unexpectedly. | `pywhatkit` depends on WhatsApp Web login, browser focus, timing, and recipient validity. | Mock `pywhatkit` for tests. Use only explicit, consented recipients in real runs. |
| Voice assistant cannot hear or speak. | Missing microphone/audio devices, speech-recognition backend, `sapi5` Windows-only TTS, or headless environment. | Treat as a desktop-workstation workflow, not a headless CI workflow. Mock speech/TTS/browser functions for automated tests. |
| Desktop assistant opens unwanted pages. | Conditional logic includes an `elif 'open google' or 'search on google' in query` pattern that is effectively always truthy when reached. | Fix the condition before runtime use; test command routing with mocks. |

## Sockets and scanners

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Socket server accepts only one client or prints raw bytes. | Beginner demo code with minimal protocol handling. | Keep tests simple: start server, send one message, assert response, then terminate. |
| Port scanner is blocked or flagged. | Network scanning triggers firewalls, IDS, or policy restrictions. | Do not scan outside loopback/owned lab hosts, and obtain explicit authorization before any scan. |
| False negatives in port scan. | One-second timeout, firewall drops, DNS mismatch, or target refuses connections. | Increase timeout only when authorized; prefer targeted owned hosts rather than broad scans. |

## Windows-only and destructive operations

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `os.startfile` missing. | `desktopassistant` path launch is Windows-only. | Guard with platform checks or use portable alternatives when needed. |
| Voice engine `sapi5` unavailable. | Windows SAPI engine requested on non-Windows systems. | Use platform-specific TTS configuration or skip audio behavior in headless/CI. |
| Shutdown script would power off the machine. | `Windows_Shutdown/shutdown.py` calls `shutdown /s /t 0` at top level. | Never execute or import it during routine work. Review statically or refactor behind a protected confirmation flag. |
| Spam bot controls the wrong window. | `pyautogui` types into whichever application has focus. | Never run against real chat/work applications. Use mocked GUI libraries or an isolated throwaway text field if manual demonstration is explicitly requested. |

## Static checker interpretation

| Finding | Meaning | Next step |
| --- | --- | --- |
| `top-level server startup` | Importing/running the file can bind a port or start a loop before tests can control it. | Use subprocess supervision or refactor behind `if __name__ == "__main__"`. |
| `credential need` | The file contains obvious passwords, tokens, API keys, auth headers, login calls, or environment variable requirements. | Create test credentials or mocks; never use production secrets. |
| `destructive host command` | The file calls shutdown/reboot/remove/delete-like system commands or host-specific launch APIs. | Static review only unless a human explicitly authorizes a controlled environment. |
| `network client` | The code uses requests, feedparser, urllib, sockets, SMTP/IMAP, pywhatkit, or subprocess network tools. | Mock by default; use local fixtures or loopback when runtime behavior is required. |
