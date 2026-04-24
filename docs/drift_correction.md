# Drift And Backlash Correction

## What The Current Mechanics Suggest

The belt slack looks more like backlash and direction-dependent hysteresis than steady monotonic drift.

That usually means:

- moves in the same direction are fairly repeatable
- reversals are worse
- a pure serpentine scan can accumulate row-to-row registration changes even if the stage does not truly drift away

## Immediate Software Mitigations

### 1. Prefer Same-Direction Final Approach

When possible, approach the final imaging coordinate from the same direction each time.

Two practical ways:

- use a flyback raster instead of a pure serpentine raster
- overshoot and settle back to the target by a calibrated backlash amount

### 2. Measure Backlash From Images

Use overlapping tiles or anchor revisits to estimate the actual residual shift.

The repo now includes:

```powershell
& 'C:\Users\xulab\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m flake_ml.cli estimate-shift `
  path\to\left_tile.jpg `
  path\to\right_tile.jpg `
  --axis x `
  --overlap-fraction 0.12
```

This measures the pixel shift inside the overlapping region and is a good first tool for quantifying backlash.

### 3. Periodic Anchor Re-Registration

For longer scans, revisit a known anchor location every few rows or every few millimeters.

If the anchor image shifts relative to the original anchor:

- update the stage-to-image coordinate model
- or at minimum flag that part of the scan for correction / reacquisition

## Fiducial Strategies That Do Not Pollute The Sample Area

Good options:

- a tiny scribed mark on a sacrificial wafer edge
- a permanent reference chip fixed to the sample holder outside the scan ROI
- a corner reference slide or etched marker mounted on the carrier

Avoid putting fiducials in the actual flake-search region.

## Recommended Progression

1. quantify X and Y backlash from overlap images
2. decide whether flyback or backlash-compensated serpentine is better
3. add anchor revisits every `5-10` rows for larger scans
4. only after that invest in more complex mosaic correction
