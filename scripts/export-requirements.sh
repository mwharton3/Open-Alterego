#!/usr/bin/env bash
# Regenerate requirements.txt from uv.lock for Hugging Face Spaces, which
# installs with pip and runs on CPU. Run after any dependency change:
#
#   scripts/export-requirements.sh
#
# Local development should use uv (scripts/setup.sh), not this file.
set -euo pipefail
cd "$(dirname "$0")/.."

{
  echo "# Hugging Face Spaces install list (CPU torch + Gradio)."
  echo "# GENERATED from uv.lock by scripts/export-requirements.sh; do not edit."
  uv export --frozen --no-header --no-dev --no-hashes --emit-index-url \
    --extra cpu --extra gradio \
    | grep -v -e 'download.pytorch.org/whl/cu124' -e 'download.pytorch.org/whl/cu128'
} > requirements.txt
echo "Wrote requirements.txt"
