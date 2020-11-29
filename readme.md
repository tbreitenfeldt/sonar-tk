# Audio UI

A python library for creating accessible screen reader only user interfaces using pyglet and accessible_output2. You can create a window and add various UI elements such as buttons, checkboxs, edit boxes, etc...

A utils package is included which provides various useful tools for building games, or other accessible screen reader only user interfaces, such as a simple audio wrapper for pyglet, a speech util that is a wrapper for accessible_output2, and a key manager for wrapping the keyboard behavior of pyglet.

## Installation

Audio_ui is published on pypi, and can be installed using pip:

```
pip3 install audio_ui
```

## Supported Python Versions

This library has been tested using python 3.8.6, although should work on earlier versions of python 3.8, as well as python 3.9.

## Dependencies

audio_ui depends on a few dependencies for use. These dependencies are listed below:

- [pyglet] (https://pypi.org/project/pyglet/)
- [accessible_output2] (https://pypi.org/project/accessible-output2/)
- [pyperclip] (https://pypi.org/project/pyperclip/)

## Core Modules

The core modules for audio_ui are the window, state_machine, state, and everything in the utils package, including: speech_manager, audio_manager, and key_handler. You can use audio_ui without using any of the UI elements found in the elements package. The screens package contains the container for holding UI elements as well as a dialog module.

## Installing Source

First clone the repository from:

[https://github.com/tbreitenfeldt/audio_ui] (https://github.com/tbreitenfeldt/audio_ui)

then install the dependencies with pip:

```
pip install -r requirements.txt
```

Run the tests using
[nose2] (https://pypi.org/project/nose2/).
First install nose2 using pip:

```
pip install nose2
```

Then run the tests from the main directory by running:

```
nose2
```
