from __future__ import annotations

from pathlib import Path
import json
import subprocess
from typing import Any


CANON_ROOT = Path(r"C:\Program Files (x86)\Canon")
EOS_UTILITY_EXE = CANON_ROOT / "EOS Utility" / "EU3" / "EOS Utility 3.exe"
EDSDK_DLL = CANON_ROOT / "EOS Utility" / "EU3" / "EDSDK.dll"


def _run_powershell_json(script: str) -> Any:
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "PowerShell probe failed.")
    text = result.stdout.strip()
    if not text:
        return None
    return json.loads(text)


def _windows_file_version(path: Path) -> str | None:
    if not path.exists():
        return None
    script = (
        f"(Get-Item '{str(path)}').VersionInfo | "
        "Select-Object -ExpandProperty FileVersion | ConvertTo-Json -Compress"
    )
    try:
        value = _run_powershell_json(script)
    except RuntimeError:
        return None
    if isinstance(value, str):
        return value
    return None


def probe_wia_devices() -> list[dict[str, Any]]:
    script = r"""
    $devices = @()
    try {
        $manager = New-Object -ComObject WIA.DeviceManager
        foreach ($info in $manager.DeviceInfos) {
            $name = $info.Properties['Name'].Value
            if ($name -notmatch 'Canon|EOS') {
                continue
            }
            $entry = [ordered]@{
                name = $name
                type = $info.Type
                device_id = $info.DeviceID
                commands = @()
                connect_error = $null
            }
            try {
                $device = $info.Connect()
                foreach ($command in $device.Commands) {
                    $entry.commands += [ordered]@{
                        name = $command.Name
                        command_id = $command.CommandID
                    }
                }
            }
            catch {
                $entry.connect_error = $_.Exception.Message
            }
            $devices += [pscustomobject]$entry
        }
    }
    catch {
        $devices = @([pscustomobject]@{
            name = $null
            type = $null
            device_id = $null
            commands = @()
            connect_error = $_.Exception.Message
        })
    }
    $devices | ConvertTo-Json -Depth 6 -Compress
    """
    payload = _run_powershell_json(script)
    if payload is None:
        return []
    if isinstance(payload, dict):
        return [payload]
    return list(payload)


def probe_camera_environment() -> dict[str, Any]:
    wia_devices = probe_wia_devices()
    eos_utility_present = EOS_UTILITY_EXE.exists()
    edsdk_present = EDSDK_DLL.exists()
    sdk_version = _windows_file_version(EDSDK_DLL)
    eos_utility_version = _windows_file_version(EOS_UTILITY_EXE)

    recommended_path = "unknown"
    notes: list[str] = []
    canon_connected = any(device.get("name") for device in wia_devices)
    wia_take_picture = any(
        any(command.get("name") == "Take Picture" for command in device.get("commands", []))
        for device in wia_devices
    )

    if canon_connected and edsdk_present:
        recommended_path = "canon_sdk"
        notes.append("Canon EOS body detected and EDSDK is installed locally.")
    elif eos_utility_present:
        recommended_path = "eos_utility_watch"
        notes.append("EOS Utility is installed; use it as a hot-folder bridge until SDK capture is wired.")
    elif canon_connected:
        recommended_path = "wia_transfer_only"
        notes.append("Camera is visible through WIA, but this path is usually limited to transfer/import.")

    if canon_connected and not wia_take_picture:
        notes.append("WIA does not expose a Take Picture command on this camera, so WIA is not the automation path.")

    return {
        "canon_root": str(CANON_ROOT),
        "eos_utility": {
            "present": eos_utility_present,
            "path": str(EOS_UTILITY_EXE),
            "version": eos_utility_version,
        },
        "edsdk": {
            "present": edsdk_present,
            "path": str(EDSDK_DLL),
            "version": sdk_version,
        },
        "wia_devices": wia_devices,
        "recommended_path": recommended_path,
        "notes": notes,
    }
