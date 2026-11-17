# Python API

This package exposes the in-process `RuntimeConfig` and
`SilentSpeechService`. Gradio and the HTTP API call it directly. It
intentionally has no dependency on either interface.

It is a uv workspace member, installed editable by `scripts/setup.sh` from
the repository root (see the root README). `RuntimeConfig.device` defaults to
`auto`: CUDA when available, otherwise CPU.
