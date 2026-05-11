# Teeny Composer
![Teeny Composer screenshot](/teeny-composer.png)

## About
Teeny Composer is a simple midi file editor for creation or editing of simple tunes.

## Features V0.1

- shows notes as bars either on stave or piano view
- addition and deletion of notes or tracks
- variable speed playback using fluidsynth and sound font (currently only GeneralUser-GS.sf2)
- transposition
- tracks can be independantly saved and loaded to a simple text based format

## Installation

Locate everything in a folder. Assuming you have python3 installed, then for the first time, run python3 TeenyComposer.py from a terminal and you'll see what dependancy packages are missing. Use pip to install.

The fluidsynth runtime can be installed using apt-get on linux, but is also available on Windows and Mac.
On windows, you need to locate the bin directory from the downloaded zip in C:/tool/fluidsynth

Download GeneralUser-GS.sf2 from one of the many sources and locate in the same folder.
The GeneralUser-GS.txt file is a list of that soundfonts contents with bank and numbers.
I got my sf2 file from https://github.com/mrbumpy409/GeneralUser-GS

Alternative sound fonts could be used but for V1 this requires changes in the program.
Modity and use list-sf2-instruments.sh to create your own list of the contents.

### Dependancies

- python3
- tkinter (usually included with python)
- mido (to load and save midifiles but then not used internally)
- pyfluidsynth and fluidsynth (only needed if using playback) 

## Mouse click and drag behaviour
git push -u origin master
Left button - drag right on canvas to add or modify note
            - drag left over note to delete
            - single click to locate playback cursor
Right button - drag right to indicate area to zoom.
            If mostly horizontal, then time zoom only.
            If mostly vertical then note range zoom only.
Middle button - drag to move view

