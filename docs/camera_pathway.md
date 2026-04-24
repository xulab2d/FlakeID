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

### Stage A: Immediate Bring-Up

Use `EOS Utility` as the capture engine and let FlakeID watch the download folder.

Why:

- Canon already supports the camera on this machine
- it avoids brittle reverse engineering on day one
- it lets you start collecting blank fields, anchors, and pilot tiles immediately

Recommended flow:

1. In EOS Utility, open remote shooting.
2. Set the save destination once to `photos/incoming`.
3. Disable any linked auto-open behavior you do not want during scanning.
4. Keep FlakeID responsible for copying images into per-scan folders, renaming, cataloging, and later analysis.

### Stage B: Robust Automation

Build a small long-lived Canon SDK helper around the installed `EDSDK.dll`.

That helper should do only a few things:

- open one camera session and keep it open
- trigger a capture
- save the downloaded image to a requested path
- report camera identity and errors cleanly

That is the cleanest end state for this Windows workstation because Canon's own SDK is already present and the camera is known to be supported.

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
