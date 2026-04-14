# CAD Starter Pack

This directory contains initial parametric `OpenSCAD` source for the Zeiss Axio retrofit.

Current parts:

- `focus_conical_clamp_pulley.scad`
- `x_stage_split_pulley.scad`
- `y_stage_split_pulley.scad`

## Why OpenSCAD

There is no CAD CLI installed in the current environment, but `OpenSCAD` is a practical text-native CAD format that can be:

- edited parametrically,
- rendered locally later,
- version-controlled cleanly,
- used as a bridge until a full microscope scan is available.

## How To Render Later

Once `OpenSCAD` is installed:

```bash
openscad -o focus_conical_clamp_pulley.stl focus_conical_clamp_pulley.scad
openscad -o x_stage_split_pulley.stl x_stage_split_pulley.scad
openscad -o y_stage_split_pulley.stl y_stage_split_pulley.scad
```

## Current Design Intent

- `focus`
  - conical two-piece clamp pulley for the left focus knob
  - sized from measured taper
  - clamp screw holes included as simple pass-through/capture geometry
- `X/Y`
  - split-clamp pulleys sized to fit over the knurled knobs
  - intended as calibration-friendly belt pulleys rather than running belts directly on the knob surface

## Still Needed From The 3D Scan

The scan should capture:

- exact clearances around the `X/Y` stage knobs
- exact clearances around the left focus knob
- nearby housing geometry for motor bracket attachment
- whether there are existing screw points usable for brackets
- belt routing clearance for vertical-loop `X/Y` belts
- motor placement envelope beside each knob

## Important Caveat

These are first-pass geometry placeholders, not production-ready parts yet. The main value is:

- locking down the coupling concept,
- giving you editable source,
- making the next CAD iteration faster once the microscope scan exists.
