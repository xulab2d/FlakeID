# Camera Pathway

## What We Confirmed On This Workstation

From a direct probe on `2026-04-23`:

- the camera enumerates in Windows as `Canon EOS Rebel T6i`
- `EOS Utility 3` is installed locally at `C:\Program Files (x86)\Canon\EOS Utility\EU3\EOS Utility 3.exe`
- Canon `EDSDK.dll` is installed locally at `C:\Program Files (x86)\Canon\EOS Utility\EU3\EDSDK.dll`
- the local EDSDK version is `3.17.0.1`
- the local EOS Utility version is `3.18.5.13`
- the Windows WIA path only exposes `Synchronize`, not `Take Picture`

Bottom line:

- the long-term automation path should be Canon `EDSDK` over USB
- the near-term practical bridge is `EOS Utility` saving into a watched folder
- WIA is only a diagnostic/import fallback on this camera

## Recommended Capture Stack

### Stage A: Direct SDK Capture

Use the repo helper around Canon `EDSDK.dll`:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\canon_sdk_capture.ps1 -Probe
```

And for a real shutter test:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\canon_sdk_capture.ps1 `
  -Output outputs\camera_test.jpg
```

This helper:

- opens one Canon session directly through `EDSDK.dll`
- switches the save destination to the host PC
- triggers the shutter
- downloads the captured image to the requested path

Important:

- close `EOS Utility` and any live-view window before running it
- Canon camera sessions are exclusive, so the SDK helper cannot open the body while EOS Utility still owns it

### Stage B: Watched-Folder Fallback

If direct SDK capture is temporarily unavailable, FlakeID can still fall back to `EOS Utility` plus a watched hot folder at `photos/incoming`.

### Stage C: Optional Live-View Integration

After still-image capture is stable, add optional live-view support for:

- focus checks
- brightness checks
- anchor alignment checks before longer scans

Do not make live view a blocker for tile capture.

## Camera Settings To Lock

For early dataset collection, keep the camera configuration fixed within a workflow:

- manual exposure mode
- fixed shutter speed
- fixed ISO
- fixed white balance
- fixed image quality
- fixed picture style
- disable auto lighting optimizer
- disable highlight tone priority
- disable long-exposure noise reduction
- disable high-ISO noise reduction
- disable lens corrections or any other scene-dependent processing

If storage is acceptable, prefer `RAW+JPEG` on the camera while ingesting `JPEG` into the current pipeline. That preserves raw data for future color/thickness calibration without blocking the current software.

## Why Not WIA

Windows WIA is useful only as a sanity check here. On this T6i probe, WIA exposed only `Synchronize` and did not expose `Take Picture`, so it should not be treated as the automation path.

## Repo Commands

Probe the camera environment:

```powershell
& 'C:\Users\xulab\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m flake_ml.cli camera-probe
```

Create a new session scaffold:

```powershell
& 'C:\Users\xulab\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m flake_ml.cli init-session `
  --config configs/lab.example.toml `
  --output-root outputs/sessions `
  --sample-id graphene_trial_001 `
  --material graphene `
  --substrate graphene_285_wet `
  --objective 10x `
  --operator xulab
```
