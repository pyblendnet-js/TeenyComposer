# Teeny Composer
![Teeny Composer screenshot](/teeny-composer.png)

## About
Teeny Composer is a simple midi file editor for creation or editing of simple tunes.

## Features V0.1

- shows notes as bars either on stave or piano view
- addition and deletion of notes or tracks
- variable speed playback using fluidsynth and sound font (currently only GeneralUser-GS.sf2)
- transposition by track or by selection
- tracks can be independantly saved and loaded to a simple text based format
- delete notes by selection
- cut, copy, and paste selection using cntrl+X, cntrl+C and cntrl+V 
- undo and redo using cntrl+Z and cntrl+Y
- cntrl+left button drag for multi selection
- shift+left button drag for multi unselection
- click on piano area to play notes

## Installation

Locate everything in a folder. Assuming you have python3 installed, then for the first time, run python3 TeenyComposer.py from a terminal and you'll see what dependancy packages are missing. Use pip to install.

The fluidsynth runtime can be installed using apt-get on linux, but is also available on Windows and Mac.
On windows, you need to locate the bin directory from the downloaded zip in C:/tool/fluidsynth

Download GeneralUser-GS.sf2 from one of the many sources and locate in the same folder.
The GeneralUser-GS.txt file is a list of that soundfonts contents with bank and numbers.
I got my sf2 file from https://github.com/mrbumpy409/GeneralUser-GS

Alternative sound fonts could be used but for this version requires changes in the program.
Modity and use list-sf2-instruments.sh to create your own list of the sound font contents.

### Dependancies

- python3
- tkinter (usually included with python)
- mido (to load and save midifiles but then not used internally)
- pyfluidsynth and fluidsynth (only needed if using playback) 

## Mouse click and drag behaviour

Left button
- drag right on canvas to add or modify note
- drag left over note to delete
- single click to locate playback cursor

Right button
- drag right to indicate area to zoom.
- drag horizontal for time zoom only.
- drag vertically for note range zoom.

Middle button
- drag to move view
- click to set time cursor
- cntrl+click to set begin time
- cntrl+click to set fini time

## Keyboard behaviour
- cntrl+H to print edit history to console
- cntrl+S to print selection to console
- cntrl+T to print track to console
- delete key for delete selection

