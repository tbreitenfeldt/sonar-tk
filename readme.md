# Sonar TK

A python library for creating audio games. There are 3 separate modules: UI, map building, and sound. These components are brought together in an opinionated module called world. All of these modules are designed to work together, or stand alone.

A utils package is included which provides various useful tools for building games, or other accessible screen reader only user interfaces, such as a speech util that is a wrapper for accessible_output2, state machine classes, and a key manager for wrapping the keyboard behavior of pyglet.

## Installation

sonartk is published on pypi, and can be installed using pip:

```
pip3 install sonartk
```

## Supported Python Versions

This library has been tested using python 3.11.

## Dependencies

audio_ui depends on a few dependencies for use. These dependencies are listed below:

- [pyglet] (https://pypi.org/project/pyglet/)
- [accessible_output2] (https://pypi.org/project/accessible-output2/)
- [pyperclip] (https://pypi.org/project/pyperclip/)
- [pyogg] (https://pypi.org/project/PyOgg/)

## Core Modules

- ui - use to create a window, provide key handling, and a game loop.
- map-builder - used for reading in maps, and providing helpful methods for traversing the map such as methods for returning near by map object, and path finding.
- sound - wraps open-al using a python wrapper open-al-light

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
