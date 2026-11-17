"""Gradio adapter for the interface-neutral silent-speech service."""

import time
import traceback
from collections.abc import Callable, Iterator

import gradio as gr

from python_api.core import RuntimeConfig, SilentSpeechService


TIPS = """
### Tips for best accuracy
- **Bright light on your face** (face a window or lamp — not backlit)
- **Look at the camera**, face filling the frame, roughly eye-level
- **Articulate a little more deliberately** than normal
- Leave a **~1 second pause between sentences**; keep each sentence ≥ ~1s
- It reads **lips only** — sound is never used
"""


def format_transcription(output):
    """Convert a core transcription result into Gradio textbox values."""

    if not output.get("segments"):
        return (
            "No face / no speech detected. Try better lighting and face the "
            "camera.",
            "",
        )

    lines = []
    for segment in output["segments"]:
        if not segment["text"]:
            continue
        start, end = segment["seg_time"]
        lines.append(f"[{start:4.1f}–{end:4.1f}s]  {segment['text']}")

    transcript = output.get("transcript", "").strip() or "(nothing recognized)"
    return transcript, "\n".join(lines)


STATUS_IDLE = "⚪ **Waiting for a video.** Record or upload a clip to start."
STATUS_RUNNING = (
    "⏳ **Reading lips…** The first run also downloads the model, so it can "
    "take a minute."
)
STATUS_NO_SPEECH = "⚠️ **No face or speech detected.** Try better lighting and face the camera."
STATUS_FAILED = "❌ **Inference failed.** Details are in the transcript box."

Outputs = tuple[str, str, str]


def create_handler(
    service: SilentSpeechService,
) -> Callable[[str | None, bool], Iterator[Outputs]]:
    """Create a UI callback around any compatible core service.

    The callback is a generator yielding ``(status, transcript, breakdown)`` so
    the status bar updates as soon as inference starts and again when it ends.
    """

    def handle(video, flip):
        if not video:
            yield STATUS_IDLE, "", ""
            return
        yield STATUS_RUNNING, "", ""
        started = time.perf_counter()
        try:
            output = service.transcribe(video, nbest=5, hflip=bool(flip))
        except Exception:
            yield STATUS_FAILED, f"Error:\n{traceback.format_exc()}", ""
            return
        if not output.get("segments"):
            yield STATUS_NO_SPEECH, *format_transcription(output)
            return
        elapsed = time.perf_counter() - started
        yield (
            f"✅ **Done** in {elapsed:.1f}s.",
            *format_transcription(output),
        )

    return handle


default_service = SilentSpeechService(RuntimeConfig.from_env())
run = create_handler(default_service)


def build_app(service: SilentSpeechService | None = None) -> gr.Blocks:
    """Build the Gradio UI without forcing the model to load."""

    handler = run if service is None else create_handler(service)
    with gr.Blocks(title="Silent Lip Reader") as interface:
        gr.Markdown(
            "# 👄 Silent Lip Reader\n"
            "Record yourself (or upload) — it reads your **lips only**, "
            "no sound used, and writes what you said."
        )
        with gr.Row():
            with gr.Column():
                video = gr.Video(
                    sources=["webcam", "upload"],
                    label="Record (webcam) or upload a clip",
                )
                flip = gr.Checkbox(
                    value=False,
                    label=(
                        "Flip horizontally — only tick if the transcript comes "
                        "out as gibberish (some setups mirror the video)"
                    ),
                )
                gr.Markdown(TIPS)
            with gr.Column():
                status = gr.Markdown(STATUS_IDLE, container=True)
                transcript = gr.Textbox(label="Transcript (lip-read)", lines=4)
                breakdown = gr.Textbox(
                    label="Per-utterance breakdown",
                    lines=10,
                )

        # Inference starts only once a recording or upload has finished and
        # the file is on the server, so there is nothing to click too early.
        # Toggling the flip box re-runs the current clip. "always_last" drops
        # stale queued runs when the input changes again mid-inference.
        for trigger, api_name, api_visibility in (
            (video.change, "transcribe", "public"),
            (flip.change, "transcribe_on_flip", "undocumented"),
        ):
            trigger(
                handler,
                inputs=[video, flip],
                outputs=[status, transcript, breakdown],
                api_name=api_name,
                api_visibility=api_visibility,
                show_progress="minimal",
                show_progress_on=[status],
                trigger_mode="always_last",
            )
    return interface


demo = build_app()


def main():
    demo.launch(server_name="0.0.0.0", server_port=7860)


if __name__ == "__main__":
    main()
