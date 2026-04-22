# Bring-Up Checklist

## Hardware Bring-Up

1. Confirm which serial port is the GRBL controller.
2. Manually verify that `$X`, `?`, and a tiny `G0` move behave correctly before any scan automation.
3. Measure the real XY travel per commanded unit and confirm whether your GRBL coordinates already correspond to micrometers or need a conversion.
4. Pick one objective for the first automated pipeline and keep it fixed during early dataset collection.
5. Install `pyserial` before attempting live automated scans from Python, so the GRBL serial connection can stay open.

## Camera Bring-Up

1. Turn on the Canon camera and confirm a repeatable tethered capture path on Windows.
2. Replace `camera.capture_command` in [configs/lab.example.toml](../configs/lab.example.toml) with the real capture command.
3. Lock exposure, white balance, ISO, and illumination settings.
4. Save all raw images with stable filenames and timestamps.

## Optical Calibration

1. For graphene on 285 nm and hBN on 90 nm, collect 30 to 50 blank-substrate fields each.
2. Repeat blank-field capture at the start and end of at least three sessions.
3. Verify whether brightness drift is dominated by lamp intensity, white balance, or vignetting.
4. Build one flat-field file per objective and illumination setting.

## Scan Geometry

1. Measure the true field of view in micrometers for the chosen objective.
2. Update `scan.fov_width_um` and `scan.fov_height_um` accordingly.
3. Start with overlap near 10 to 15%.
4. Run `scan-plan` on a small region first and confirm tile spacing on the microscope.

## Dataset Bootstrapping

1. Run 10 small scans per workflow before attempting a full slide.
2. Review every surfaced candidate and label it `accept`, `reject`, or `ambiguous`.
3. Save a short note for hard negatives such as tape residue, dust, fringes, or focus failure.
4. Keep Raman or AFM confirmations for a smaller gold-standard subset.

## First Success Criteria

1. The system should not miss obviously usable flakes in a test region.
2. The false-positive rate should be low enough that a human can review a scan in minutes, not hours.
3. The same thresholds should work across multiple days without retuning.
4. The catalog should be rich enough to export a first supervised dataset.
