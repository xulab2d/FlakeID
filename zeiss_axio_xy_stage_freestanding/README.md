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

- `custom rigid clamp pulleys sized for a cut compliant liner` for the Zeiss Axio `X/Y` knobs
- `custom freestanding weighted motor pods` with adjustable motor height
- `donor STL references` for `NEMA17` motor mount and pulley/gear proportions

The pod concept is deliberately simple:

- a heavy printable base with ballast cavity
- a vertical tower made as `two slotted side rails` with a center access window
- an adjustable-height horizontal `NEMA17` motor plate
- motor shaft pointing upward
- small metal `GT2 20T` pulley fixed to the motor shaft
- horizontal `GT2` belt directly between the motor pulley and the knob pulley
- explicit cable notch and cable-tie slots for motor wiring

## Project Layout

- `exports/stl/`
  - printable STL files for the first-pass freestanding build
- `models/`
  - CadQuery model builders
- `scripts/export_models.py`
  - STL export script
- `sketches/`
  - concept drawing of the overall XY setup
- `references/donor_stl/`
  - upstream donor STL files gathered for comparison
- `MINIMAL_BUY_LIST.md`
  - minimal purchased-part list for the first `XY-only` build
- `arduino/`
  - quick bring-up sketch and notes for `Uno + CNC Shield V3`

Concept sketch:

- [xy_stage_setup_concept.svg](/Users/xulab/Desktop/Flake_Identification/flakefinder_lab/zeiss_axio_xy_stage_freestanding/sketches/xy_stage_setup_concept.svg)

## Printable Parts

Print:

- `1x` `axio_x_knob_pulley_left_half.stl`
- `1x` `axio_x_knob_pulley_right_half.stl`
- `1x` `axio_y_knob_pulley_left_half.stl`
- `1x` `axio_y_knob_pulley_right_half.stl`
- `2x` `xy_pod_body.stl`
- `2x` `xy_pod_ballast_lid.stl`
- `2x` `xy_pod_motor_plate_nema17.stl`

Optional preview/check parts:

- `x_drive_preview.stl`
- `y_drive_preview.stl`

Clamp strategy for the knob pulleys:

- rigid clamp shell in `PLA` or `PETG`
- cut strip liner material by hand and place it inside the bore
- shell bore sized for roughly `1 mm` liner thickness
- clamp preload compresses the liner against the knurled knob
- built-in bolt-head and hex-nut pockets for clamp preload

Pod adjustment / wiring strategy:

- the motor plate bolts to the tower through `two visible vertical slots`, one in each side rail
- you loosen the two tower bolts, slide the plate up or down, and retighten
- the large center cutout makes those slots and bolts easier to see and reach
- the motor plate has a cable slot near the motor center hole so the motor lead can exit cleanly
- the top of the tower has a cable notch
- both the tower and the motor flange have tie slots so the cable can be strain-relieved down the pod

## Hardware Assumptions

- `2x NEMA17` motors
- `2x GT2 20T metal pulleys`, `5 mm` bore
- `GT2 6 mm` closed-loop belts
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
- a cut compliant liner is meant to conform into the knurling
- the printed pulley is just the rigid clamp shell

This should be substantially more trustworthy than the earlier smooth-bore friction clamp.

Recommended liner material:

- best first choice: `1/32 in` or `1.0 mm` adhesive-backed `nitrile` or `polyurethane` rubber sheet
- acceptable fallback: thin adhesive-backed `neoprene`

What to avoid:

- very soft foam
- cork
- very slick silicone sheet
- anything thicker than about `1.5 mm` on the first pass

The goal is a thin, high-friction, slightly compliant layer, not a squishy cushion.

## Motor Wiring

Suggested routing:

1. mount the motor with the connector facing the open side of the plate
2. route the cable through the plate cable slot
3. bring the cable toward the tower notch
4. tie the cable to the flange/tower tie slots
5. run the cable downward along the back of the pod

That is the intended analog of the donor UC2 motor-mount style: keep cable exit clear of the belt path and give it a defined strain-relief path.

## Likely Next Refinements

- tune the knob pulley width and flange profile after a dry fit
- tune the pod height slots after testing actual belt plane
- decide whether direct two-pulley belt wrap is enough or whether an idler should be added
- widen or narrow the ballast cavity based on the weight you want to use
