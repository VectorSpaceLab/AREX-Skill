# Project recipes

Several READMEs in this subtree have stale entry filenames. Trust the checker and the actual file inventory over a copied run snippet.

| Project | Entry file | Runtime style | Notes |
| --- | --- | --- | --- |
| `Chess_Game` | `ChessGame.py` | pygame board game | `ChessEngine.py` helper, `images/`, `requirements.txt` pins `pygame==2.4.0`. |
| `Snake_game` | `main.py` | pygame arcade game | `snakeicon.ico`, no requirements file in tree. |
| `Connect-Four` | `main.py` | Tkinter board game | stdlib Tkinter only. |
| `Color_Game` | `main.py` | Tkinter timing game | `highest_score.txt` is writable local state. |
| `Caterpillar_Game` | `Caterpillar.py` | turtle game | Turtle uses the Tk backend; live window required. |
| `Convoys_GameofLife` | `GameOfLife.py` | curses terminal sim | `curses`, `copy`, `random`, `time`; demo media files `ConwayGif.gif` and `demo.png`; use a real TTY. |
| `Egg_Catcher` | `eggcatcher.py` | Tkinter canvas game | `Tk`, `Canvas`, `messagebox`; no external deps. |
| `HangMan` | `HangMan.py` | terminal word game | reads `words.txt`; pure stdlib. |
| `Hangman_Game` | `hangman.py` | terminal word game | pure stdlib prompt loop. |
| `Lazy_Pong` | `pong.py` | pygame arcade game | `pygame`, `argparse`, `logging`; may create `pong_log.log`. |
| `Minesweeper_game` | `minesweeper.py` | terminal puzzle | `random`, `re`; `images/` is screenshot evidence only. |
| `Othello-Reversi-Game` | `main.py` | pygame board game | `Board.py` helper, `images/`, `Gotham-Font/`, `requirements.txt` pins `pygame` and `numpy`. |
| `Screenpet` | `screenpet.py` | Tkinter + turtle desktop pet | `after()` timers and Tk-backed turtle graphics. |
| `Simple_dice` | `dice.py` | Tkinter toy app | `dice.png` must stay beside the script. |
| `Spinning Donut` | `spinningdonut.py` | pygame animation | no asset dir, but needs display and font support. |
| `Tic_Tac_Toe` | `tic_tac_toe.py` | terminal game | README text may name the file differently; trust the actual filename. |
| `TEXTVENTURE` | `game.py` | terminal adventure | `Assets/` directory, `os`, `sys`, `time`. |
| `Zombie_Game` | `zombie.py` primary; `main.py` alternate | terminal quiz plus data demo | `zombie.py` is the quiz; `main.py` fetches a remote CSV and builds a Plotly chart. |
| `Music-Player` | `music_player.py` | Tkinter audio player | `images/`, `python-vlc`, native VLC/libvlc, a real music folder, and a hardcoded music path in the source example. |
| `Chinese_FlashCard` | `app/main.py` | Tkinter flashcard app | `app/app.py`, `app/models.py`, `app/config.json`, live `requests` + `beautifulsoup4`, and top-level image files. |
| `Finance_Tracker` | `main.py` | customtkinter dashboard | `customtkinter`, `matplotlib`, `numpy`; pie-chart backend required. |
| `Investment Calculator` | `Calc.py` | customtkinter calculator | `customtkinter`, `matplotlib`, `numpy`, `img/` assets. |
| `TestTypingSpeed` | `TestTypingSpeed.py` | terminal typing trainer | `essential-generators`; `requirements.txt` is encoded as UTF-16 in this checkout. |
