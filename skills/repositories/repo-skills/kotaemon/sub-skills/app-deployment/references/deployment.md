# App Deployment

This reference helps future agents install and launch the Kotaemon Gradio app without depending on the original source docs.

## Deployment choices

| Mode | Use when | Safe operator notes |
| --- | --- | --- |
| Docker image | The user wants the quickest isolated app run and accepts container volumes. | Mount a persistent `ktem_app_data` directory; expose `7860`; set Gradio host/port with env vars. |
| Local `uv` install | The user has a checkout and wants a reproducible source install. | Use Python 3.10 per project docs; expect a broad dependency set and slow wheels on first install. |
| Local conda/editable install | The user is developing or debugging source packages. | Install `libs/kotaemon` and `libs/ktem` editable; optional parser/provider dependencies may still be missing. |
| Hugging Face Space | The user wants online hosted setup. | Duplicate the template Space, wait for build, then complete first setup in the app UI. |

## Docker launch pattern

Use Docker when the user asks for a clean operator deployment and is comfortable with container networking.

```bash
docker run \
  -e GRADIO_SERVER_NAME=0.0.0.0 \
  -e GRADIO_SERVER_PORT=7860 \
  -v ./ktem_app_data:/app/ktem_app_data \
  -p 7860:7860 -it --rm \
  ghcr.io/cinnamon/kotaemon:main-lite
```

Choose the image variant deliberately:

- `main-lite`: smaller image; works for common workflows.
- `main-full`: includes additional `unstructured` support for more document types at the cost of image size.
- `main-ollama`: bundles Ollama-oriented local/private RAG support.

If local providers such as Ollama run on the host while Kotaemon runs in Docker, `localhost` inside the container is the container, not the host. Replace local-provider base URLs with an address reachable from the container, such as Docker host gateway names on supported platforms or a LAN address.

## Local source install

Recommended project install path:

```bash
uv sync --python 3.10
source .venv/bin/activate
cp .env.example .env
python app.py
```

Conda/editable alternative:

```bash
conda create -n kotaemon python=3.10
conda activate kotaemon
pip install -e "libs/kotaemon[all]"
pip install -e "libs/ktem"
cp .env.example .env
python app.py
```

Operator cautions:

- A complete install may download many packages, including Gradio, LangChain/LlamaIndex integrations, Chroma/LanceDB, document parsers, and provider SDKs.
- Optional document parsers and provider backends are not all required for basic startup; missing optional packages usually affect specific file types or providers.
- Editable metadata for `kotaemon==0.0.1` and `ktem==0.0.1` can exist even when all optional dependencies are not installed.

## Launch entrypoint

The root `app.py` constructs `ktem.main.App`, creates the Gradio app, queues it, and launches it in-browser. It allows static paths for bundled app assets and the Gradio temp directory.

Relevant environment/config values:

- `GRADIO_SERVER_NAME` and `GRADIO_SERVER_PORT`: standard Gradio host/port controls, useful for Docker and remote servers.
- `KH_GRADIO_SHARE`: read by `flowsettings.py`; when true, Gradio sharing is enabled.
- `GRADIO_TEMP_DIR`: if unset, `app.py` defaults it to `<KH_APP_DATA_DIR>/gradio_tmp`.

Do not run `python app.py` as a diagnostic unless the user has approved launching a server.

## App data directory

`flowsettings.py` defaults `KH_APP_DATA_DIR` to `ktem_app_data` next to `flowsettings.py` and creates subdirectories at import time:

- `user_data/`: SQLite database, user files, docstore, vectorstore, and other persistent app data.
- `markdown_cache_dir/`, `chunks_cache_dir/`, `zip_cache_dir/`, `zip_cache_dir_in/`: generated ingestion/export caches.
- `huggingface/`: `HF_HOME` and `HF_HUB_CACHE` are pointed here for local model/cache management.
- `gradio_tmp/`: used as the default Gradio temp directory when `GRADIO_TEMP_DIR` is unset.

Back up the whole `ktem_app_data/` tree before update, migration, or destructive cleanup. Permissions problems usually appear as SQLite open errors, upload/write failures, or missing cache files.

## PDF.js viewer assets

Kotaemon can display PDF citations in an in-browser PDF viewer. `ktem.assets` reads:

- `PDFJS_VERSION_DIST`, default `pdfjs-4.0.379-dist`.
- `PDFJS_PREBUILT_DIR`, default `<ktem package>/assets/prebuilt/<PDFJS_VERSION_DIST>`.

The repository scripts download PDF.js from Mozilla and unzip it into the prebuilt assets directory. Those scripts perform network and file-write side effects, so use `scripts/check_app_config.py` first to verify whether the directory already exists.

If the PDF viewer is blank or citation previews fail while chat still works, check that `PDFJS_PREBUILT_DIR` exists and contains a PDF.js distribution with viewer assets such as `web/viewer.html` or distribution files under `build/` and `web/`.

## Release scripts are reference-only

The `run_linux.sh`, `run_macos.sh`, and `run_windows.bat` workflows install Miniconda or tools, create environments, install packages, download PDF.js, optionally start a local model server helper, and launch the UI. They are useful for understanding the intended flow but are not safe diagnostics because they mutate the machine and may download large artifacts.

The `download_pdfjs.sh` helper performs a network download and unzip. The update scripts activate a managed conda environment and reinstall from a Git source. Treat all of these as side-effectful operator actions requiring explicit approval.
