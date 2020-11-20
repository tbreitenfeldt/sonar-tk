from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / 'readme.md').read_text(encoding='utf-8')

setup(
    name='audio_ui', 
    version='1.0',
    description='A library for creating screen reader only user interfaces.',
    url='https://github.com/tbreitenfeldt/audio_ui',
    author='Timothy Breitenfeldt',
    author_email='timothyjb310@gmail.com',
    classifiers=[
        'Development Status :: Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9'
    ],
    keywords='development, accessibility, screen reader, audio, UI',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),  # Required
    python_requires='>=3.8',
    install_requires=['accessible_output2', 'pyglet', 'pyperclip'],
    project_urls={  # Optional
        'Bug Reports': 'https://github.com/tbreitenfeldt/audio_ui/issues',
        'Source': 'https://github.com/tbreitenfeldt/audio_ui',
    },
)
