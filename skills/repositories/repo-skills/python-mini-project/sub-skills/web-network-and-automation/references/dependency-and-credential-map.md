# Dependency and Credential Map — Web, Network, and Automation

This map classifies the service and automation folders by dependency, port, credential, network, and host-side-effect requirements. Treat every row as optional/unverified unless a future task explicitly prepares the needed environment and accounts.

## Project dependency and safety matrix

| Project | Main files | Dependency clues | Ports or endpoints | Credentials and configuration | Generated files or host side effects | Safety class | Verification stance |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `Crud_in_flask` | `main.py`, `create_db.py`, `database.sql` | Flask, sqlite3 | Flask dev server default `127.0.0.1:5000` unless overridden | `SECRET_KEY` is a placeholder; no external credentials | `create_db.py` writes `database.db` in cwd | Local service with DB writes | Static plus optional temp-copy DB/app smoke |
| `Firebase_Authentication_Using_Flask` | `main.py`, `db.py`, `run.py`, `start_server.sh` | Flask, `firebase==3.0.1`, `python-jwt`, `gcloud`, `requests-toolbelt`, pinned Werkzeug | Flask default `5000`; Firebase remote APIs during auth flows | `FIREBASE_APIKEY`, `FIREBASE_AUTHDOMAIN`, `FIREBASE_DATABASEURL`, `FIREBASE_PROJECT_ID`, `FIREBASE_STORAGE_BUCKET`, `FIREBASE_MESSAGING_SENDER_ID`, `FIREBASE_APP_ID`, optional `FIREBASE_MEASUREMENT_ID` | User creation/login against Firebase test project; session cookies | Credentialed external service | Static by default; mock or disposable Firebase for route tests |
| `RSS_Manager` | `pyproject.toml`, `main.py`, `utils.py`, templates | Python `>=3.11`; `fastapi[all]`, `uvicorn[standard]`, `sqlalchemy`, `jinja2`, `python-multipart`, `feedparser` | Uvicorn default `127.0.0.1:8000`; RSS feed URLs supplied by users | No secret by default; user-provided feed URLs | `utils.py` creates `subscriptions.db`; feed parsing may fetch network data | Local web service plus network feed client | Static by default; optional import in temp copy; mock/local RSS fixture for network behavior |
| `Simple_Http_Server` | `mhttp.py` | stdlib `socket`, `pathlib` | Host `0.0.0.0`, port `1997` in source | None | Binds a listening socket; serves files from chosen folder | Network-exposing local server | Static only by default; optional supervised loopback subprocess after changing host/port |
| `Socket_example` | `server.py`, `client.py` | stdlib `socket` | `localhost:3000` | None | Server accept loop; client sends one message | Local socket demo | Static by default; optional subprocess integration with timeout |
| `Todo_App` | `main.py` | Flask, Flask-Bootstrap | Flask default `5000` | None | In-memory todo state; dev server starts at import | Local service with top-level server side effect | Static only unless run as supervised script |
| `Url_Shortener` | `url_shortner.py` | `requests`; `json` is stdlib despite requirements listing | Bitly endpoint `https://api-ssl.bitly.com/v4/shorten` | Bitly bearer token; placeholder `api_key = 'You api key here'` | Sends the submitted URL to Bitly | Credentialed external API client | Static plus mocked `requests.post`; no live API by default |
| `website-builder` | `run.py`, `app/__init__.py`, `app/routes/portfolio_routes.py` | Flask, Flask-WTF, Jinja2; requirements include many heavy ML/audio/cloud packages not needed for basic Flask routes | Flask default `5000` | Missing `config.py` is expected to define `DevelopmentConfig` and `ProductionConfig`; AI provider credentials may be needed if unfinished AI features are implemented | Starts Flask app after config exists | Incomplete local web app | Static only until missing config is supplied or mocked |
| `Automated_Mailing` | `mail.py` | pandas, smtplib/email stdlib; requirements file includes stdlib names and unusual encoding | Gmail SMTP `smtp.gmail.com:587` | Sender address, account email, password/app password, recipient CSV path and column names | Sends real email to every CSV row | Credentialed bulk-send automation | Static only; mock SMTP/pandas for tests |
| `Mail_Checker` | `mail_checker.py` | imaplib stdlib; requirements lists stdlib name | Gmail IMAP SSL `imap.gmail.com` | Gmail address/password or app password; mail sender filters | Logs in and reads inbox subjects at import | Credentialed inbox access | Static only; mock IMAP for tests |
| `Whatsapp_Bot` | `main.py` | `pywhatkit`, datetime | WhatsApp Web/browser; scheduled/instant send functions | Phone number or group id, message, browser login session | Sends WhatsApp messages; opens/controls browser | Credentialed messaging automation | Static only; mock pywhatkit for tests |
| `desktopassistant` | `index.py` | pyttsx3, speech_recognition, wikipedia, webbrowser, pyautogui, pywhatkit, spotipy | Wikipedia/Google/YouTube/StackOverflow/LeetCode, Spotify OAuth, browser | Microphone permission, browser session, optional Spotify OAuth client credentials | Speaks audio, listens to mic, opens websites, may open Windows VS Code path | Interactive desktop/network automation | Static only unless on a prepared desktop workstation |
| `Port Scanner` | `scan_port.py` | stdlib socket | Broad port list including SSH/HTTP/DB/RDP ranges | Explicit authorization for target host | Connect attempts against selected host | Intrusive network scanner | Static only; never scan third-party hosts in verification |
| `PostgreSQL_Dumper` | `script.py` | `pexpect`, system `pg_dump` | PostgreSQL host/port, default commonly `5432` | DB host, port, user, name, password | Writes SQL dump `<db>_<date>.sql` in cwd; pexpect terminal interaction | Credentialed database export | Static plus mocked pexpect; real dump only on disposable DB |
| `Windows_Shutdown` | `shutdown.py` | stdlib `os` | None | Windows admin privileges | Calls OS shutdown immediately | Destructive host operation | Static only; never execute |
| `spam_bot` | `bot1.py`, `bot2.py` | pyautogui, keyboard, time | Focused GUI application | User-provided spam text; active keyboard/focus context | Types and presses Enter repeatedly | Spam/destructive GUI automation | Static only; mock GUI libraries for tests |
| `IP_Locator` | `main.py`, `LocateIP.py` | requests, pyfiglet, subprocess/os/re/json | `http://ip-api.com/json/...`; `nslookup` command | Target IP/domain; no API key in source | Changes cwd to Windows Desktop path and writes `ip_data.json`/`ip_data.txt`; clears terminal | External API/subprocess/file-writing utility | Static only; mock requests/subprocess and redirect output path before use |

