# Scanning Protocol v0.1

## Goal

Get a stable, labelable first dataset for flake discovery before motorized focus exists.

This protocol is deliberately conservative. It prioritizes repeatability over area throughput.

## Core Decision

For the first phase, use a **single fixed objective**, **single fixed illumination recipe**, and **small flat scan windows**.

My recommendation is:

- coarse automated discovery at `10x`
- optional manual revisit of good candidates at `20x` or higher
- no objective changes during a data-collection session

If your available objective set makes `10x` impractical, `20x` is the backup, but then the scan area per session should be smaller until XY and focus stability are proven.

## Why This Protocol First

- No motorized Z means focus variation is the main bottleneck.
- Changing objectives early multiplies calibration burden.
- Small, repeatable scans produce better training data than large inconsistent scans.
- Graphene on 285 nm oxide and hBN on 90 nm oxide both benefit from tightly controlled optical conditions.

## Recommended Bootstrap Protocol

### Session setup

1. Warm up the illumination source for a fixed amount of time.
2. Use one objective only for the full session.
3. Lock camera exposure, ISO, white balance, and file format.
4. Keep condenser/aperture settings unchanged for the whole session.
5. Record substrate, oxide thickness, sample prep, objective, and exposure in the session metadata.

### Before the first scan

1. Capture `20 to 30` blank-field images on clean bare substrate.
2. Capture `5` repeat blank fields after refocusing to estimate session variance.
3. Focus at the center of the intended ROI.
4. Check focus at the four corners of that ROI.

### ROI size

Until motorized focus exists, start with:

- `2 mm x 2 mm` automated scans at `10x`
- if the sample is very flat and all corners stay acceptably sharp, increase to `3 mm x 3 mm`
- avoid larger windows at first

At `20x`, start smaller:

- `1 mm x 1 mm` to `1.5 mm x 1.5 mm`

## Motion And Imaging Settings

### XY path

- serpentine raster
- overlap: `12%`
- stage settle time after each move: `250 to 400 ms`

### Focus strategy without motorized Z

- choose the focus plane that best preserves flake edges across the whole ROI, not just at the center
- if corners visibly drift out of focus, shrink the scan window rather than forcing a bigger scan
- keep the sample orientation fixed during a session

### Capture order

For each sample:

1. blank-field calibration
2. one or two small pilot scans
3. review pilot scan for overlap and focus consistency
4. only then run additional scans

## Substrate-Specific Notes

### Graphene on 285 nm wet Si/SiO2

- This should be the easiest of your two workflows to bootstrap.
- Favor getting high-quality negative space and contamination examples, not just obvious flakes.
- Early ranking can focus on mono/few-layer-like color deviations plus compact polygonal shapes.

### hBN on 90 nm dry Si/SiO2

- Keep illumination especially stable because thin hBN can be subtle.
- Collect more blank-field images per session than you think you need.
- Plan on more human review per square millimeter than graphene in the early phase.

## First Bench Test

### Test 1: communication only

- confirm GRBL responds on the expected COM port
- do not move the stage yet

### Test 2: tiny motion square

- move a very small square path near the current location
- confirm commanded direction signs match microscope motion
- confirm no cable snag or backlash surprise

Suggested first motion amplitudes:

- `50 um`
- then `100 um`
- then `250 um`

### Test 3: overlap validation

- capture a `3 x 3` tile grid
- verify neighboring tiles overlap by about the expected amount
- verify there is no obvious skipped or duplicated motion step

### Test 4: focus-window validation

- run a `2 mm x 2 mm` scan
- inspect center and corners for edge sharpness
- if corner sharpness fails, reduce the ROI size

## Dataset Collection Target

For each workflow:

- `10` pilot scans on different samples
- `3` sessions on different days
- `200 to 300` manually reviewed candidates

That is enough to start tuning thresholds and candidate ranking.

## Required Metadata Per Scan

- `sample_id`
- `material`
- `substrate`
- `oxide_thickness_nm`
- `objective`
- `exposure`
- `illumination recipe`
- `scan_width_mm`
- `scan_height_mm`
- `overlap_fraction`
- `operator`
- `date`

## Success Criteria

The protocol is good enough to scale when:

1. tile overlap is visually consistent across the full scan
2. focus is acceptable across the chosen ROI
3. optical appearance is stable enough that thresholds do not need retuning every scan
4. a reviewer can label surfaced candidates quickly without fighting obvious artifacts

