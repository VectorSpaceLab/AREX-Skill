# Cross-cutting troubleshooting

Use this repo-level page before a specific sub-skill page when the failure is about setup, routing, or safety rather than one project family.

## Symptom-to-route table

| Symptom | Likely cause | First recovery step | Route next |
| --- | --- | --- | --- |
| A user asks to "run the repo" or install everything | There is no root package; the checkout is a gallery of independent folders. | Identify the target folder or category from `project-catalog.md`; do not install root-wide dependencies. | Relevant sub-skill. |
| `pip install -r requirements.txt` fails at repo root | The root file is UTF-16LE and includes explanatory prose, not only requirement specifiers. | Use project-local requirements or inspect imports statically. | Dependency map + target sub-skill. |
| Script fails because a file cannot be found | Many projects assume current working directory is the project folder. | Run via a wrapper or set cwd to the project folder; preserve asset subdirectories. | Target sub-skill. |
| `ModuleNotFoundError` for a sibling module | Folder names are not packages; imports assume the script directory is on `sys.path`. | Run from the project folder or add that folder to `PYTHONPATH` for the check only. | CLI or target sub-skill. |
| `TclError`, pygame video error, curses setup error | GUI/terminal UI launched in a headless session. | Keep verification static or use a real display/TTY session. | `games-gui-and-desktop`. |
| Server never returns or blocks the shell | Service script starts an infinite loop or development server. | Use static checker first; if live run is required, isolate port/process and add timeout. | `web-network-and-automation`. |
| Network scraper returns empty/403/429 | Website layout changed, throttled, or needs headers/session. | Use a saved HTML fixture; update selectors before live scraping. | `data-media-ml-and-vision`. |
| App requests tokens, email login, Firebase config, browser session, or WhatsApp | The project is credentialed automation. | Use mocks or disposable accounts only after explicit authorization. | `web-network-and-automation`. |
| CV/ML demo imports but live behavior fails | Import does not prove camera/model/GPU/download readiness. | Prepare a project-specific environment and tiny fixture; do not treat CPU import as full validation. | `data-media-ml-and-vision`. |
| A script wants to shut down the host, spam messages, scan ports, or dump databases | Unsafe/destructive project. | Do not run; inspect statically or design a mock/dry-run harness. | `web-network-and-automation`. |

## Safe default workflow

1. Identify the mini-project folder or task family with `project-catalog.md`.
2. Run the root static scanner instead of running project code:
   - `python scripts/inventory_mini_projects.py --root <checkout> --category <category>`
   - `python scripts/check_project_static.py --root <checkout> <project-folder>`
3. Read the owning sub-skill and its troubleshooting page.
4. Prepare a project-local environment only for the selected folder and verification target.
5. Execute live code only when the safety class allows it and the user has authorized required display, network, credentials, hardware, or host side effects.

## Generated output and review artifacts

- Runtime files live inside this skill tree.
- Verification reports, test cases, and construction notes are not runtime content and should stay outside the generated skill tree.
- If refreshing the skill after source changes, update the project catalog, dependency map, provenance, and native candidate map together.
