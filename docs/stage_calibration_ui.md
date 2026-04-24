# Stage Calibration UI

## Goal

Provide a safe manual-control window for:

- stage boundary mapping
- belt-friendly motion tuning
- scan ROI setup
- launching a raster capture run

## Launch

From the repo root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\launch_stage_ui.ps1 `
  -Config configs/lab.example.toml
```

## What The UI Does

- reads live GRBL status
- jogs `X` and `Y` by a chosen step size
- lets you lower jog feed before testing
- reads and writes GRBL max-rate settings `$110/$111`
- reads and writes GRBL acceleration settings `$120/$121`
- lets you mark current position as safe min/max bounds
- saves those bounds and motion values back into the config file
- lets you mark `left`, `right`, `top`, and `bottom` scan edges for the next scan ROI
- estimates raster size from FOV and overlap
- launches `run-scan` in a separate PowerShell window
- keeps scan photos organized under `photos/scans/...`

## Recommended Starting Values

If belts are skipping, start here:

- jog feed: `20 to 40 mm/min`
- x max rate: `40 to 80 mm/min`
- y max rate: `40 to 80 mm/min`
- x accel: `1 to 3 mm/s^2`
- y accel: `1 to 3 mm/s^2`

Then increase only after motion becomes repeatable.

## Safe Workflow

1. Open the UI.
2. Click `Refresh Status`.
3. Lower feed/rate/acceleration before any bigger move.
4. Use small jog steps first.
5. Mark safe min/max bounds only at backed-off safe locations, not at hard stops.
6. Mark the scan ROI edges for the flake region you want to raster.
7. Fill in sample metadata and click `Start Scan`.

## Notes

- Manual knob motion still does not update GRBL coordinates automatically.
- If you move the stage by hand, re-zero or re-establish your session coordinate reference before trusting the display.
- `Feed Hold`, `Resume`, and `Soft Reset` are exposed in the UI for bring-up convenience, but use them carefully.
- Jog motion is sent as feed-controlled `G1`, not `G0` rapids, so the jog-feed field should now have a real effect.
- On this current GRBL/UNO path, writing controller settings works more reliably than reading them back. Treat the UI fields as the intended values and verify by actual stage behavior.
- For the current default watched-folder camera flow, set EOS Utility once to save into `photos/incoming`. Each scan then copies images into its own per-scan folder automatically.
