from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import base64
import re
import subprocess


STATUS_PATTERN = re.compile(
    r"<(?P<state>[^,>]+),MPos:(?P<mx>[-\d.]+),(?P<my>[-\d.]+),(?P<mz>[-\d.]+),WPos:(?P<wx>[-\d.]+),(?P<wy>[-\d.]+),(?P<wz>[-\d.]+)>"
)
SETTING_PATTERN = re.compile(r"^\$(?P<code>\d+)=?(?P<value>[-\d.]+)?", re.MULTILINE)


@dataclass(slots=True)
class GrblStatus:
    state: str
    machine_x_mm: float
    machine_y_mm: float
    machine_z_mm: float
    work_x_mm: float
    work_y_mm: float
    work_z_mm: float
    raw: str


class PowerShellGrblBridge:
    def __init__(self, port: str, baud: int = 115200, startup_delay_ms: int = 500) -> None:
        self.port = port
        self.baud = baud
        self.startup_delay_ms = startup_delay_ms

    @staticmethod
    def _ps_quote(value: str) -> str:
        return "'" + value.replace("'", "''") + "'"

    def _build_inline_command(self, lines: list[str], wait_for: str, timeout_ms: int) -> str:
        encoded_lines = ", ".join(self._ps_quote(line) for line in lines)
        port = self._ps_quote(self.port)
        wait = self._ps_quote(wait_for)
        return (
            f"$lines = @({encoded_lines}); "
            f"$sp = New-Object System.IO.Ports.SerialPort {port},{self.baud},([System.IO.Ports.Parity]::None),8,([System.IO.Ports.StopBits]::One); "
            "$sp.ReadTimeout = 250; "
            "$sp.WriteTimeout = 1000; "
            "$sp.DtrEnable = $false; "
            "$sp.RtsEnable = $false; "
            "$sp.Open(); "
            f"Start-Sleep -Milliseconds {self.startup_delay_ms}; "
            "$flushDeadline = [DateTime]::UtcNow.AddMilliseconds(200); "
            "while([DateTime]::UtcNow -lt $flushDeadline){ $null = $sp.ReadExisting(); Start-Sleep -Milliseconds 20 }; "
            "$responses = New-Object System.Collections.Generic.List[string]; "
            "foreach($line in $lines){ "
            "if($line -eq '?'){ $sp.Write('?') } "
            "elseif($line -eq '!'){ $sp.Write('!') } "
            "elseif($line -eq '~'){ $sp.Write('~') } "
            "elseif($line -eq '__CTRL_X__'){ $sp.Write([char]24) } "
            "else { $sp.Write($line + \"`n\") }; "
            "Start-Sleep -Milliseconds 80 }; "
            f"$waitFor = {wait}; "
            f"$deadline = [DateTime]::UtcNow.AddMilliseconds({timeout_ms}); "
            "while([DateTime]::UtcNow -lt $deadline){ "
            "$chunk = $sp.ReadExisting(); "
            "if($chunk){ "
            "$responses.Add($chunk); "
            "if($waitFor -eq '__NONE__'){ break } "
            "if(($responses.ToArray() -join '').Contains($waitFor)){ break } "
            "} "
            "Start-Sleep -Milliseconds 20 "
            "}; "
            "$text = ($responses.ToArray() -join ''); "
            "$sp.Close(); "
            "Write-Output $text"
        )

    @property
    def script_path(self) -> Path:
        return Path(__file__).resolve().parents[3] / "scripts" / "grbl_send.ps1"

    def _run_script_line(self, line: str, wait_for: str, timeout_ms: int) -> str:
        command_base64 = base64.b64encode(line.encode("utf-8")).decode("ascii")
        wait_for_base64 = base64.b64encode(wait_for.encode("utf-8")).decode("ascii")
        result = subprocess.run(
            [
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
                "-StartupDelayMs",
                str(self.startup_delay_ms),
                "-CommandBase64",
                command_base64,
                "-WaitForBase64",
                wait_for_base64,
                "-TimeoutMs",
                str(timeout_ms),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "PowerShell GRBL script command failed.")
        return result.stdout.strip()

    def run_lines(self, lines: list[str], wait_for: str = "ok", timeout_ms: int = 5000) -> str:
        inline = self._build_inline_command(lines, wait_for=wait_for, timeout_ms=timeout_ms)
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", inline],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "PowerShell GRBL command failed.")
        return result.stdout.strip()

    def status(self) -> GrblStatus:
        raw = self.run_lines(["?"], wait_for="<", timeout_ms=3000)
        match = STATUS_PATTERN.search(raw)
        if not match:
            raise RuntimeError(f"Could not parse GRBL status response: {raw}")
        return GrblStatus(
            state=match.group("state"),
            machine_x_mm=float(match.group("mx")),
            machine_y_mm=float(match.group("my")),
            machine_z_mm=float(match.group("mz")),
            work_x_mm=float(match.group("wx")),
            work_y_mm=float(match.group("wy")),
            work_z_mm=float(match.group("wz")),
            raw=raw,
        )

    def unlock(self) -> str:
        return self._run_script_line("$X", wait_for="ok", timeout_ms=4000)

    def set_work_origin(self) -> str:
        return self.run_lines(["G92 X0 Y0"], wait_for="ok", timeout_ms=4000)

    def jog_relative(self, dx_um: float, dy_um: float, feed_mm_min: float) -> str:
        dx_mm = dx_um / 1000.0
        dy_mm = dy_um / 1000.0
        gcode = f"G21 G91 G0 X{dx_mm:.4f} Y{dy_mm:.4f} F{feed_mm_min:.2f}"
        return self.run_lines([gcode], wait_for="ok", timeout_ms=6000)

    def set_max_rates(self, x_mm_min: float, y_mm_min: float) -> str:
        first = self._run_script_line(f"$110={x_mm_min:.3f}", wait_for="ok", timeout_ms=4000)
        second = self._run_script_line(f"$111={y_mm_min:.3f}", wait_for="ok", timeout_ms=4000)
        return "\n".join(part for part in (first, second) if part)

    def set_acceleration(self, x_mm_s2: float, y_mm_s2: float) -> str:
        first = self._run_script_line(f"$120={x_mm_s2:.3f}", wait_for="ok", timeout_ms=4000)
        second = self._run_script_line(f"$121={y_mm_s2:.3f}", wait_for="ok", timeout_ms=4000)
        return "\n".join(part for part in (first, second) if part)

    def feed_hold(self) -> str:
        return self.run_lines(["!"], wait_for="__NONE__", timeout_ms=1000)

    def resume(self) -> str:
        return self.run_lines(["~"], wait_for="__NONE__", timeout_ms=1000)

    def soft_reset(self) -> str:
        return self.run_lines(["__CTRL_X__"], wait_for="Grbl", timeout_ms=3000)

    def read_settings(self) -> dict[str, float]:
        raw = self._run_script_line("$$", wait_for="$132", timeout_ms=5000)
        settings: dict[str, float] = {}
        for match in SETTING_PATTERN.finditer(raw):
            code = match.group("code")
            value = match.group("value")
            if value is None:
                continue
            settings[code] = float(value)
        return settings
