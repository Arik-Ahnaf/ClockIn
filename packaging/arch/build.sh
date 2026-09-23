#!/usr/bin/env bash
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$project_root"
uv sync --locked --group build
uv run --no-sync python build.py
uv run --no-sync python scripts/verify_distribution.py
# Creates a pacman package without installing it. Run as your regular user.
cd dist/arch
makepkg --force --clean
