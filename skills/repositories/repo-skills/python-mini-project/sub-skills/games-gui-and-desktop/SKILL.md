---
name: games-gui-and-desktop
description: "Operate and troubleshoot Tkinter, pygame, turtle, audio, and
  desktop game projects in python-mini-project."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# games-gui-and-desktop

Use this sub-skill for local interactive projects that open windows, draw on a canvas, play audio, or block on a terminal game loop.

## Use it for
- `Chess_Game`, `Snake_game`, `Connect-Four`, `Color_Game`, `Caterpillar_Game`, `Convoys_GameofLife`, `Egg_Catcher`, `HangMan`, `Hangman_Game`, `Lazy_Pong`, `Minesweeper_game`, `Othello-Reversi-Game`, `Screenpet`, `Simple_dice`, `Spinning Donut`, `Tic_Tac_Toe`, `TEXTVENTURE`, `Zombie_Game`, `Music-Player`, `Chinese_FlashCard`, `Finance_Tracker`, `Investment Calculator`, `TestTypingSpeed`.

## Route away when
- the task is mostly service, API, bot, or credentialed automation
- the task is mostly scraping, CV/ML, heavy plotting, or notebook/data work
- the task is mostly stdlib algorithms, utilities, or pure text processing

## Safe first step
Run `scripts/check_gui_requirements.py` on the target project folder(s). It parses Python files only, records GUI/game imports, requirement hints, asset directories and support files, and entry-loop signals. It never starts windows, audio, or game loops.

## Working rules
- Treat display and audio as optional until confirmed.
- Do not import or execute project modules during inspection.
- Expect `mainloop()`, `pygame.display.set_mode()`, `pygame.init()`, `turtle.mainloop()`, `curses.wrapper()`, and `while True` loops to be live-run entry points.
- Prefer relative asset paths anchored at the script directory.
- When the project depends on live data, native audio libraries, or a real terminal, report the dependency instead of forcing a headless run.

## Bundled files
- `references/gui-game-runtime.md`
- `references/project-recipes.md`
- `references/troubleshooting.md`
- `scripts/check_gui_requirements.py`

## Suggested flow
1. Inspect the target folder name and entry file.
2. Run the checker.
3. Read the recipe row for that project family.
4. Apply the troubleshooting guidance before any live run.
