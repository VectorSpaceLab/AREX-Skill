---
name: web-network-and-automation
description: "Operate python-mini-project web apps, network clients, sockets,
  credentialed bots, and host automation safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Web, Network, and Automation

Use this sub-skill when the task touches python-mini-project folders that behave like services, network clients, credentialed automation, bots, sockets, or host/system automation.

## Route here

- Flask/FastAPI web apps: `Crud_in_flask`, `Firebase_Authentication_Using_Flask`, `RSS_Manager`, `Todo_App`, `website-builder`.
- Local network services and sockets: `Simple_Http_Server`, `Socket_example`.
- HTTP/API clients and URL/IP tools: `Url_Shortener`, `IP_Locator`, `Port Scanner`.
- Email, messaging, bots, and desktop automation: `Automated_Mailing`, `Mail_Checker`, `Whatsapp_Bot`, `desktopassistant`, `spam_bot`.
- Database and host automation with side effects: `PostgreSQL_Dumper`, `Windows_Shutdown`.

## Route elsewhere

- Non-network CLI, algorithms, shell helpers, text/file utilities, and pure stdlib puzzles belong to `cli-algorithms-and-utilities`.
- Tkinter/pygame/turtle display-first games and desktop apps belong to `games-gui-and-desktop` unless the task is specifically network or credential automation.
- Web scraping as data extraction, PDFs, images, audio, notebooks, OpenCV, TensorFlow/Keras, or YOLO workflows belong to `data-media-ml-and-vision` unless the task is deploying or securing a service wrapper.

## Safe operating workflow

1. Identify the target mini-project folder and treat it as a standalone project; do not install root requirements as a universal environment.
2. Run the bundled static checker before any execution:
   `python scripts/check_service_project.py <repo-checkout>/<project-folder>`.
   The checker reads files and parses Python AST only; it does not import modules, start servers, send mail, scan ports, or call the network.
3. Read `references/service-recipes.md` for the folder-specific startup or safe-test recipe.
4. Read `references/dependency-and-credential-map.md` before installing dependencies, setting environment variables, choosing ports, or preparing test accounts.
5. If execution is necessary, run from the project folder unless the recipe says otherwise. Many templates, SQLite files, `.env` files, and relative imports assume the project cwd.
6. Use local-only, disposable resources: temporary SQLite files, loopback ports, test Firebase/SMTP/IMAP/Bitly/WhatsApp accounts, and non-production PostgreSQL databases.
7. Never run destructive or spam-capable scripts on a shared host. `Windows_Shutdown`, `spam_bot`, broad `Port Scanner` runs, and real mass email/WhatsApp sends require explicit human authorization and a dry-run or mocked substitute first.

## Evidence basis

This sub-skill was distilled from project-local evidence such as `RSS_Manager/pyproject.toml`, `RSS_Manager/main.py`, Flask app READMEs, service source files, and unsafe automation README/source warnings. The runtime guidance is self-contained so future agents can apply it to any compatible checkout without reopening the original production notes.

## Bundled references

- `references/service-recipes.md` — folder-by-folder service and safe test recipes.
- `references/dependency-and-credential-map.md` — dependencies, ports, credentials, generated files, and safety classes.
- `references/troubleshooting.md` — app module/cwd, port, database, credential, socket, Windows-only, and destructive automation failures.
- `scripts/check_service_project.py` — static service and automation hazard checker.
