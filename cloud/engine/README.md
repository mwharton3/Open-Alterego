# Open-Altergo engine

This installable package owns the Auto-AVSR model, preprocessing, decoding, and
training primitives. Applications and training workflows depend on it; it does
not depend on Gradio or Modal.

From the repository root:

```bash
scripts/setup.sh --extras ""
uv run python -m open_altergo_engine.local_infer sample.mp4
```

The engine is a uv workspace member. Its PyTorch stack (`torch`,
`torchvision`, `torchaudio`, `pytorch-lightning`) is supplied by the root
project's `cpu`/`cu124` extras so each machine gets the right build.

Download the pinned, checksum-verified model bundle explicitly:

```bash
uv run python -m open_altergo_engine.model_assets download \
  --local-dir ./models/silent-lip-reader
```

The same verification runs automatically before the default checkpoint or
tokenizer is loaded.
