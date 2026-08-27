# Interactive/App Troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: fastapi`, `streamlit`, `uvicorn`, or `python_multipart` | API extra missing. | Install `pip install "pix2tex[api]"`; run the API dependency checker. |
| `POST /predict/` returns validation error | Wrong multipart field name or non-image upload. | Send `files={"file": open(..., "rb")}` and verify the image with the OCR image inspector. |
| `uvicorn app:app` cannot find module | Running from the wrong directory for the source helper. | Prefer `uvicorn pix2tex.api.app:app --port 8502` from an installed package. |
| Streamlit page cannot connect | API process is not listening on port 8502. | Start API first or use `python -m pix2tex.api.run` when long-running processes are allowed. |
| GUI import fails for PyQt/WebEngine/pynput/screeninfo/latex2sympy2 | GUI extra missing or platform package issue. | Install `pix2tex[gui]`; on Linux ensure Qt/WebEngine dependencies and display are available. |
| Screenshot opens the wrong tool | Auto-detection picked an incompatible backend. | Set `SCREENSHOT_TOOL=grim`, `spectacle`, `gnome-screenshot`, or `pil`. |
| Qt WebEngine sandbox error on Linux | Qt sandbox restrictions in some environments. | The GUI sets `QTWEBENGINE_DISABLE_SANDBOX=1` for non-Windows; confirm sandbox policy before launching in restricted environments. |
| Docker command fails | Docker daemon/network/image unavailable. | Verify Docker access separately; do not treat Docker failure as pix2tex model failure. |
