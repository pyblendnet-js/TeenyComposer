# Teeny Composer
![Teeny Composer screenshot]("/teeny composer.png")

## About
Teeny Composer is a simple midi file editor for creation or editing of simple tunes.

## Features V0.1

- shows notes as bar either on stave or piano view
- addition and deletion of notes or tracks
- variable speed playback using fluidsynth and GeneralUser-GS.sf2 sound bank
- transposition
- tracks can be independantly saved and loaded to a simple text based format

## Installation

Locate everything anywhere you like. Assuming you have python3 installed, then for the first time, run python3 TeenyComposer.py from a terminal and you'll see what dependancy packages are missing.

### Dependancies

- python3
- tkinter (usually included with python)
- mido (to load and save midifiles but then not used internally)
- pyfluidsynth and fluidsynth (only needed if using playback) 

## Mouse click and drag behaviour

Left button - drag right on canvas to add or modify note
            - drag left over note to delete
            - single click to locate playback cursor
Right button - drag right to indicate area to zoom.
            If mostly horizontal, then time zoom only.
            If mostly vertical then note range zoom only.
Middle button - drag to move view

