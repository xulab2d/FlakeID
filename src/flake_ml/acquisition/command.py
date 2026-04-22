from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

from .base import Camera


class ExternalCommandCamera(Camera):
    def __init__(self, command_template: str) -> None:
        self.command_template = command_template

    def capture(self, output_path: str | Path) -> Path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        command = self.command_template.format(output=str(output))
        result = subprocess.run(command, capture_output=True, text=True, shell=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "External capture command failed.")
        if not output.exists():
            raise FileNotFoundError(f"Capture command completed but did not create {output}")
        return output


class DirectoryReplayCamera(Camera):
    def __init__(self, image_dir: str | Path) -> None:
        image_root = Path(image_dir)
        self.images = sorted(
            path for path in image_root.iterdir() if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
        )
        self.index = 0

    def capture(self, output_path: str | Path) -> Path:
        if self.index >= len(self.images):
            raise StopIteration("No more images available in replay directory.")
        source = self.images[self.index]
        self.index += 1
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, output)
        return output

