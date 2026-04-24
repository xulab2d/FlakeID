from __future__ import annotations

from pathlib import Path
import subprocess

from .base import Camera


class CanonSdkCamera(Camera):
    def __init__(self, helper_script: str | Path, timeout_s: float = 45.0) -> None:
        self.helper_script = Path(helper_script)
        self.timeout_s = timeout_s

    def capture(self, output_path: str | Path) -> Path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(self.helper_script),
                "-Output",
                str(output),
                "-TimeoutSeconds",
                f"{self.timeout_s:.3f}",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Canon SDK capture failed.")
        if not output.exists():
            raise FileNotFoundError(f"Canon SDK capture completed but did not create {output}")
        return output
