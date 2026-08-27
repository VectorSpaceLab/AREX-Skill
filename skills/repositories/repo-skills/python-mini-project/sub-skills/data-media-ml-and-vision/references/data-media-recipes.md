# Data, media, vision, and ML recipes

Use this map to decide which style of work a folder needs. Stay static and local first; only cross into live network, camera, microphone, speaker, or model-download work when the task explicitly asks for it.

## Boundary guide

- Stay here for scraping, local file conversion, media transforms, OpenCV demos, notebooks, plotting, and ML notebooks.
- Hand off to web-network-and-automation when the primary task is service deployment, credential handling, or long-lived API/server behavior.
- Hand off to cli-algorithms-and-utilities when the task is a pure stdlib CLI helper with no media, scraping, or ML dependency.
- Hand off to games-gui-and-desktop only when the code is mainly a game or general desktop UI with no data/media focus.

## Project family map

| Family | Representative folders | Common inputs and outputs | Safe-default handling | Boundary notes |
| --- | --- | --- | --- | --- |
| Web scraping and tabular collection | Web scraping for book names; Web Scraping IPhone from Flipkart | URLs in, HTML/CSV/DataFrame out | Cache or fixture the page before changing selectors; keep live requests off by default | Flipkart mail delivery and credential handling belong in web-network-and-automation if that is the primary task |
| Document and PDF transforms | Slideshare to PDF; Demerge_pdfs; images_to_pdf_converter | URLs, PDFs, or image folders in; PDF split/merge output out | Verify path, page count, and file type before writing output | Treat website scraping and download steps as optional, not automatic |
| Image utilities and QR tools | Image_compressor; Simple_Image_resize; image_comparator; img_to_ascii; QR Code Generator; qr_with_logo | Local images or text in; resized images, ASCII text, or QR images out | Operate on copies and check extensions; avoid overwriting originals | GUI front-ends such as Tkinter or easygui stay here because the media conversion is the point |
| Audio, speech, and download helpers | Download Audio; Youtube_video_download; TextToSpeech; Speech_To_Text; Speaking_Dictionary; Speaking_Wikipedia | Video URLs, microphone input, or text in; MP3, transcript, or spoken output out | Keep network and microphone access off by default; note codec and speaker requirements | If the task becomes an app-service wrapper, route to web-network-and-automation |
| Vision and OpenCV demos | Face_Recognition; Finding_Lanes; Motion_Detection; Object_Detection; Shape_Recognition | Images, video files, or webcam feed in; annotated frames or detections out | Prefer sample images/videos over live camera input; do not auto-download weights | Live webcam and display are runtime dependencies; do not assume they exist |
| Notebook plotting and analytics | Geo_Plot_Using_Folium; Plotter; Regression using ANN; mnist_digit_recognizer; Text_Predication | Notebooks, CSVs, and model code in; charts, predictions, or notebook output out | Inspect notebook cells and import lines statically before any execution | Keep service deployment of a model app in web-network-and-automation |
| TensorFlow/Keras demo apps | digit-recognizer; mnist_digit_recognizer; Regression using ANN | Training data and model artifacts in; predictions or trained model out | Check version pins before installing; isolate the environment | If the request is really about exposing a Flask app, move to web-network-and-automation |
| Windows Excel conversion | xls_to_xlsx | .xls input; .xlsx output | Windows only; require Excel and pywin32/COM | Never assume this works on Linux or macOS |

## Recipe table

| Recipe | Files or clues to look for | What the future agent should verify | What to avoid by default |
| --- | --- | --- | --- |
| Scrape book names into a DataFrame | Web scraping for book names/scraping.py; requests; BeautifulSoup; pandas | Selector stability, output columns, and whether the page still exists | Replaying live scraping loops without a fixture |
| Scrape Flipkart iPhone listings | Web Scraping IPhone from Flipkart/project.py and all functions.py; requests; BeautifulSoup; pandas; smtplib; password module | CSV schema, pagination, and whether the mail step is really needed | Treating email delivery as part of a static scrape task |
| Turn Slideshare slides into a PDF | Slideshare to PDF/main.py; validators; requests; bs4; PIL | URL validity, slide image extraction, and PDF write path | Running against untrusted live pages without a fallback file |
| Split one PDF into many PDFs | Demerge_pdfs/demerging_pdfs.py; PyPDF2; input page counts | Page count math, output file names, and whether the input PDF exists | Overwriting original PDFs or assuming page counts are valid |
| Compress or resize local images | Image_compressor/image_compressor.py; Simple_Image_resize/main.py; PIL; easygui | Image extension handling, quality/compression settings, and output directory | Mutating the source image set in place |
| Compare two images | image_comparator/image_comparison.py; cv2 | Same-size comparison, valid image reads, and diff output path | Assuming missing or corrupt images will compare cleanly |
| Convert an image to ASCII | img_to_ascii/img_to_ascii.py; pywhatkit | Image path, text output name, and output encoding | Running on a missing or non-image file |
| Generate QR codes | QR Code Generator/qrGenerator.py; qrcode; tkinter; qr_with_logo/qr.py; PIL | Input text, logo path, and output PNG path | Saving into the wrong directory or assuming a logo file exists |
| Download audio or video from YouTube | Download Audio/Download Audio.py; Youtube_video_download/main.py; pytube; moviepy | URL validity, output filename, and ffmpeg availability | Downloading or transcoding without explicit permission and storage path |
| Speak text or transcribe speech | TextToSpeech/Text_To_Speech.py; Speech_To_Text/Speech_To_Text.py; Speaking_Dictionary/Speaking_Dictionary.py; Speaking_Wikipedia/speaking_wikipedia.py | Speaker, microphone, and network access; whether the lookup service is available | Starting microphone loops or TTS loops by default in a headless session |
| Detect faces, motion, lanes, shapes, or objects | Face_Recognition/main.py; Finding_Lanes/lanes.py; Motion_Detection/main.py; Object_Detection/object-detection.py; Shape_Recognition/main.py | Camera or video file availability, display access, and model file access | Assuming webcam access or a GUI display is always present |
| Plot data in notebooks | Geo_Plot_Using_Folium/Geo_plot.ipynb; Plotter/Plotter.ipynb | Notebook kernel, CSV inputs, and whether the notebook is exploratory or runnable | Auto-running notebook cells without reading them first |
| Train or demo TensorFlow/Keras models | digit-recognizer/app.py; mnist_digit_recognizer/main.py; Regression using ANN/CCPP_ANN.ipynb | TensorFlow version, Keras compatibility, and model/data file location | Mixing incompatible TensorFlow and Keras pins in one environment |
| Convert .xls to .xlsx | xls_to_xlsx/xls_to_xlsx.py | Windows, Excel install, and pywin32 COM access | Running on non-Windows hosts or with an open locked workbook |

## Short operational recipe

1. Identify whether the folder is scraping, conversion, audio, vision, notebook, or ML.
2. Read the local README, requirements, and notebook cells as evidence.
3. Run scripts/check_heavy_project_requirements.py on the project folder or repo root.
4. Decide whether the task needs network, camera, audio, GPU, notebook, or Windows COM access.
5. If the task crosses into deployment or service hosting, hand it to web-network-and-automation.
6. Keep the work self-contained and avoid live execution unless the environment and task both justify it.
