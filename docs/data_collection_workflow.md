# Data Collection Workflow

## Goal

Collect microscope images in a way that is immediately usable for:

- candidate detection
- manual review
- later re-registration and drift correction
- later supervised training

## Session Layout

Use one session folder per scan day / sample batch.

The `init-session` command creates:

- `incoming`: raw files arriving from EOS Utility
- `tiles`: curated per-tile images used by the pipeline
- `blankfield`: blank substrate or no-sample images for flat-field correction
- `anchors`: reference images used for drift / backlash checks
- `labels`: exported annotations or review artifacts
- `logs`: acquisition logs and notes
- `qc`: quick overlays, diagnostics, and registration outputs

## Start-Of-Session Checklist

1. Run `camera-probe` once and confirm the expected camera is present.
2. Run `init-session` and note the session path.
3. In EOS Utility, point downloads to the session `incoming` directory.
4. Lock microscope lamp intensity and camera settings.
5. Confirm the current objective and record it in the session metadata.

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
