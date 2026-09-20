# AGENTS.md

Tiny Python CLI package scaffolded with `uv` (v0.1.0, hello-world placeholder). No dependencies, tests, CI, or linters configured yet.

## Repo layout quirk

The git/project root is nested one level below the opened folder: all files live in `Sotooh/Sotooh/` (OneDrive double-nesting). Run git/uv commands from that subdirectory; the parent `Sotooh/` is not the repo and `git` will fail there.

## Toolchain

- Managed with [uv](https://docs.astral.sh/uv), Python 3.11 (`requires-python = ">=3.11"`, `.python-version` = 3.11).
- Build backend: `uv_build`. Package via `uv build`.
- Standard src-layout: code lives in `src/sotooh/`.

## Commands

- Sync env: `uv sync`
- Run the CLI: `uv run sotooh` (entrypoint `sotooh:main` in `src/sotooh/__init__.py`)

Remote is `origin` → `https://github.com/vmzhelifonov-hub/Sotooh.git`, branch `master`.