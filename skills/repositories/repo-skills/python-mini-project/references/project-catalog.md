# Python Mini Projects catalog

This repo is a gallery of standalone mini-project folders, not a single importable Python package. Use this catalog to route a task by project family before choosing an environment or running anything. Folder names below are evidence names from the source repository; treat them as relative targets in a fresh checkout, not links to this original checkout.

## Category routes

| If the task mentions... | Use sub-skill | Typical verification posture |
| --- | --- | --- |
| Adding a new mini project, reviewing a PR, fixing README/requirements/hygiene | `contribution-and-project-maintenance` | Static review, template/skeleton generation, no project execution by default. |
| Algorithms, text/file utilities, calculators, data structures, small stdlib scripts | `cli-algorithms-and-utilities` | Safe static checks; only curated native checks for `Cat_command` and `Execute Shell Command` by default. |
| Tkinter, pygame, turtle, terminal games, desktop/audio loops | `games-gui-and-desktop` | Static/dependency checks first; live execution only with a display/audio-capable session. |
| Flask/FastAPI apps, sockets, URL/mail/RSS/IP automation, bots, host automation | `web-network-and-automation` | Static service and credential checks first; no network/service/destructive action without explicit scope. |
| Scraping, PDF/image/audio conversion, notebooks, OpenCV, TensorFlow/Keras, YOLO, plotting | `data-media-ml-and-vision` | Static dependency/backend checks first; live runs need prepared data/network/camera/model environment. |

## CLI, algorithms, and utilities

Primary owner: `sub-skills/cli-algorithms-and-utilities/`.

- Core data structures/algorithms: `Binary_Search_Tree`, `Binary_tree`, `Prefix_Trie`, `linked_lists`, `Stack_structure`, `Tower-of_Hanoi`, `Sudoku_solver`.
- Text and encoding helpers: `Caesar_Cipher`, `Converting_Roman_to_Integer`, `Email Slicer`, `Encode_Morse.py`, `ExtractPhoneNumberEmail`, `Morse_code_beep`, `string_manipulator`, `TextEncryptor`, `lorem_in_python`, `Word_Jumble`, `Wordle_Aid`, `minionGame`.
- File/CLI utilities: `Cat_command`, `Diff_Utility`, `Execute Shell Command`, `csv_to_json`, `Converter`, `Address Validator`.
- Simple console games or math exercises that do not require a display-first runtime: `Expense_Tracker`, `Fancy_Text_Generator`, `GK_Maestro`, `Hashed_and_Salted_Pass`, `Madlibs`, `Number Guessing`, `Number Guessing Upper Boundary`, `Password_Generator_2`, `Password_Manager`, `Rock_Paper_Scissors_Spock`, `Star_Pyramid`, `Triangle Calculator`.

Notes:
- `Execute Shell Command` is useful as a tiny test-backed utility, but new code should avoid arbitrary `shell=True` behavior.
- GUI-backed projects with reusable algorithms, such as `Smart_Calculator`, belong to the GUI route for runtime, with algorithm details referenced from the CLI route only when static inspection is enough.

## Games, GUI, and desktop apps

Primary owner: `sub-skills/games-gui-and-desktop/`.

- Pygame/turtle/curses games and loops: `Caterpillar_Game`, `Chess_Game`, `Convoys_GameofLife`, `Exercise-Timer`, `Lazy_Pong`, `Othello-Reversi-Game`, `Snake_game`, `Spinning Donut`.
- Tkinter/customtkinter games and UI exercises: `Chinese_FlashCard`, `Color_Game`, `Connect-Four`, `Dictionary`, `Egg_Catcher`, `Finance_Tracker`, `Investment Calculator`, `Minesweeper_game`, `Password Generator`, `Screenpet`, `Simple_dice`, `Smart_Calculator`, `Sqlite-crud`, `TestTypingSpeed`, `Weights_on_different_planets`.
- Terminal/interactive games and puzzles: `Dice_Rolling_Stimulator`, `HangMan`, `Hangman_Game`, `infix_postfix_calculator`, `Matchmaker`, `Math_Game`, `TEXTVENTURE`, `Tic_Tac_Toe`, `Zombie_Game`.
- Desktop/media shells: `Music-Player`.

Notes:
- Treat GUI and game folders as long-running, interactive projects even when their README says only `python main.py`.
- Asset folders such as images, fonts, or audio are project-local runtime prerequisites; do not move or delete them during cleanup.

## Web, network, service, and automation projects

Primary owner: `sub-skills/web-network-and-automation/`.

- Web apps and services: `Crud_in_flask`, `Firebase_Authentication_Using_Flask`, `RSS_Manager`, `Todo_App`, `Url_Shortener`, `website-builder`.
- Socket/HTTP/network utilities: `Simple_Http_Server`, `Socket_example`, `IP_Locator`, `Port Scanner`.
- Email, bot, and desktop automation: `Automated_Mailing`, `Mail_Checker`, `Whatsapp_Bot`, `desktopassistant`, `spam_bot`.
- Database or host/system automation: `PostgreSQL_Dumper`, `Windows_Shutdown`.

Notes:
- Credentialed or destructive projects must stay static-only until the user authorizes a disposable test account, network target, or host-side effect.
- `Windows_Shutdown` is intentionally classified as unsafe; never run it as a verification smoke test.

## Data, media, ML, and vision projects

Primary owner: `sub-skills/data-media-ml-and-vision/`.

- Web scraping and data collection: `Web scraping for book names`, `Web Scraping IPhone from Flipkart`, `web scraping- Find python jobs from a website`, `Currency_Converter`, `Google_Translate`.
- Documents, PDFs, images, and QR/media conversion: `Clip_Organizer`, `Demerge_pdfs`, `Download Audio`, `Image_compressor`, `Simple_Image_resize`, `images_to_pdf_converter`, `image_comparator`, `img_to_ascii`, `QR Code Generator`, `qr_with_logo`, `Slideshare to PDF`, `Youtube_video_download`, `xls_to_xlsx`.
- Speech/audio/text-language demos: `Animalese_translator`, `simple-chatbot`, `Speaking_Dictionary`, `Speaking_Wikipedia`, `Speech_To_Text`, `Text_Predication`, `TextToSpeech`.
- CV, plotting, notebooks, and ML: `Face_Recognition`, `Finding_Lanes`, `Geo_Plot_Using_Folium`, `mnist_digit_recognizer`, `Motion_Detection`, `NASA_Image_Extraction`, `Object_Detection`, `Plotter`, `Regression using ANN`, `Shape_Recognition`, `digit-recognizer`.

Notes:
- Many projects in this category require network, camera, local media files, heavyweight model packages, or OS-specific tooling.
- Use static inspection and tiny fixtures before live scraping, model loading, camera access, or notebook execution.

## Long-tail routing rule

If a new or renamed folder is not listed here, route by execution surface:

1. If the task is about adding/reviewing/fixing project structure, use `contribution-and-project-maintenance`.
2. If it is stdlib-oriented and terminal-first, use `cli-algorithms-and-utilities`.
3. If it opens a window, uses pygame/turtle/curses/Tk, or needs assets/audio, use `games-gui-and-desktop`.
4. If it starts a server, performs network/credentialed automation, or mutates a host/service, use `web-network-and-automation`.
5. If it processes documents/images/audio/data, scrapes sites, uses notebooks, CV, or ML frameworks, use `data-media-ml-and-vision`.
