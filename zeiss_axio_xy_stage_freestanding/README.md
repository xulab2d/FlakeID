# Zeiss Axio XY Stage Freestanding Retrofit

First-pass `XY-only` project for the `Zeiss Axio` manual microscope.

This version intentionally avoids motorized focus. It assumes:

- focus is set manually before scan start,
- the objective is not changed during a scan,
- the stage knobs are driven by `freestanding` motor pods sitting on the table,
- the motor pods do not attach to the microscope body.

## Measurements Used

Stage/knob heights above the table with the stage near its lowest position:

- `X knob bottom`: `85 mm`
- `Y knob bottom`: `109 mm`
- `stage bottom`: `180 mm`

Knob diameters already recorded:

- `X knob`: `27.8 mm`
- `Y knob`: `32.93 mm`

These are enough for a first-pass `XY-only` concept.

Approximate starting belt-plane targets for dry fitting:

- `X pod`: start around `95-100 mm` above the table
- `Y pod`: start around `120-126 mm` above the table

Those ranges are intentionally loose because the exact usable belt plane depends on the vertical thickness of the knob and where the clamp pulley rides best.

## Design Strategy

This project uses:

- `custom rigid-shell + compliant-liner clamp pulleys` for the Zeiss Axio `X/Y` knobs
- `custom freestanding weighted motor pods` with adjustable motor height
- `donor STL references` for `NEMA17` motor mount and pulley/gear proportions

The pod concept is deliberately simple:

- a heavy printable base with ballast cavity
- a vertical tower
- an adjustable-height horizontal `NEMA17` motor plate
- motor shaft pointing upward
- GT2 belt between the motor pulley and the knob pulley

## Project Layout

- `exports/stl/`
  - printable STL files for the first-pass freestanding build
- `models/`
  - CadQuery model builders
- `scripts/export_models.py`
  - STL export script
- `references/donor_stl/`
  - upstream donor STL files gathered for comparison

## Printable Parts

Print:

- `1x` `axio_x_knob_pulley_rigid_left_half.stl`
- `1x` `axio_x_knob_pulley_rigid_right_half.stl`
- `1x` `axio_x_knob_pulley_liner_left_half.stl` in `TPU`
- `1x` `axio_x_knob_pulley_liner_right_half.stl` in `TPU`
- `1x` `axio_y_knob_pulley_rigid_left_half.stl`
- `1x` `axio_y_knob_pulley_rigid_right_half.stl`
- `1x` `axio_y_knob_pulley_liner_left_half.stl` in `TPU`
- `1x` `axio_y_knob_pulley_liner_right_half.stl` in `TPU`
- `2x` `xy_pod_body.stl`
- `2x` `xy_pod_ballast_lid.stl`
- `2x` `xy_pod_motor_plate_nema17.stl`

Optional preview/check parts:

- `x_drive_preview.stl`
- `y_drive_preview.stl`

Clamp strategy for the knob pulleys:

- rigid outer shell in `PLA` or `PETG`
- separate inner liner halves in `TPU`
- liner bore intentionally undersized relative to the knob
- shell bore sized to compress the liner against the knurled knob
- built-in bolt-head and hex-nut pockets for clamp preload

## Hardware Assumptions

- `2x NEMA17` motors
- `2x GT2 20T metal pulleys`, `5 mm` bore
- `GT2 6 mm` belt
- `M3` screws for motor mounting
- `3x M3 socket-head screws + 3x M3 hex nuts` for each knob pulley
- `M5` or `M6` bolts/washers/nuts for plate-to-tower mounting
- dense ballast for each pod base
  - steel blocks
  - steel washers
  - lead shot in a bag
  - similar compact mass

## Current Uncertainties

This first pass intentionally leaves adjustment margin because these details are still not pinned down:

- exact knob vertical thickness / preferred belt plane on each knob
- exact lateral offset from knob center to a comfortable motor-pod position
- how much belt wrap is needed before slip appears

That is why the pod uses:

- an adjustable motor plate height
- freestanding placement instead of microscope-side attachment

## Pulley Notes

These pulleys are intentionally more aggressive than the first pass:

- clamp preload comes from `3` through-bolts
- the compliant liner is meant to conform into the knurling
- the liner can be printed in `TPU 95A` or used as a template for cut sheet rubber

This should be substantially more trustworthy than the earlier smooth-bore friction clamp.

## Likely Next Refinements

- tune the knob pulley width and flange profile after a dry fit
- tune the pod height slots after testing actual belt plane
- decide whether a simple direct belt is enough or whether an idler should be added
- widen or narrow the ballast cavity based on the weight you want to use
