from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import time

from .base import Camera


class WatchedFolderCamera(Camera):
    """
    Wait for an image to land in a hot folder, then copy it into the pipeline.

    This is intended for EOS Utility workflows where Canon software performs the
    actual capture and download, and our code simply waits for the new file.
    """

    def __init__(
        self,
        incoming_dir: str | Path,
        trigger_command_template: str = "",
        timeout_s: float = 30.0,
        stability_ms: int = 500,
        watch_extensions: str = ".jpg,.jpeg,.png,.tif,.tiff",
    ) -> None:
        self.incoming_dir = Path(incoming_dir)
        self.trigger_command_template = trigger_command_template.strip()
        self.timeout_s = timeout_s
        self.stability_ms = stability_ms
        self.extensions = {
            extension.lower().strip()
            for extension in watch_extensions.split(",")
            if extension.strip()
        }
        self._seen_paths = {path.resolve() for path in self._list_candidate_files()}

    def _list_candidate_files(self) -> list[Path]:
        if not self.incoming_dir.exists():
            return []
        return [
            path
            for path in self.incoming_dir.iterdir()
            if path.is_file() and (not self.extensions or path.suffix.lower() in self.extensions)
        ]

    def _run_trigger(self, output_path: Path) -> None:
        if not self.trigger_command_template:
            return
        command = self.trigger_command_template.format(output=str(output_path), incoming=str(self.incoming_dir))
        result = subprocess.run(command, capture_output=True, text=True, shell=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "Watched-folder trigger command failed.")

    def _wait_for_stable_new_file(self, start_time: float) -> Path:
        deadline = time.time() + self.timeout_s
        while time.time() < deadline:
            candidates = sorted(self._list_candidate_files(), key=lambda path: path.stat().st_mtime)
            for candidate in candidates:
                resolved = candidate.resolve()
                if resolved in self._seen_paths:
                    continue
                stat_before = candidate.stat()
                if stat_before.st_mtime < start_time:
                    self._seen_paths.add(resolved)
                    continue
                time.sleep(max(self.stability_ms, 0) / 1000.0)
                stat_after = candidate.stat()
                if (
                    stat_before.st_size == stat_after.st_size
                    and stat_before.st_mtime == stat_after.st_mtime
                ):
                    self._seen_paths.add(resolved)
                    return candidate
            time.sleep(0.1)
        raise TimeoutError(
            f"No new image arrived in {self.incoming_dir} within {self.timeout_s:.1f} seconds."
        )

    def capture(self, output_path: str | Path) -> Path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        start_time = time.time()
        self._run_trigger(output)
        source = self._wait_for_stable_new_file(start_time)
        shutil.copy2(source, output)
        return output
