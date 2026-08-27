# GUI and desktop runtime guide

This sub-skill covers local interactive projects. Use the static checker first, then decide whether a live desktop or terminal session is actually needed.

## Runtime families

| Family | Examples | Runtime needs | Static notes |
| --- | --- | --- | --- |
| Tkinter / customtkinter / turtle | `Connect-Four`, `Color_Game`, `Egg_Catcher`, `Screenpet`, `Simple_dice`, `Chinese_FlashCard`, `Finance_Tracker`, `Investment Calculator`, `Caterpillar_Game`, `Music-Player` | A real GUI session with Tk available. Turtle uses Tk under the hood. `matplotlib.pyplot.show()` also wants a desktop backend. | Do not treat a headless import as proof that the GUI will run. |
| pygame | `Chess_Game`, `Snake_game`, `Lazy_Pong`, `Othello-Reversi-Game`, `Spinning Donut` | SDL video support, and sometimes audio. Images, fonts, and icons often live beside the script. | Check for `pygame.init()`, `pygame.display.set_mode()`, `pygame.image.load()`, and font usage. |
| Terminal / curses | `Convoys_GameofLife`, `HangMan`, `Hangman_Game`, `Minesweeper_game`, `Tic_Tac_Toe`, `TEXTVENTURE`, `TestTypingSpeed`, `Zombie_Game` | A real TTY and interactive stdin/stdout. `curses` usually needs a proper terminal, not a notebook or redirected output. | These projects can still be desktop games even when they never open a window. |
| Data-linked desktop demos | `Chinese_FlashCard`, `Finance_Tracker`, `Investment Calculator`, `Zombie_Game` | GUI plus requests, plotting, or live data. Network and chart backends may matter as much as the windowing toolkit. | If the task is mostly scraping or data shaping, hand it to the data or network skill instead. |
| Audio / media playback | `Music-Player` | Tk plus native VLC/libvlc and playable media files. | A pip package alone is not enough if the native VLC library is missing. |

## Dependency interpretation

- Treat `tkinter`, `turtle`, `curses`, `random`, `os`, `sys`, `glob`, `time`, and `re` as stdlib or system features. Do not suggest `pip install` for them.
- External packages in this subtree are usually `pygame`, `customtkinter`, `python-vlc`, `matplotlib`, `numpy`, `pandas`, `plotly`, `requests`, `beautifulsoup4`, and `essential-generators`.
- Some README snippets are stale or misleading. Trust the checker and file inventory over a copy-pasted install command.

## Asset and path rules

- Keep images, icons, fonts, audio, and support files beside the script or in the bundled asset directory.
- Resolve runtime paths from `Path(__file__).resolve().parent` instead of assuming the current working directory.
- Treat `images/`, `img/`, `Assets/`, and `Gotham-Font/` as part of the runtime surface, not documentation noise.
- If the checker reports absolute paths or remote URLs, treat them as portability or network dependencies that need explicit handling.

## Checker output fields

- `stack_tags`: the runtime style detected for the folder, such as `tk`, `pygame`, `terminal`, `curses`, `audio`, `network`, or `data`.
- `entry_candidates`: the likely launch files after local imports are filtered out.
- `requirements_files`: detected dependency files and their decoded package hints.
- `requirements_hints`: missing or mismatched dependency notes.
- `asset_dirs` and `asset_files`: runtime files that should ship with the project.
- `support_files`: local state, config, or data files that the code expects.
- `remote_urls` and `absolute_paths`: portability or network risks.

## How to use the result

1. Scan the folder.
2. Identify the runtime family.
3. Check the asset and support files.
4. Only then decide whether a live run is warranted.
