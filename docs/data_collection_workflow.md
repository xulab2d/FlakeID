# Data Collection Workflow

## Goal

Collect microscope images in a way that is immediately usable for:

- candidate detection
- manual review
- later re-registration and drift correction
- later supervised training

## Scan Folder Layout

Each automated raster now creates its own folder inside `photos/scans`.

A typical scan folder contains:

- `tiles`: curated per-tile images used by the pipeline
- `blankfield`: blank substrate or no-sample images for flat-field correction
- `anchors`: reference images used for drift / backlash checks
- `labels`: exported annotations or review artifacts
- `logs`: acquisition logs and notes
- `qc`: scan plan, summaries, and registration diagnostics
- `scan_catalog.db`: SQLite catalog for the scan

The fixed EOS Utility hot folder should be:

- `photos/incoming`

This avoids changing the EOS Utility save destination for every scan. FlakeID watches that one folder and copies each new image into the active scan folder automatically.

## Start-Of-Scan Checklist

1. Run `camera-probe` once and confirm the expected camera is present.
2. In EOS Utility, point downloads to `photos/incoming`.
3. Lock microscope lamp intensity and camera settings.
4. Confirm the current objective and sample metadata in the scan UI.
5. Mark the scan ROI edges, then start with a small pilot raster before larger runs.

## Capture Order

### 1. Blank Fields

Collect `20-30` blank-field images at the beginning of the session.

Use:

- same objective
- same lamp setting
- same camera settings
- representative substrate region with no obvious flakes

Repeat another `10-20` blank fields at the end of the session if the session is long.

### 2. Anchor Images

Before the first scan, capture anchor images from one or more fixed reference locations.

Good anchor targets:

- a scribed edge mark on the wafer perimeter
- a fixed reference chip mounted at the holder edge
- a stable dust/scratch cluster near a non-critical corner if nothing better exists

Capture anchors:

- before the scan
- every few rows or every few millimeters during longer scans
- after the scan

### 3. Pilot Tiles

Collect a small pilot area first:

- `3 x 3` or `5 x 5` tiles
- same overlap you plan to use for production
- verify focus, brightness, and overlap consistency

### 4. Production Tiles

Once the pilot looks stable, acquire the larger raster.

## If Capture Triggering Is Still Manual

If `camera.capture_command` is blank and the driver is `watched_folder`, the scan waits at each tile until a new image appears in `photos/incoming`.

That is still useful for:

- early camera bring-up
- testing raster geometry
- small human-supervised pilot scans

Once a direct trigger command or Canon SDK helper is added, the same scan folders and UI workflow continue to work.

## Labeling Priorities

Start with the highest-value labels first:

1. tile-level `usable / not usable`
2. candidate-level `flake / not flake`
3. material label `graphene / hBN / other`
4. quality label `interesting / ignore / revisit`

Thickness labels can come later, after the acquisition pipeline is stable.

## File Naming Guidance

Each tile filename should eventually encode:

- session id
- tile row / column
- stage coordinates
- timestamp
- material / substrate context if needed

This keeps later registration, relabeling, and model training much easier.
