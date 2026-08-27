---
name: data-media-ml-and-vision
description: "Route scraping, media conversion, plotting, vision, and ML demo tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# data-media-ml-and-vision

Use this sub-skill for python-mini-project folders whose main job is one of these:
- scraping or tabular collection
- PDF, image, audio, QR, or ASCII conversion
- notebook-driven plotting or ML demos
- OpenCV, MediaPipe, TensorFlow, Keras, Ultralytics, Folium, Plotly, or NLTK work
- Windows-only Excel COM conversion

Representative folders:
- Web scraping for book names
- Web Scraping IPhone from Flipkart
- Slideshare to PDF
- Demerge_pdfs
- Image_compressor
- Simple_Image_resize
- images_to_pdf_converter
- image_comparator
- img_to_ascii
- QR Code Generator
- qr_with_logo
- Download Audio
- Youtube_video_download
- TextToSpeech
- Speech_To_Text
- Speaking_Dictionary
- Speaking_Wikipedia
- Face_Recognition
- Finding_Lanes
- Motion_Detection
- Object_Detection
- Shape_Recognition
- Geo_Plot_Using_Folium
- Plotter
- Regression using ANN
- digit-recognizer
- mnist_digit_recognizer
- Text_Predication
- xls_to_xlsx

Route to web-network-and-automation instead when the main task is deploying or operating a Flask/FastAPI service, handling credentials or secrets, or maintaining long-lived API/server behavior.

Route to cli-algorithms-and-utilities when the project is really a pure stdlib helper with no media, scraping, notebook, or ML dependency.

Working rules:
1. Stay inside the current checkout.
2. Read the project README, requirements, and notebook files as static evidence.
3. Run scripts/check_heavy_project_requirements.py before changing heavy folders.
4. Assume network, camera, microphone, speakers, GPU, model download, notebook kernel, and Windows COM dependencies are optional unless the task explicitly asks for them.
5. Do not execute project code by default. Use a safe sample file or fixture only when a live check is explicitly requested and the environment is ready.

What to produce:
- a short task summary
- a dependency/backend risk note
- a safe next-step plan or handoff to another sub-skill when the boundary is crossed

See:
- references/data-media-recipes.md
- references/ml-vision-dependency-map.md
- references/troubleshooting.md
- scripts/check_heavy_project_requirements.py
