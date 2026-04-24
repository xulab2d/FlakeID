import time
import unittest
from pathlib import Path

from flake_ml.acquisition.watch import WatchedFolderCamera


class WatchedFolderCameraTests(unittest.TestCase):
    def test_capture_copies_new_file_from_incoming_dir(self) -> None:
        workspace_temp = Path.cwd() / "outputs" / "test_temp" / "watch_camera"
        incoming = workspace_temp / "incoming"
        output = workspace_temp / "captured" / "tile.jpg"
        incoming.mkdir(parents=True, exist_ok=True)
        if output.exists():
            output.unlink()

        source = incoming / "source.jpg"
        if source.exists():
            source.unlink()
        trigger = (
            "powershell.exe -NoProfile -Command "
            "\"[System.IO.File]::WriteAllBytes('{incoming}\\\\source.jpg',[byte[]](116,101,115,116,45,105,109,97,103,101))\""
        )
        camera = WatchedFolderCamera(
            incoming_dir=incoming,
            trigger_command_template=trigger,
            timeout_s=2.0,
            stability_ms=10,
        )

        captured = camera.capture(output)
        self.assertEqual(captured, output)
        self.assertTrue(output.exists())
        self.assertEqual(output.read_bytes(), b"test-image")


if __name__ == "__main__":
    unittest.main()
