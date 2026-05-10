## Project Details

This is a python library that focuses on providing the tools necessary to build audio games. It includes modules for handling state management, audio playback, user input, and game logic specific to audio-based interactions. The only output is through sounds and screen readers, making it accessible for visually impaired users.

### Technical Details

This project uses python 3.13 and follows standard python coding conventions. It leverages libraries such as pyglet for input management, and Open AL for audio playback. The project is structured into several modules, each responsible for a specific aspect of audio game development, such as UI and state management, audio processing, and map handling.

### Coding Style

- Follow PEP 8 guidelines for Python code style.
- use comments  sparingly
- Use descriptive variable and function names to enhance code readability.
- Include docstrings for all public classes and methods to explain their purpose and usage.

### Testing

This project uses pytest for unit testing. Ensure that all new features and bug fixes are accompanied by appropriate test cases to maintain code quality and reliability. Keep project test coverage above 90%.

### Pre-commit Hooks

The project uses pre-commit hooks to enforce code quality and style guidelines. Ensure that all commits pass the pre-commit checks before pushing changes to the repository. The hooks used are mypy for type checking, black for code formatting, and flake8 for linting. Always check mypy and flake8 after making changes to the codebase.