## Credential handling checklist

| Credential or secret | Projects | Preferred storage | Red flags |
| --- | --- | --- | --- |
| Firebase web config | `Firebase_Authentication_Using_Flask` | Environment variables loaded from a local `.env` excluded from commits | Missing `FIREBASE_*`; production Firebase project; logging returned user tokens |
| Bitly token | `Url_Shortener` | `BITLY_TOKEN` environment variable or secret manager; patch placeholder before use | Hard-coded `api_key`; testing against real Bitly without consent |
| SMTP account/password | `Automated_Mailing` | Test SMTP server or disposable account app password | Ordinary Gmail password; broad recipient CSV; no dry-run; secrets in code/logs |
| IMAP account/password | `Mail_Checker` | Disposable inbox app password or mocked IMAP server | README-era less-secure-app guidance; top-level login at import |
| WhatsApp session/recipient | `Whatsapp_Bot`, `desktopassistant` | Logged-in browser session on a disposable workstation and explicit recipient consent | Sending to real contacts/groups during tests; screen/browser focus assumptions |
| Spotify OAuth | `desktopassistant` | Environment variables or local credentials file excluded from commits | Missing redirect URI/client secret; accidental production account control |
| PostgreSQL credentials | `PostgreSQL_Dumper` | Environment variables, `.pgpass`, or injected test credentials | Dumping production DB; SQL dump left in workspace; password visible in logs |
| Network scan target | `Port Scanner` | Written authorization in the task, ideally loopback or owned lab host | Third-party domain/IP; broad scan without scope |

## Port and binding map

| Port or binding | Projects | Meaning | Safe adjustment |
| --- | --- | --- | --- |
| Flask default `5000` | `Crud_in_flask`, `Firebase_Authentication_Using_Flask`, `Todo_App`, `website-builder` | Default Flask development server port when not specified | Use `--host 127.0.0.1 --port <free-port>` or equivalent when starting intentionally. |
| Uvicorn default `8000` | `RSS_Manager` | Default FastAPI dev server port | Use `uvicorn main:app --host 127.0.0.1 --port <free-port>`. |
| `0.0.0.0:1997` | `Simple_Http_Server` | Source binds all interfaces on port 1997 | Prefer patching to `127.0.0.1` and a temporary free port for tests. |
| `localhost:3000` | `Socket_example` | Server/client demo pair | Check for conflicts with existing dev servers; use timeout supervision. |
| SMTP `smtp.gmail.com:587` | `Automated_Mailing` | TLS SMTP send endpoint | Prefer a local fake SMTP server for tests. |
| IMAP `imap.gmail.com:993` | `Mail_Checker` | Gmail IMAP SSL endpoint | Mock for tests; use app password only for explicit real access. |
| PostgreSQL `5432` common default | `PostgreSQL_Dumper` | User-supplied DB port in dumper function | Use a disposable DB and output directory. |

## Requirement file hazards

| Evidence | Hazard | Recommended action |
| --- | --- | --- |
| Root `requirements.txt` | Legacy aggregate, not a clean universal lockfile for all projects. | Do not install it for this sub-skill; install only the selected project needs. |
| `Automated_Mailing/requirements.txt` | Contains stdlib packages and appears encoded with null bytes. | Install `pandas` only when needed; `os`, `smtplib`, and `email` are stdlib. |
| `Mail_Checker/requirements.txt` | Lists `imaplib`, which is stdlib. | No pip install needed for `imaplib`; credentialed access remains the blocker. |
| `Url_Shortener/requirements.txt` | Lists `json`, which is stdlib. | Install `requests`; never pip-install `json`. |
| `website-builder/requirements.txt` | Very broad pinned stack with ML/audio/cloud packages for a small Flask skeleton. | Start with minimal Flask/Jinja/Flask-WTF unless a task needs the unfinished AI stack. |
| `RSS_Manager/pyproject.toml` | Declares package metadata that does not make the repo root a package; app still runs from project cwd. | Treat as a project-local FastAPI dependency declaration, not a root install recipe. |
