from __future__ import annotations

import re
import time

from ..models import StagePosition
from .base import MotionController

try:
    import serial  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    serial = None


class PySerialGrblController(MotionController):
    """
    Persistent GRBL controller intended for real scan-time use.

    Unlike one-shot PowerShell probes, this class keeps the serial port open so
    the Arduino is not reset before every move.
    """

    def __init__(
        self,
        port: str,
        baud: int = 115200,
        travel_rate_um_s: float = 2500.0,
        settle_time_ms: int = 250,
        startup_delay_s: float = 2.0,
        read_timeout_s: float = 0.25,
    ) -> None:
        if serial is None:
            raise RuntimeError(
                "pyserial is not installed. Install it before using the persistent GRBL controller."
            )

        self.port = port
        self.baud = baud
        self.travel_rate_um_s = travel_rate_um_s
        self.settle_time_ms = settle_time_ms
        self._position = StagePosition(0.0, 0.0)
        self._serial = serial.Serial(port=self.port, baudrate=self.baud, timeout=read_timeout_s, write_timeout=1.0)
        time.sleep(startup_delay_s)
        self._serial.reset_input_buffer()
        self._serial.reset_output_buffer()

    def close(self) -> None:
        if getattr(self, "_serial", None) is not None and self._serial.is_open:
            self._serial.close()

    def __enter__(self) -> "PySerialGrblController":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def _write_line(self, line: str) -> None:
        self._serial.write((line + "\n").encode("ascii"))
        self._serial.flush()

    def _read_until(self, expected: str, timeout_s: float = 5.0) -> str:
        deadline = time.time() + timeout_s
        buffer = []
        while time.time() < deadline:
            chunk = self._serial.readline().decode("ascii", errors="ignore").strip()
            if chunk:
                buffer.append(chunk)
                if expected in chunk:
                    return "\n".join(buffer)
            time.sleep(0.02)
        raise TimeoutError(f"Did not receive expected GRBL response containing {expected!r}.")

    def _query_status(self) -> str:
        deadline = time.time() + 2.0
        while time.time() < deadline:
            self._serial.write(b"?")
            self._serial.flush()
            chunk = self._serial.readline().decode("ascii", errors="ignore").strip()
            if chunk.startswith("<") and ">" in chunk:
                return chunk
            time.sleep(0.05)
        raise TimeoutError("No GRBL status response received.")

    def unlock(self) -> str:
        self._write_line("$X")
        return self._read_until("ok")

    def home(self) -> None:
        self._write_line("$H")
        self._read_until("ok", timeout_s=20.0)
        self._position = StagePosition(0.0, 0.0)

    def move_abs(self, x_um: float, y_um: float) -> None:
        self._write_line("G21")
        self._read_until("ok")
        self._write_line("G90")
        self._read_until("ok")
        x_mm = x_um / 1000.0
        y_mm = y_um / 1000.0
        feed_mm_min = max((self.travel_rate_um_s * 60.0) / 1000.0, 0.1)
        self._write_line(f"G1 X{x_mm:.4f} Y{y_mm:.4f} F{feed_mm_min:.2f}")
        self._read_until("ok")
        self.wait_for_idle()
        self._position = StagePosition(float(x_um), float(y_um))

    def wait_for_idle(self) -> None:
        deadline = time.time() + 20.0
        while time.time() < deadline:
            response = self._query_status()
            if "Idle" in response:
                time.sleep(self.settle_time_ms / 1000.0)
                return
            time.sleep(0.05)
        raise TimeoutError("GRBL did not return to Idle before timeout.")

    def current_position(self) -> StagePosition:
        response = self._query_status()
        match = re.search(r"MPos:([-\d.]+),([-\d.]+)", response)
        if match:
            self._position = StagePosition(float(match.group(1)) * 1000.0, float(match.group(2)) * 1000.0)
        return self._position
