# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changed

- Updated docs dependency pins from `mkdocstrings[python]==0.26.1` to
  `mkdocstrings==1.0.4` and `mkdocstrings-python==2.0.3` in
  `requirements-dev.txt` and docs optional dependencies in `pyproject.toml`.

### Fixed

- Removed MkDocs build deprecation warnings related to deprecated
  `mkdocs_autorefs` import paths by upgrading the mkdocstrings toolchain.
- Verified docs build is clean with `mkdocs build` (no deprecation warnings).
