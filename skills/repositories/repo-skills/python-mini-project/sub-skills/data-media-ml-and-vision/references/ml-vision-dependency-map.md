# ML and vision dependency map

This file maps package clues to backend needs and safe-default behavior. It is for static triage, not for installation or execution.

## Backend matrix

| Clue or package family | Typical files or imports | Backend or system need | Why it is heavy or fragile | Safe default |
| --- | --- | --- | --- | --- |
| Web scraping and tabular extraction | requests, bs4, BeautifulSoup, pandas, validators | Network access only | Site layout drift, anti-bot behavior, paging changes, and fragile selectors | Inspect HTML or use a cached fixture before touching live requests |
| Local document and image conversion | PIL/Pillow, PyPDF2, img2pdf, qrcode, pyqrcode, pypng, easygui, pywhatkit | Local filesystem; sometimes GUI dialogs | Corrupt PDFs, bad image paths, extension mismatches, and GUI prompts in headless sessions | Work on copies and validate paths and file types first |
| Audio download and transcription | pytube, moviepy, ffmpeg, pyttsx3, speech_recognition, PyAudio, gTTS, PyDictionary, wikipedia | Network, audio output, microphone input, and codec binaries | Missing ffmpeg, missing portaudio/PyAudio wheels, no microphone, or no speaker device | Keep audio capture and transcoding off by default |
| OpenCV image and video demos | cv2, numpy, mediapipe | Display, webcam, or sample video/image files | No `$DISPLAY`, camera permissions, missing codecs, and frame size assumptions | Prefer saved media over webcam and document the quit key |
| Object detection and model inference | torch, ultralytics, YOLO, cv2 | Model weights, CPU or GPU, and usually display/camera | Weights may download automatically; CUDA or torch mismatch can block inference | Treat model downloads and webcam use as optional until requested |
| TensorFlow / Keras demos | tensorflow, keras, sklearn, pandas, numpy | CPU or GPU runtime; isolated Python env | Old TensorFlow pins, Keras compatibility, and large training/runtime costs | Do not mix incompatible TF/Keras versions in one environment |
| Notebook-first plotting and analytics | .ipynb files, folium, plotly, cufflinks, chart_studio, matplotlib, pandas | Jupyter kernel and notebook runtime | Hidden state, out-of-order cells, and dependency drift inside notebooks | Inspect cells statically first; avoid auto-running notebooks |
| Windows Excel COM conversion | win32com, pywin32, Dispatch("Excel.Application") | Windows desktop with Excel installed | COM is unavailable off Windows and can fail if Excel is missing or locked | Skip on non-Windows hosts and document the limitation |

## Package-to-backend notes

| Package or clue | What it usually implies | Projects where it appears | Backend warning to surface |
| --- | --- | --- | --- |
| requests + BeautifulSoup + pandas | Live web scraping or structured HTML extraction | Web scraping for book names; Web Scraping IPhone from Flipkart; Slideshare to PDF | Network fragility and site layout drift |
| PIL / Pillow | Image open, resize, compress, or compositing work | Image_compressor; Simple_Image_resize; Slideshare to PDF; qr_with_logo | Bad paths, corrupt image bytes, and format mismatch |
| PyPDF2 / img2pdf | PDF split/merge or image-to-PDF conversion | Demerge_pdfs; images_to_pdf_converter | Broken page counts, bad PDFs, and output overwrite risk |
| qrcode / pyqrcode / pypng | QR code generation | QR Code Generator; qr_with_logo | Missing logo files or wrong save directory |
| pytube / moviepy | YouTube media download or audio extraction | Download Audio; Youtube_video_download | Network reliance and ffmpeg dependency |
| pyttsx3 / speech_recognition / PyAudio | Text-to-speech or microphone transcription | TextToSpeech; Speech_To_Text; Speaking_Dictionary | Audio hardware and portaudio issues |
| cv2 / mediapipe / numpy | OpenCV vision and frame math | Face_Recognition; Finding_Lanes; Motion_Detection; Shape_Recognition | Camera/display availability and frame assumptions |
| torch / ultralytics | YOLO-style object detection | Object_Detection | Automatic model download and GPU/CPU mismatch |
| tensorflow / keras | Neural network training or inference | digit-recognizer; mnist_digit_recognizer; Regression using ANN | Old version pins, large dependency stacks, and runtime cost |
| folium / plotly / cufflinks / chart_studio | Notebook plotting or map visualization | Geo_Plot_Using_Folium; Plotter | Jupyter-only workflow and optional online plotting service |
| win32com / pywin32 | Excel COM automation | xls_to_xlsx | Windows-only COM and installed Excel required |

## Version and platform watchlist

| Location | Pin or clue | Risk | What the checker should say |
| --- | --- | --- | --- |
| digit-recognizer/requirements.txt | tensorflow=2.1.0, cudatoolkit=10.1, cudnn=7.6, protobuf==3.19.0 | Old GPU-era stack and possible ABI conflicts | Flag old TensorFlow pinning and GPU dependence |
| mnist_digit_recognizer/requirements.txt | tensorflow==2.15.0, keras=3.0.2 | TensorFlow and Keras compatibility risk | Flag version pairing as environment-sensitive |
| Object_Detection/requirements.txt | ultralytics>=8.0.100, opencv-python>=4.5.5.62 | Model downloads plus webcam/display need | Flag camera/model-download and display risk |
| Speaking_Dictionary/requirements.txt and README | pyttsx3, PyDictionary, speech_recognition, gTTS, pyaudio | Audio hardware plus network lookups | Flag microphone, speaker, and install complexity |
| xls_to_xlsx/requirements.txt | pywin32==306 | Windows COM only | Flag Windows and Excel as hard prerequisites |
| Plotter/Plotter.ipynb | chart_studio, cufflinks, plotly | Notebook and optional online plotting | Flag notebook-first workflow and optional service login |
| Geo_Plot_Using_Folium/Geo_plot.ipynb | folium, basemap note in README | Notebook runtime and possibly heavy map packages | Flag notebook use and avoid eager installation guesses |

## Hazard tags used by the checker

- network
- credentials
- camera
- display
- audio
- codec
- model-download
- tensorflow-pin
- notebook
- windows-com
- service-deployment

## Default interpretation rules

- If a folder imports cv2, torch, ultralytics, mediapipe, or tensorflow, treat it as heavy even if it has a GUI.
- If a folder imports pyttsx3, speech_recognition, pyaudio, moviepy, or pytube, treat audio/network access as optional and explicitly gated.
- If a folder contains .ipynb files, treat it as notebook-first until proven otherwise.
- If a folder imports win32com or uses Dispatch("Excel.Application"), treat it as Windows-only.
- If a folder is a Flask or FastAPI service around an ML model, consider that a routing boundary and hand off to web-network-and-automation.
