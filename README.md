---
title: Open Altergo
emoji: 👄
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: 6.15.2
python_version: "3.11"
app_file: app.py
pinned: false
license: mit
short_description: Extensible silent-speech inference and personalization
tags:
  - lip-reading
  - visual-speech-recognition
  - silent-speech
  - gradio
---

# Open-Altergo

Open-Altergo is an extensible silent-speech system: it reads visible mouth
movement from video, returns text, and can be personalized to a speaker. The
repository separates the reusable API, model engine, interfaces, training
workflows, and cloud provisioning so future Swift, HTTP, or desktop interfaces
do not depend on Gradio.

Audio is stripped before inference. The current model is Auto-AVSR and the
current browser interface is Gradio.

## Repository map

```text
apps/
├── gradio/                    Gradio UI and its dependencies
└── apple/                     Planned macOS and iOS consumption clients
apis/
├── python_api/                Direct, in-process Python interface
└── http_api/                  Network interface for Swift and other clients
training/                      Dataset preparation and fine-tuning commands
pretraining/                   Pinned external pretraining/model sources
cloud/
├── engine/                    Installable Auto-AVSR engine package
└── modal/                     Modal provisioning and job definitions
docs/
├── interface-architecture.md
├── modal-finetuning.md
├── RESEARCH_LOG.md
└── Silent-Lip-Reader-README.md
scripts/                       setup.sh (GPU-aware install), export-requirements.sh
app.py                         Hugging Face compatibility launcher
requirements.txt               Generated from uv.lock for Hugging Face Spaces
```

The dependency direction is deliberate:

```text
Gradio ───────────────────────► Python API ──► engine
Swift / remote clients ─HTTP─► HTTP API ─────► Python API
training workflows ──────────────────────────► engine
Modal ───────────────────────► training workflows
```

The native iOS architecture, test matrix, Claude Code execution loop, and
TestFlight plan live in [apps/apple](apps/apple/README.md).

## Install

Prerequisites: [uv](https://docs.astral.sh/uv/) and `ffmpeg`
(`brew install ffmpeg` or `apt install ffmpeg libgl1 libglib2.0-0`). Supported
platforms are Linux, Windows, and Apple Silicon macOS; PyTorch 2.6 has no
Intel-macOS wheels.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # if uv is not installed
scripts/setup.sh
```

`scripts/setup.sh` creates `.venv` with Python 3.11 from `uv.lock` and picks
the PyTorch build for the machine:

| Machine | PyTorch build | Inference device |
| --- | --- | --- |
| Linux/Windows with an NVIDIA driver ≥ 525 | `cu124` (CUDA 12.4) | `cuda` |
| Linux/Windows without one | `cpu` | `cpu` |
| Apple Silicon Mac | `cpu` (standard macOS wheel) | `cpu` |

It installs the `gradio` and `http` interfaces by default and finishes by
printing the device inference will use. Override the choices with
`scripts/setup.sh --backend cpu|cu124 --extras "gradio http"`, or run uv
directly, always naming exactly one backend extra:

```bash
uv sync --extra cu124 --extra gradio --extra http
```

`uv run …` never changes the installed PyTorch build, but a bare `uv sync`
removes it along with every extra not named; re-run `scripts/setup.sh` after
pulling dependency changes.

At runtime `LIPREAD_DEVICE` defaults to `auto`, which uses CUDA when it is
available and the CPU otherwise. Set it to `cpu`, `cuda`, or `cuda:N` to
override. Apple `mps` is not auto-selected: it needs
`PYTORCH_ENABLE_MPS_FALLBACK=1` and measured about 2x slower than the CPU for
this model.

## Run the Gradio application

```bash
uv run python app.py
```

Record or upload a clip and inference starts as soon as the video reaches the
server; the status bar above the transcript reports progress. The first
inference downloads the public Auto-AVSR checkpoint if no local checkpoint is
configured.

## Use the core without Gradio

```bash
scripts/setup.sh --extras ""
```

```python
from python_api import RuntimeConfig, SilentSpeechService

service = SilentSpeechService(RuntimeConfig())  # device="auto"
result = service.transcribe("sample.mp4")
print(result["transcript"])
```

Set `LIPREAD_CKPT` to use a personalized checkpoint.

## Run the HTTP API

```bash
uv run uvicorn apis.http_api.app:app --host 0.0.0.0 --port 8000
```

The HTTP API lets Swift and other non-Python clients upload a video to
`POST /v1/transcriptions`. It wraps the same Python API used by Gradio.

## Model assets

The Auto-AVSR checkpoint and tokenizer remain on Hugging Face rather than Git
LFS. The engine packages a central manifest with the repository, immutable
revision, expected sizes, SHA-256 checksums, provenance, and license.

Download and verify the complete bundle:

```bash
uv run python -m open_altergo_engine.model_assets download \
  --local-dir ./models/silent-lip-reader
```

See [model assets](docs/model-assets.md) for exact hashes and provenance.

## Train on generic compute

The training code is not tied to Modal. On a machine with a CUDA GPU:

```bash
uv run python training/prepare_dataset.py \
  --manifest datasets/me/manifest.csv \
  --output-dir datasets/me/processed \
  --dataset-name me

uv run python training/train_personal.py \
  --root-dir datasets/me/processed \
  --output-dir runs/me-v1 \
  --train-file me_train.csv \
  --val-file me_val.csv
```

See [Modal fine-tuning](docs/modal-finetuning.md) for provisioned A10 training,
persistent checkpoints, and Doppler-based secret injection.

## Tests

```bash
uv run python -m unittest discover -s tests -t .
```

## Dependency management

`pyproject.toml` and `uv.lock` are the source of truth. The root project is a
uv workspace whose members are `cloud/engine` and `apis/python_api`. Add or
change dependencies with `uv add` / `uv lock`, then regenerate the pip-format
`requirements.txt` used by Hugging Face Spaces (CPU + Gradio):

```bash
scripts/export-requirements.sh
```

## External pretraining sources

Candidate upstream model repositories live under `pretraining/` as metadata and
download tooling. Large weights remain on their original host and are fetched
at an immutable revision into an ignored local cache. See
[pretraining](pretraining/README.md).

## Status and provenance

The repository contains a complete preprocessing and personalized fine-tuning
workflow, but it does not yet include a project-specific Modal run log or
evaluated personalized checkpoint. Treat personalized quality claims as
unverified until held-out WER is recorded.

The original demo, pipeline work, evaluation, and research were created by
[Ahmet Dedeler](https://ahmetdedeler.com) around the open Auto-AVSR model.
See the archived [Silent Lip Reader README](docs/Silent-Lip-Reader-README.md)
and [research log](docs/RESEARCH_LOG.md) for history, limitations, and credits.

## Security

This is a public repository. Do not commit recordings, datasets, checkpoints,
API keys, Modal credentials, Doppler local state, or `.env` files. Use Doppler
or your compute provider's secret manager to inject credentials at runtime.

MIT licensed.
