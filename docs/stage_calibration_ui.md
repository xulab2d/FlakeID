# Stage Calibration UI

## Goal

Provide a safe manual-control window for boundary mapping and belt-friendly tuning before full scan automation.

## Launch

From the repo root:

```powershell
& 'C:\Users\xulab\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m flake_ml.cli stage-ui `
  --config configs/lab.example.toml
```

## What The UI Does

- reads live GRBL status
- jogs `X` and `Y` by a chosen step size
- lets you lower jog feed before testing
- reads and writes GRBL max-rate settings `$110/$111`
- reads and writes GRBL acceleration settings `$120/$121`
- lets you mark current position as safe min/max bounds
- saves those bounds and motion values back into the config file

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
6. Save bounds to config when finished.

## Notes

- Manual knob motion still does not update GRBL coordinates automatically.
- If you move the stage by hand, re-zero or re-establish your session coordinate reference before trusting the display.
- `Feed Hold`, `Resume`, and `Soft Reset` are exposed in the UI for bring-up convenience, but use them carefully.
- On this current GRBL/UNO path, writing controller settings works more reliably than reading them back. Treat the UI fields as the intended values and verify by actual stage behavior.
