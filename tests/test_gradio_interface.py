import os
import unittest

os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")

import gradio as gr

from apps.gradio import app as gradio_app


def tearDownModule():
    gradio_app.demo.close()


class FakeService:
    def __init__(self, output=None, error=None):
        self.output = output
        self.error = error
        self.calls = []

    def transcribe(self, video, **kwargs):
        self.calls.append((video, kwargs))
        if self.error:
            raise self.error
        return self.output


def run_handler(service, video, flip):
    return list(gradio_app.create_handler(service)(video, flip))


class GradioHandlerTests(unittest.TestCase):
    def test_formats_transcript_and_segment_breakdown(self):
        service = FakeService(
            {
                "transcript": "hello world",
                "segments": [
                    {"text": "hello", "seg_time": [0.0, 1.2]},
                    {"text": "world", "seg_time": [1.2, 2.5]},
                ],
            }
        )

        updates = run_handler(service, "clip.mp4", True)

        self.assertEqual(updates[0], (gradio_app.STATUS_RUNNING, "", ""))
        status, transcript, breakdown = updates[-1]
        self.assertIn("Done", status)
        self.assertEqual(transcript, "hello world")
        self.assertIn("[ 0.0– 1.2s]  hello", breakdown)
        self.assertIn("[ 1.2– 2.5s]  world", breakdown)
        self.assertEqual(
            service.calls,
            [("clip.mp4", {"nbest": 5, "hflip": True})],
        )

    def test_missing_video_resets_status_without_calling_core(self):
        service = FakeService({})

        updates = run_handler(service, None, False)

        self.assertEqual(updates, [(gradio_app.STATUS_IDLE, "", "")])
        self.assertEqual(service.calls, [])

    def test_no_segments_returns_actionable_message(self):
        service = FakeService({"transcript": "", "segments": []})

        status, transcript, breakdown = run_handler(service, "clip.mp4", False)[-1]

        self.assertEqual(status, gradio_app.STATUS_NO_SPEECH)
        self.assertIn("No face / no speech detected", transcript)
        self.assertEqual(breakdown, "")

    def test_backend_exception_is_reported_without_crashing_ui(self):
        service = FakeService(error=RuntimeError("backend failed"))

        status, transcript, breakdown = run_handler(service, "clip.mp4", False)[-1]

        self.assertEqual(status, gradio_app.STATUS_FAILED)
        self.assertIn("RuntimeError: backend failed", transcript)
        self.assertEqual(breakdown, "")

    def test_default_model_remains_lazy_after_ui_import(self):
        self.assertIsInstance(gradio_app.demo, gr.Blocks)
        self.assertFalse(gradio_app.default_service.is_loaded)


class GradioLayoutTests(unittest.TestCase):
    def test_no_manual_trigger_button(self):
        buttons = [
            block
            for block in gradio_app.demo.blocks.values()
            if isinstance(block, gr.Button)
        ]
        self.assertEqual(buttons, [])

    def test_video_change_triggers_inference(self):
        video_ids = {
            block_id
            for block_id, block in gradio_app.demo.blocks.items()
            if isinstance(block, gr.Video)
        }
        triggers = {
            (target[0], target[1])
            for dependency in gradio_app.demo.fns.values()
            for target in dependency.targets
        }
        self.assertTrue(
            any((video_id, "change") in triggers for video_id in video_ids)
        )


class CompatibilityLauncherTests(unittest.TestCase):
    def test_root_app_exports_gradio_interface(self):
        import app

        self.assertIs(app.demo, gradio_app.demo)
        self.assertIs(app.run, gradio_app.run)


if __name__ == "__main__":
    unittest.main()
