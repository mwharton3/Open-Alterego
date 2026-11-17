#!/usr/bin/env bash
# Create the uv environment with the right PyTorch build for this machine.
#
#   scripts/setup.sh                      # auto-detect, install gradio + http
#   scripts/setup.sh --backend cpu        # force the CPU build
#   scripts/setup.sh --extras gradio      # choose interface extras
#   OPEN_ALTERGO_TORCH_BACKEND=cu124 scripts/setup.sh
#
# Detection: an NVIDIA driver (nvidia-smi) selects the CUDA 12.4 build on
# Linux/Windows; everything else gets the CPU build. At runtime the default
# LIPREAD_DEVICE=auto uses CUDA when available and the CPU otherwise.
set -euo pipefail

cd "$(dirname "$0")/.."

backend="${OPEN_ALTERGO_TORCH_BACKEND:-auto}"
extras="gradio http"
min_cuda_driver=525  # CUDA 12.x minor-version compatibility floor

usage() { sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --backend) backend="$2"; shift 2 ;;
    --extras) extras="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is not installed. Install it with:" >&2
  echo "  curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 1
fi

os="$(uname -s)"
arch="$(uname -m)"

if [[ "$os" == "Darwin" ]]; then
  if [[ "$arch" != "arm64" && "$(sysctl -n sysctl.proc_translated 2>/dev/null || echo 0)" != "1" ]]; then
    echo "Intel Macs are not supported: PyTorch 2.6 ships no x86_64 macOS wheels." >&2
    exit 1
  fi
  # Never pick up an x86_64 (Rosetta) interpreter on Apple Silicon.
  export UV_PYTHON="${UV_PYTHON:-cpython-3.11-macos-aarch64}"
fi

if [[ "$backend" == "auto" ]]; then
  backend="cpu"
  if [[ "$os" != "Darwin" ]] && command -v nvidia-smi >/dev/null 2>&1; then
    driver="$(nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null | head -n1 || true)"
    gpu="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -n1 || true)"
    if [[ -n "$driver" ]]; then
      if (( ${driver%%.*} >= min_cuda_driver )); then
        backend="cu124"
        echo "Detected NVIDIA GPU: ${gpu} (driver ${driver})"
      else
        echo "NVIDIA driver ${driver} is older than ${min_cuda_driver}; using the CPU build." >&2
      fi
    fi
  fi
  if [[ "$backend" == "cpu" ]]; then
    if [[ "$os" == "Darwin" ]]; then
      echo "Detected Apple Silicon: installing the standard macOS PyTorch build (CPU inference)."
    else
      echo "No usable NVIDIA GPU detected: installing the CPU build."
    fi
  fi
fi

case "$backend" in
  cpu|cu124) ;;
  *) echo "Unsupported backend '$backend' (expected cpu or cu124)." >&2; exit 2 ;;
esac

args=(--extra "$backend")
for extra in $extras; do
  args+=(--extra "$extra")
done

echo "+ uv sync ${args[*]}"
uv sync "${args[@]}"

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "Warning: ffmpeg was not found on PATH; install it before running inference." >&2
fi

uv run python - <<'EOF'
import torch

from python_api.core.config import resolve_device

print(f"torch {torch.__version__}; inference device: {resolve_device('auto')}")
EOF
