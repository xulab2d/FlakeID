from __future__ import annotations

from pathlib import Path
import re
import subprocess
import time

from ..models import StagePosition
from .base import MotionController


class PowerShellGrblController(MotionController):
    def __init__(
        self,
        port: str,
        baud: int = 115200,
        travel_rate_um_s: float = 2500.0,
        settle_time_ms: int = 250,
    ) -> None:
        self.port = port
        self.baud = baud
        self.travel_rate_um_s = travel_rate_um_s
        self.settle_time_ms = settle_time_ms
        self._position = StagePosition(0.0, 0.0)

    @property
    def script_path(self) -> Path:
        return Path(__file__).resolve().parents[3] / "scripts" / "grbl_send.ps1"

    def _send(self, *commands: str, wait_for: str = "ok", timeout_ms: int = 2000) -> str:
        command = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(self.script_path),
            "-Port",
            self.port,
            "-Baud",
            str(self.baud),
            "-TimeoutMs",
            str(timeout_ms),
            "-WaitFor",
            wait_for,
        ]
        for line in commands:
            command.extend(["-Command", line])
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "Failed to communicate with GRBL.")
        return result.stdout.strip()

    def unlock(self) -> str:
        return self._send("$X")

    def home(self) -> None:
        self._send("$H", wait_for="ok", timeout_ms=10000)
        self._position = StagePosition(0.0, 0.0)

    def move_abs(self, x_um: float, y_um: float) -> None:
        x_mm = x_um / 1000.0
        y_mm = y_um / 1000.0
        feed_mm_min = max((self.travel_rate_um_s * 60.0) / 1000.0, 0.1)
        self._send("G21", "G90", f"G1 X{x_mm:.4f} Y{y_mm:.4f} F{feed_mm_min:.2f}")
        self._position = StagePosition(float(x_um), float(y_um))
        self.wait_for_idle()

    def move_rel(self, dx_um: float, dy_um: float) -> None:
        new_x = self._position.x_um + dx_um
        new_y = self._position.y_um + dy_um
        self.move_abs(new_x, new_y)

    def status(self) -> str:
        return self._send("?", wait_for="<", timeout_ms=1500)

    def wait_for_idle(self) -> None:
        deadline = time.time() + 20.0
        while time.time() < deadline:
            response = self.status()
            if "Idle" in response:
                time.sleep(self.settle_time_ms / 1000.0)
                return
            time.sleep(0.1)
        raise TimeoutError("GRBL did not return to Idle before timeout.")

    def current_position(self) -> StagePosition:
        response = self.status()
        match = re.search(r"MPos:([-\d.]+),([-\d.]+)", response)
        if match:
            return StagePosition(float(match.group(1)) * 1000.0, float(match.group(2)) * 1000.0)
        return self._position
