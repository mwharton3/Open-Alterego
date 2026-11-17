# Modal provisioning

`app.py` builds the runtime image, mounts persistent Volumes, and invokes the
provider-independent commands in `training/`.

The Modal client is in the `modal` dependency group. Run with credentials
injected by Doppler:

```bash
doppler run -- uv run --group modal modal run cloud/modal/app.py::prepare --dataset-name my-speaker
```

See [the complete guide](../../docs/modal-finetuning.md). No Modal or Doppler
credentials belong in this directory.
