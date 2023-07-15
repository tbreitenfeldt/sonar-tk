from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / 'readme.md').read_text(encoding='utf-8')

setup(
    name='audio_ui', 
    version='0.1.1',
    description='A library for creating screen reader only user interfaces using Pyglet.',
    url='https://github.com/tbreitenfeldt/audio_ui',
    author='Timothy Breitenfeldt',
    author_email='timothyjb310@gmail.com',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11'
    ],
    keywords='development, accessibility, screen reader, audio, UI',
    package_dir={'': 'audio_ui'},
    packages=find_packages(where='audio_ui'),  # Required
    python_requires='>=3.10',
    install_requires=['accessible_output2', 'pyglet', 'pyperclip'],
    project_urls={  # Optional
        'Bug Reports': 'https://github.com/tbreitenfeldt/audio_ui/issues',
        'Source': 'https://github.com/tbreitenfeldt/audio_ui',
    },
)
